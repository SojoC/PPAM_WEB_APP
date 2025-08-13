import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os

class WhatsAppServicio:
    """
    Servicio de WhatsApp final y robusto, con métricas detalladas y
    optimizado para funcionar en un entorno de servidor como Render.
    """
    def __init__(self, perfil_dir="playwright_whatsapp_profile"):
        self.perfil_dir = os.path.abspath(perfil_dir)
        self.contexto = None
        self.pagina = None
        self.playwright = None

    async def _inicializar_playwright(self):
        if self.contexto and not self.contexto.is_closed():
            print("METRICA: Reutilizando sesión de Playwright existente.")
            return True
        
        print("METRICA: Inicializando Playwright en modo Headless para Render...")
        try:
            self.playwright = await async_playwright().start()
            self.contexto = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.perfil_dir,
                headless=True,  # MODO SIN PANTALLA PARA RENDER
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            self.pagina = self.contexto.pages[0] if self.contexto.pages else await self.contexto.new_page()
            print("METRICA: Navegador iniciado en segundo plano.")
            return True
        except Exception as e:
            print(f"METRICA DE ERROR CRÍTICO al inicializar Playwright: {e}")
            return False

    async def conectar_whatsapp(self):
        if not await self._inicializar_playwright():
            return {"status": "error", "mensaje": "No se pudo iniciar el navegador."}
            
        print("METRICA: Abriendo WhatsApp Web...")
        await self.pagina.goto("https://web.whatsapp.com", timeout=120000)

        selector_qr = "div[data-testid='qrcode']"
        selector_lista_chats = "div[data-testid='chat-list']"
        
        try:
            print("METRICA: Esperando por QR o Lista de Chats...")
            await self.pagina.wait_for_selector(f"{selector_qr}, {selector_lista_chats}", state='attached', timeout=90000)
            
            if await self.pagina.locator(selector_qr).is_visible(timeout=5000):
                print("METRICA: Se necesita escanear QR.")
                qr_base64 = await self.pagina.locator(selector_qr).screenshot(type="png", base64=True)
                return {"status": "necesita_qr", "qr_code": f"data:image/png;base64,{qr_base64}"}
            
            print("METRICA: Sesión de WhatsApp ya iniciada.")
            return {"status": "logueado"}
        except TimeoutError:
            return {"status": "error", "mensaje": "Timeout al cargar WhatsApp."}

    async def esta_logueado(self):
        if not self.pagina or self.pagina.is_closed(): return False
        print("METRICA: Verificando si la sesión está activa...")
        try:
            await self.pagina.wait_for_selector("div[data-testid='chat-list']", state='visible', timeout=5000)
            print("METRICA: Sesión activa confirmada.")
            return True
        except TimeoutError:
            print("METRICA: Sesión no activa.")
            return False

    async def enviar_mensaje(self, telefono, mensaje):
        print(f"\n--- INICIO DE SECUENCIA DE ENVÍO a {telefono} ---")
        if not await self.esta_logueado():
            print("METRICA DE ERROR: Intento de envío sin sesión activa.")
            return False
        try:
            numero = ''.join(filter(str.isdigit, telefono))
            print(f"METRICA: Navegando al chat de {numero}...")
            await self.pagina.goto(f"https://web.whatsapp.com/send?phone={numero}")
            
            caja_mensaje_selector = "div[data-testid='conversation-compose-box-input']"
            print("METRICA: Esperando a que la caja de texto aparezca...")
            caja_mensaje = self.pagina.locator(caja_mensaje_selector)
            await caja_mensaje.wait_for(state="visible", timeout=30000)
            
            print("METRICA: Escribiendo y enviando mensaje...")
            await caja_mensaje.fill(mensaje)
            await caja_mensaje.press("Enter")
            await self.pagina.wait_for_timeout(3000)
            print(f"--- SECUENCIA DE ENVÍO A {telefono} COMPLETADA ---")
            return True
        except Exception as e:
            print(f"METRICA DE ERROR al enviar mensaje a {telefono}: {e}")
            return False