import os
from playwright.async_api import async_playwright, TimeoutError
from contextlib import suppress
import asyncio

SEL_QR = ["div[data-testid='qrcode'] canvas"]
SEL_LOGGED = ["div[data-testid='chat-list']"]
SEL_MSGBOX = [
    "div[data-testid='conversation-compose-box-input']",
    "div[contenteditable='true'][data-tab='10']"
]

class WhatsAppServicio:
    def __init__(self, perfil_dir="playwright_whatsapp_profile"):
        self.perfil_dir = os.path.abspath(perfil_dir)
        self._pw = None
        self._ctx = None
        self._page = None
        self._lock = asyncio.Lock()
        print("✅ Servicio de WhatsApp (Playwright) listo.")

    async def _ensure_context(self):
        if self._ctx and not self._ctx.is_closed():
            if not self._page or self._page.is_closed():
                self._page = await self._ctx.new_page()
            return
        os.makedirs(self.perfil_dir, exist_ok=True)
        self._pw = await async_playwright().start()
        # Headless si está en Render
        headless_mode = os.environ.get('RENDER', '').lower() in ('1', 'true', 'yes')
        self._ctx = await self._pw.chromium.launch_persistent_context(
            user_data_dir=self.perfil_dir,
            headless=headless_mode,
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        self._page = self._ctx.pages[0] if self._ctx.pages else await self._ctx.new_page()

    async def _wait_any(self, selectors, state="visible", timeout=30000):
        for sel in selectors:
            try:
                el = await self._page.wait_for_selector(sel, state=state, timeout=timeout)
                return el, sel
            except Exception:
                continue
        return None, None

    async def conectar_whatsapp(self) -> dict:
        async with self._lock:
            await self._ensure_context()
            await self._page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=90000)
            el, sel = await self._wait_any(SEL_QR + SEL_LOGGED, state="visible", timeout=90000)
            headless_mode = os.environ.get('RENDER', '').lower() in ('1', 'true', 'yes')
            if headless_mode and el and sel in SEL_QR:
                print("❌ No se puede escanear QR en Render. Sube el perfil autenticado.")
                return {"status": "error", "mensaje": "No se puede escanear QR en Render. Sube el perfil autenticado."}
            if el and sel in SEL_QR:
                print("-> Se necesita escanear QR.")
                return {"status": "necesita_qr"}
            if el and sel in SEL_LOGGED:
                print("-> Sesión ya iniciada.")
                return {"status": "logueado"}
            return {"status": "error", "mensaje": "No se pudo determinar el estado de la sesión."}

    async def esta_logueado(self) -> bool:
        await self._ensure_context()
        try:
            await self._page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)
            el, sel = await self._wait_any(SEL_LOGGED, state="visible", timeout=15000)
            return bool(el)
        except Exception:
            return False

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        async with self._lock:
            await self._ensure_context()
            # Verifica sesión activa
            el, sel = await self._wait_any(SEL_LOGGED, state="visible", timeout=15000)
            if not el:
                print("❌ No hay sesión activa en WhatsApp Web.")
                return False
            numero = ''.join(filter(str.isdigit, telefono))
            if not numero.startswith('58'):
                numero = '58' + numero[-10:]  # Ajusta según país
            numero = f'+{numero}'
            print(f"➡️  Preparando envío a {numero}...")
            try:
                await self._page.goto(f"https://web.whatsapp.com/send?phone={numero}", timeout=60000)
                input_box, _ = await self._wait_any(SEL_MSGBOX, state="visible", timeout=20000)
                if not input_box:
                    print("❌ No se encontró la caja de texto para el mensaje.")
                    return False
                await input_box.click()
                await asyncio.sleep(0.5)
                await input_box.fill("")  # Limpia el campo
                await asyncio.sleep(0.5)
                await input_box.type(mensaje, delay=30)
                await asyncio.sleep(1)
                await input_box.press("Enter")
                await asyncio.sleep(2)
                print(f"✅ Mensaje enviado a {telefono}")
                return True
            except Exception as e:
                print(f"❌ Error al enviar mensaje a {telefono}: {e}")
                return False

    async def cerrar(self):
        if self._ctx:
            await self._ctx.close()
        if self._pw:
            await self._pw.stop()