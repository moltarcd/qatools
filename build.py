import subprocess

APP_NAME = "QA_Tools_Toolkit"

# Configuramos los parámetros estrictos de PyInstaller para PyWebView
cmd = [
    "pyinstaller",
    "--noconfirm",   # Sobrescribe carpetas de compilación anteriores automáticamente
    "--onedir",      # Agrupa todo en una carpeta 
    "--windowed",    # OCULTA la consola negra de Windows detrás de la interfaz gráfica
    f"--name={APP_NAME}",
    # Copia de forma explícita tu carpeta web adentro del paquete empaquetado
    "--add-data=web;web", 
    "main.py"
]

print(f"🤖 Iniciando empaquetado de {APP_NAME}...")
subprocess.run(cmd, check=True)
print("✨ ¡Proceso terminado! Revisá la carpeta 'dist/'")