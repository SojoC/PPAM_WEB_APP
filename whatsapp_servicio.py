import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os

class WhatsAppServicio:
    """
    Servicio de WhatsApp final y robusto, basado en Playwright,
    optimizado para funcionar en un entorno de servidor como Render.
    """
    def __init__(self, perfil_dir="playwright_whatsapp_profile"):
        self.perfil_dir = os.path.abspath(perfil_dir)
        self.contexto = None
        self.pagina = None
        self.playwright = None
        print("✅ Servicio de WhatsApp (Playwright) listo para producción.")

    async def _inicializar_playwright(self):
        """
        Inicializa el navegador. Reutiliza la sesión si ya existe.
        En un entorno de servidor, siempre se ejecutará en modo headless.
        """
        if self.contexto and not self.contexto.is_closed():
            print("👍 Reutilizando sesión de navegador Playwright existente.")
            # Asegurarse de que tenemos una página activa
            if not self.pagina or self.pagina.is_closed():
                self.pagina = await self.contexto.new_page()
            return True
        
        print("🚀 Inicializando Playwright en modo Headless para el servidor...")
        try:
            self.playwright = await async_playwright().start()
            self.contexto = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.perfil_dir,
                headless=True,  # <-- CAMBIO CLAVE: ACTIVADO PARA RENDER
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--single-process"
                ]
            )
            self.pagina = self.contexto.pages[0] if self.contexto.pages else await self.contexto.new_page()
            print("✅ Navegador iniciado correctamente en segundo plano.")
            return True
        except Exception as e:
            print(f"❌ Error CRÍTICO al inicializar Playwright: {e}")
            return False

    async def conectar_whatsapp(self):
        """
        Abre WhatsApp Web y devuelve el estado o el código QR.
        """
        if not await self._inicializar_playwright():
            return {"status": "error", "mensaje": "No se pudo iniciar el navegador."}
            
        print("🌐 Abriendo WhatsApp Web y verificando sesión...")
        await self.pagina.goto("https://web.whatsapp.com", timeout=120000)

        selector_qr = "div[data-testid='qrcode']"
        selector_lista_chats = "div[data-testid='chat-list']"
        
        try:
            # Espera a que CUALQUIERA de los dos selectores aparezca
            await self.pagina.wait_for_selector(f"{selector_qr}, {selector_lista_chats}", state='attached', timeout=90000)
            
            # Si el código QR es visible, se necesita iniciar sesión
            if await self.pagina.locator(selector_qr).is_visible(timeout=5000):
                print("  -> Se detectó Código QR. Se necesita escanear.")
                qr_base64 = await self.pagina.locator(selector_qr).screenshot(type="png", base64=True)
                return {"status": "necesita_qr", "qr_code": f"data:image/png;base64,{qr_base64}"}
            
            print("✅ Sesión de WhatsApp ya iniciada.")
            return {"status": "logueado"}
        except TimeoutError:
            return {"status": "error", "mensaje": "Timeout al cargar la página de WhatsApp."}

    async def esta_logueado(self):
        """Verifica si la sesión de WhatsApp ya está iniciada."""
        if not self.pagina or self.pagina.is_closed(): return False
        try:
            await self.pagina.wait_for_selector("div[data-testid='chat-list']", state='visible', timeout=5000)
            return True
        except TimeoutError:
            return False

    async def enviar_mensaje(self, telefono, mensaje):
        """Envía un mensaje a un número de teléfono específico."""
        if not await self.esta_logueado():
            # Si no está logueado, intenta inicializar y verificar de nuevo.
            print("⚠️ Sesión no activa. Intentando reconectar...")
            await self.conectar_whatsapp()
            if not await self.esta_logueado():
                print("❌ Error: No se pudo establecer una sesión de WhatsApp.")
                return False

        try:
            numero = ''.join(filter(str.isdigit, telefono))
            print(f"➡️  Preparando envío a {numero} en Render...")
            
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
        """Cierra el navegador y detiene Playwright."""
        if self.contexto:
            await self.contexto.close()
            self.contexto = None
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        print("🛑 Sesión de Playwright cerrada.")