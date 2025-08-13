import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os
import threading

class WhatsAppServicio:
    """
    Servicio de WhatsApp final, con un reactor asyncio dedicado para máxima
    estabilidad en producción (Render).
    """
    def __init__(self, perfil_dir="playwright_whatsapp_profile"):
        self.perfil_dir = os.path.abspath(perfil_dir)
        self.contexto = None
        self.pagina = None
        self.playwright = None
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.thread.start()
        print("✅ Reactor de Misión (WhatsApp/Playwright) iniciado.")

    def _submit_coroutine(self, coro):
        """Envía una tarea a nuestro reactor y espera el resultado."""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result()

    async def _internal_inicializar(self):
        if self.contexto and not self.contexto.is_closed():
            return True
        print("🚀 Inicializando Playwright en modo Headless...")
        try:
            self.playwright = await async_playwright().start()
            self.contexto = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.perfil_dir,
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            self.pagina = self.contexto.pages[0] if self.contexto.pages else await self.contexto.new_page()
            print("✅ Navegador iniciado en segundo plano.")
            return True
        except Exception as e:
            print(f"❌ Error CRÍTICO al inicializar Playwright: {e}")
            return False

    async def _internal_conectar(self):
        if not await self._internal_inicializar():
            return {"status": "error", "mensaje": "No se pudo iniciar el navegador."}
        
        await self.pagina.goto("https://web.whatsapp.com", timeout=120000)
        selector_qr = "div[data-testid='qrcode']"
        try:
            await self.pagina.wait_for_selector(selector_qr, state='visible', timeout=30000)
            qr_base64 = await self.pagina.locator(selector_qr).screenshot(type="png", base64=True)
            return {"status": "necesita_qr", "qr_code": f"data:image/png;base64,{qr_base64}"}
        except TimeoutError:
            return {"status": "logueado"}

    async def _internal_esta_logueado(self):
        if not self.pagina or self.pagina.is_closed(): return False
        try:
            await self.pagina.wait_for_selector("div[data-testid='chat-list']", state='visible', timeout=5000)
            return True
        except TimeoutError:
            return False

    async def _internal_enviar_mensaje(self, telefono, mensaje):
        if not await self._internal_esta_logueado(): return False
        try:
            numero = ''.join(filter(str.isdigit, telefono))
            await self.pagina.goto(f"https://web.whatsapp.com/send?phone={numero}")
            caja_mensaje = self.pagina.locator("div[data-testid='conversation-compose-box-input']")
            await caja_mensaje.wait_for(state="visible", timeout=30000)
            await caja_mensaje.fill(mensaje)
            await caja_mensaje.press("Enter")
            return True
        except Exception as e:
            print(f"❌ Error al enviar a {telefono}: {e}")
            return False

    # --- Métodos públicos que la API llamará ---
    def conectar_whatsapp(self):
        return self._submit_coroutine(self._internal_conectar())

    def esta_logueado(self):
        return self._submit_coroutine(self._internal_esta_logueado())

    def enviar_mensaje(self, telefono, mensaje):
        return self._submit_coroutine(self._internal_enviar_mensaje(telefono, mensaje))