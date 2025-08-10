import asyncio
from playwright.async_api import async_playwright, TimeoutError
import os

class WhatsAppServicio:
    def __init__(self, perfil_dir="playwright_whatsapp_profile"):
        self.perfil_dir = os.path.abspath(perfil_dir)
        print("✅ Servicio de WhatsApp (Playwright) listo.")

    async def enviar_mensaje(self, telefono: str, mensaje: str) -> bool:
        try:
            async with async_playwright() as p:
                navegador = await p.chromium.launch_persistent_context(
                    user_data_dir=self.perfil_dir,
                    headless=False,
                    args=["--start-maximized"]
                )
                pagina = await navegador.new_page()
                print("🌐 Abriendo WhatsApp Web...")
                await pagina.goto("https://web.whatsapp.com")
                # Esperar inicio de sesión
                print("🕒 Verificando sesión...")
                try:
                    await pagina.wait_for_selector("canvas[aria-label='Código QR']", timeout=15000)
                    print("🛑 Escanea el código QR para iniciar sesión.")
                    await pagina.wait_for_selector("canvas[aria-label='Código QR']", state="detached", timeout=120000)
                    print("✅ Sesión iniciada correctamente.")
                except:
                    print("✅ Sesión ya activa o verificando...")
                    await pagina.wait_for_timeout(5000)
                # Cerrar popups
                print("🔍 Verificando ventanas emergentes...")
                await pagina.wait_for_timeout(3000)
                try:
                    continuar_button = await pagina.query_selector('button:has-text("Continuar")')
                    if continuar_button:
                        await continuar_button.click()
                        print("✅ Ventana emergente 'Continuar' cerrada.")
                        await pagina.wait_for_timeout(2000)
                    close_buttons = await pagina.query_selector_all('button:has-text("OK"), button:has-text("Entendido"), button:has-text("Cerrar"), button[aria-label="Cerrar"], button[aria-label="Close"]')
                    for button in close_buttons:
                        try:
                            await button.click(timeout=2000)
                            print("✅ Ventana emergente adicional cerrada.")
                            await pagina.wait_for_timeout(1000)
                        except:
                            pass
                    await pagina.keyboard.press('Escape')
                    await pagina.wait_for_timeout(1000)
                except Exception as e:
                    print(f"⚠️ Error cerrando ventanas emergentes: {e}")
                print("✅ Ventanas emergentes procesadas.")
                # Verificar que estamos en WhatsApp Web
                try:
                    await pagina.wait_for_selector("[data-testid='chat-list']", timeout=30000)
                    print("📱 WhatsApp Web cargado correctamente.")
                except:
                    print("⚠️ Esperando que WhatsApp Web termine de cargar...")
                    await pagina.wait_for_timeout(10000)
                # Buscar el número en el buscador
                numero = ''.join(filter(str.isdigit, telefono))
                if not numero.startswith('58'):
                    numero = '58' + numero[-10:]  # Venezuela, ajusta según país
                numero = f'+{numero}'
                print(f"  Buscando número: {numero}")
                try:
                    search_input = await pagina.wait_for_selector('[data-testid="chat-list-search"]', timeout=10000)
                    await search_input.click()
                    print("✅ Buscador de chats encontrado.")
                    await search_input.type(numero, delay=100)
                    await pagina.wait_for_timeout(3000)
                    print(f"📝 Número {numero} escrito en el buscador.")
                    try:
                        first_result = await pagina.wait_for_selector('[data-testid="cell-frame-container"]', timeout=5000)
                        await first_result.click()
                        print("✅ Chat encontrado y abierto desde búsqueda.")
                    except:
                        print("⚠️ No se encontró en búsqueda, probando crear nuevo chat...")
                        await pagina.goto(f"https://web.whatsapp.com/send?phone={numero}")
                        await pagina.wait_for_timeout(5000)
                except Exception as e:
                    print(f"❌ Error en búsqueda: {e}")
                    print("🔄 Usando método de URL directa...")
                    await pagina.goto(f"https://web.whatsapp.com/send?phone={numero}")
                    await pagina.wait_for_timeout(5000)
                # Buscar caja de texto de mensaje (varias opciones)
                print("🔍 Buscando caja de texto para escribir mensaje...")
                input_box = None
                selectors = [
                    'div[contenteditable="true"][data-testid="conversation-compose-box-input"]',
                    'div[contenteditable="true"][data-tab="10"]',
                    'div[contenteditable="true"][data-tab][role="textbox"]',
                    'footer div[contenteditable="true"]'
                ]
                for selector in selectors:
                    try:
                        await pagina.wait_for_selector(selector, timeout=7000)
                        input_box = await pagina.query_selector(selector)
                        if input_box:
                            print(f"✅ Caja de texto encontrada con selector: {selector}")
                            break
                    except Exception as e:
                        print(f"⚠️ No se encontró caja con selector: {selector}")
                if not input_box:
                    print("❌ No se pudo obtener la caja de texto del mensaje")
                    await navegador.close()
                    return False
                # Escribir y enviar el mensaje
                print("✍️ Escribiendo mensaje en la caja de texto del mensaje...")
                await input_box.click(force=True)
                await pagina.wait_for_timeout(500)
                try:
                    await input_box.fill("")  # Limpia el campo si es posible
                except:
                    await pagina.keyboard.press('Control+A')
                    await pagina.keyboard.press('Delete')
                await pagina.wait_for_timeout(500)
                print(f"📝 Escribiendo mensaje: {mensaje}")
                await input_box.type(mensaje, delay=50)
                await pagina.wait_for_timeout(1000)
                print("📤 Enviando mensaje con Enter...")
                await pagina.keyboard.press('Enter')
                await pagina.wait_for_timeout(2000)
                # Opcional: intenta hacer clic en el botón de enviar si existe
                try:
                    send_button = await pagina.query_selector('button[data-testid="send"], span[data-testid="send"]')
                    if send_button:
                        await send_button.click()
                        print("✅ También se hizo clic en el botón de enviar.")
                except:
                    print("ℹ️ No se encontró botón de enviar (normal si Enter funcionó).")
                # Confirmar envío
                try:
                    await pagina.wait_for_selector('[data-testid="msg-container"]', timeout=5000)
                    print("✅ Mensaje confirmado en la conversación.")
                except:
                    print("⚠️ No se pudo confirmar el mensaje en la conversación.")
                await pagina.screenshot(path="debug_screenshot.png")
                print("📸 Captura de pantalla guardada como debug_screenshot.png")
                print(f"✅ Mensaje enviado a {telefono}")
                await navegador.close()
                return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False

# Ejemplo de uso desde Flask (en tu endpoint):
# from whatsapp_servicio import WhatsAppServicio
# ws = WhatsAppServicio()
# asyncio.run(ws.enviar_mensaje(telefono, mensaje))