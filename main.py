import sys
import os

# =========================================================================
# 1. PARCHE ANTICIPADO DE CONSOLA VIRTUAL (EVITA ERROR 'isatty' EN EL .EXE)
# =========================================================================
if getattr(sys, 'frozen', False):
    # Si la app corre congelada (.exe), interceptamos los descriptores estándar
    # para que las librerías de red (Telnet/SSH) no rompan por falta de consola.
    for stream_name in ('stdout', 'stderr', 'stdin'):
        if getattr(sys, stream_name) is None:
            class SafeDummyStream:
                def write(self, x): pass
                def flush(self): pass
                def isatty(self): return False
                def __getattr__(self, name): return None  # Evita fallos si buscan encoding, buffer, etc.

            setattr(sys, stream_name, SafeDummyStream())

# =========================================================================
# 2. CONFIGURACIÓN COMPLETA DE LOGGING (ADAPTATIVA)
# =========================================================================
import logging

# Creamos el objeto logger centralizado
logger = logging.getLogger('QA-Toolkit')

if getattr(sys, 'frozen', False):
    # Entorno COMPILADO (.exe): Silenciamos la salida a consola para evitar fugas de streams
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s',
        handlers=[logging.NullHandler()]
    )
else:
    # Entorno de DESARROLLO (VS Code): Mantenemos el StreamHandler nativo que usás siempre
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s [%(levelname)s] (%(threadName)s) %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

# =========================================================================
# 3. IMPORTACIONES DEL PROYECTO (AHORA HEREDAN EL PARCHE DE FORMA SEGURA)
# =========================================================================
import webview
from scripts.tarjetas import flujo_completo_tarjetas
from scripts.legacy import ejecutar_captura_outsideview, ejecutar_flujo_obey
from scripts.unix import UnixLogMonitor

# INSTANCIAS GLOBALES
window_referencia = None
monitor_unix_global = UnixLogMonitor()

# =========================================================================
# 4. CAPA DE API EXPOESTA A JAVASCRIPT
# =========================================================================
class QA_Toolkit_API:
    def __init__(self):
        pass

    def btn_generar_tarjeta_click(self, bin_usuario, cantidad):
        logger.info(f"UI solicitando generación de {cantidad} tarjetas para el BIN {bin_usuario}")
        return flujo_completo_tarjetas(bin_usuario, cantidad)
        
    def btn_captura_outsideview_click(self, cantidad, demora, ruta):
        logger.info(f"UI solicitando inicio de capturas OutsideView. Cantidad: {cantidad}")
        return ejecutar_captura_outsideview(cantidad, demora, ruta)

    def btn_ejecutar_obey_click(self, host, port, user, password, subvol, obey_name):
        logger.info(f"UI solicitando ejecución de macro Telnet: {obey_name}")
        return ejecutar_flujo_obey(host, port, user, password, subvol, obey_name)
    
    def btn_procesar_cripto_click(self, operacion, valor):
        logger.info(f"UI solicitando operación criptográfica de Tarjetas: [{operacion}]")
        try:
            from scripts.tarjetas import desencriptar_pan_core, procesar_cripto_cvv2
            
            if operacion == "DESENCRIPTAR_PAN":
                resultado_plano = desencriptar_pan_core(valor)
                return {"status": "success", "resultado": resultado_plano}
                
            elif operacion in ["ENCRIPTAR_CVV2", "DESENCRIPTAR_CVV2"]:
                resultado_cvv = procesar_cripto_cvv2(operacion, valor)
                return {"status": "success", "resultado": resultado_cvv}
                
            else:
                return {"status": "error", "message": "Operación no soportada."}
                
        except Exception as e:
            logger.error(f"Error criptográfico en backend: {str(e)}")
            return {"status": "error", "message": str(e)}

    # MÉTODOS DEL MONITOR UNIX
    def iniciar_tail_unix(self, host, port, user, password, filepath, filter_path):
        logger.info(f"UI solicitando Tail Unix por bloque transaccional. Archivo: {filepath}. Filtro Path: '{filter_path}'")
        try:
            global window_referencia, monitor_unix_global
            
            monitor_unix_global.iniciar_monitoreo(
                host=host,
                port=port,
                user=user,
                password=password,
                filepath=filepath,
                filter_path=filter_path,
                window_instance=window_referencia
            )
            return {"status": "success", "message": "Monitoreo SSH por bloque iniciado."}
        except Exception as e:
            logger.error(f"Error al intentar lanzar el hilo de Unix: {str(e)}")
            return {"status": "error", "message": str(e)}
        
    def detener_tail_unix(self):
        logger.info("UI solicitando detener el monitoreo Unix.")
        global monitor_unix_global
        monitor_unix_global.detener_monitoreo()
        return {"status": "success", "message": "Monitoreo detenido con éxito."}

# =========================================================================
# 5. ORQUESTACIÓN E INICIO DE LA APLICACIÓN
# =========================================================================
def iniciar_app():
    global window_referencia
    
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    ruta_html = os.path.join(base_dir, 'web', 'index.html')
    logger.info(f"Cargando interfaz de usuario desde: {ruta_html}")

    api_toolkit = QA_Toolkit_API()
    
    window = webview.create_window(
        title="QA Tools Toolkit",
        url=ruta_html,
        js_api=api_toolkit,
        width=1000,
        height=950
    )
    
    window_referencia = window
    webview.start(debug=True)

if __name__ == '__main__':
    iniciar_app()