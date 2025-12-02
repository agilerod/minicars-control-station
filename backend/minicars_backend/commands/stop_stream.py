"""
Comando para detener el viewer de GStreamer en Windows.
"""
import subprocess

# Importamos el módulo completo para acceder a su variable global
from . import start_stream


def stop_stream() -> dict:
    """
    Detiene el viewer de GStreamer si está corriendo.
    """
    # Acceder a la variable global del módulo start_stream
    # Si no hay proceso registrado o ya terminó, no hacemos nada
    if start_stream._stream_process is None or start_stream._stream_process.poll() is not None:
        return {
            "status": "ok",
            "message": "No había proceso de stream corriendo.",
        }

    try:
        start_stream._stream_process.terminate()
        start_stream._stream_process = None
        return {
            "status": "ok",
            "message": "Proceso de GStreamer detenido.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Error al detener GStreamer: {exc}",
        }
