import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os
import re
import base64
from contextlib import suppress
from typing import List, Optional

# Selectores robustos basados en tu archivo
SEL_QR = ["div[data-testid='qrcode'] canvas"]
SEL_LOGGED = ["div[data-testid='chat-list']"]
SEL_MSGBOX = ["div[data-testid='conversation-compose-box-input']", "div[contenteditable='true'][data-tab='10']"]

def _to_dataurl(png: bytes) -> str:
    return "data:image/png;base64," + base64.b64encode(png).decode("utf-8")

class WhatsAppServicio:
    def __init__(self, perfil_dir="playwright_whatsapp_profile"):
        self.perfil_dir = os.path.abspath(perfil_dir)
        self._pw = None
        self._ctx = None
        self._page = None
        self._lock = asyncio.Semaphore(1)
        print("✅ Servicio de WhatsApp (Playwright) listo.")

    async def _ensure_context(self):
        if self._ctx and not self._ctx.is_closed():
            if not self._page or self._page.is_closed():
                self._page = await self._ctx.new_page()
            return
        os.makedirs(self.perfil_dir, exist_ok=True)
        self._pw = await async_playwright().start()
        # Headless se activa si la variable de entorno RENDER está presente
        headless_mode = os.environ.get('RENDER', False)
        self._ctx = await self._pw.chromium.launch_persistent_context(
            user_data_dir=self.perfil_dir,
            headless=bool(headless_mode),
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        self._page = self._ctx.pages[0] if self._ctx.pages else await self._ctx.new_page()

    async def _wait_any(self, selectors: List[str], state="visible", timeout=15000):
        for sel in selectors:
            with suppress(TimeoutError):
                el = await self._page.wait_for_selector(sel, state=state, timeout=timeout)
                if el: return el, sel
        return None, None

    async def conectar_whatsapp(self) -> dict:
        async with self._lock:
            await self._ensure_context()
            await self._page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=90000)
            
            el, sel = await self._wait_any(SEL_QR + SEL_LOGGED, state="visible", timeout=90000)
            
            if el and sel in SEL_QR:
                print("-> Se necesita escanear QR.")
                qr_el, _ = await self._wait_any(SEL_QR, timeout=5000)
                if qr_el:
                    return {"status": "necesita_qr", "qr_code": _to_dataurl(await qr_el.screenshot())}
            
            if el and sel in SEL_LOGGED:
                print("-> Sesión ya iniciada.")
                return {"status": "logueado"}

            return {"status": "error", "mensaje": "No se pudo determinar el estado de la sesión."}

    async def esta_logueado(self) -> bool:
        if not self._page or self._page.is_closed(): return False
        el, _ = await self._wait_any(SEL_LOGGED, timeout=3000)
        return el is not None

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        async with self._lock:
            try:
                await self._ensure_context()
                if not await self.esta_logueado():
                    print("-> Sesión no activa. Abortando envío.")
                    return False

                phone = re.sub(r"\D", "", telefono or "")
                await self._page.goto(f"https://web.whatsapp.com/send?phone={phone}", timeout=60000)
                
                box_el, _ = await self._wait_any(SEL_MSGBOX, state="visible", timeout=30000)
                if not box_el:
                    raise RuntimeError("No se encontró la caja de texto del chat.")
                
                await box_el.click()
                await box_el.fill(mensaje)
                await box_el.press("Enter")
                await self._page.wait_for_timeout(2000)
                
                print(f"✅ Mensaje enviado a {telefono}")
                return True
            except Exception as e:
                print(f"❌ Error al enviar mensaje a {telefono}: {e}")
                return False

    async def cerrar(self):
        async with self._lock:
            if self._ctx: await self._ctx.close()
            if self._pw: await self._pw.stop()