import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os

class WhatsAppServicio:
    def __init__(self, perfil_dir="playwright_whatsapp_profile"):
        self.perfil_dir = os.path.abspath(perfil_dir)
        self.contexto = None
        self.pagina = None
        self.playwright = None
        print("✅ Servicio de WhatsApp (Playwright) listo.")

    async def _inicializar_playwright(self):
        if self.contexto and not self.contexto.is_closed():
            print("👍 Reutilizando sesión de Playwright existente.")
            return True
        
        print("🚀 Inicializando Playwright y Chrome...")
        try:
            self.playwright = await async_playwright().start()
            self.contexto = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.perfil_dir,
                headless=True,  # CAMBIO: Render solo soporta headless
                args=["--no-sandbox", "--disable-setuid-sandbox"]
            )
            self.pagina = self.contexto.pages[0] if self.contexto.pages else await self.contexto.new_page()
            print("✅ Navegador iniciado.")
            return True
        except Exception as e:
            print(f"❌ Error CRÍTICO al inicializar Playwright: {e}")
            return False

    async def conectar_whatsapp(self):
        if not await self._inicializar_playwright():
            return {"status": "error", "mensaje": "No se pudo iniciar el navegador."}
            
        print("🌐 Abriendo WhatsApp Web y verificando sesión...")
        await self.pagina.goto("https://web.whatsapp.com", timeout=120000)

        selector_lista_chats = "div[data-testid='chat-list']"
        try:
            await self.pagina.wait_for_selector(selector_lista_chats, state='visible', timeout=30000)
            print("✅ Sesión de WhatsApp ya iniciada.")
            return {"status": "logueado"}
        except TimeoutError:
            print("❌ No se detectó sesión activa.")
            return {"status": "error", "mensaje": "No hay sesión activa. Autentica localmente y sube el perfil."}

    async def esta_logueado(self):
        if not self.pagina or self.pagina.is_closed(): return False
        try:
            await self.pagina.wait_for_selector("div[data-testid='chat-list']", state='visible', timeout=5000)
            return True
        except TimeoutError:
            return False

    async def enviar_mensaje(self, telefono, mensaje):
        if not await self.esta_logueado():
            print("❌ No hay sesión activa en WhatsApp Web.")
            return False
        try:
            numero = ''.join(filter(str.isdigit, telefono))
            print(f"➡️  Preparando envío a {numero}...")
            await self.pagina.goto(f"https://web.whatsapp.com/send?phone={numero}")
            caja_mensaje_selector = "div[data-testid='conversation-compose-box-input']"
            caja_mensaje = self.pagina.locator(caja_mensaje_selector)
            await caja_mensaje.wait_for(state="visible", timeout=30000)
            await caja_mensaje.fill(mensaje)
            await caja_mensaje.press("Enter")
            await self.pagina.wait_for_timeout(3000)
            print(f"✅ Mensaje enviado a {telefono}")
            return True
        except Exception as e:
            print(f"❌ Error al enviar mensaje a {telefono}: {e}")
            return False

    async def cerrar(self):
        if self.contexto:
            await self.contexto.close()
        if self.playwright:
            await self.playwright.stop()