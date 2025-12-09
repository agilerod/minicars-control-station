"""
Comando para detener el viewer de GStreamer en Windows.
"""
import logging
import subprocess

# Importamos el módulo completo para acceder a su variable global
from . import start_stream

logger = logging.getLogger(__name__)


def stop_stream() -> dict:
    """
    Detiene el viewer de GStreamer si está corriendo.

    Returns:
        Dict con status, message y details indicando el resultado.
    """
    # Acceder a la variable global del módulo start_stream
    # Si no hay proceso registrado o ya terminó, no hacemos nada
    if start_stream._stream_process is None or start_stream._stream_process.poll() is not None:
        logger.info("[STREAM] No stream process running")
        return {
            "status": "ok",
            "message": "No stream process was running",
            "details": "GStreamer receiver was not active",
        }

    try:
        logger.info("[STREAM] Stopping GStreamer receiver...")
        start_stream._stream_process.terminate()
        # Esperar un poco para que termine limpiamente
        try:
            start_stream._stream_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            # Si no termina en 2 segundos, forzar cierre
            logger.warning("[STREAM] GStreamer did not terminate gracefully, forcing kill...")
            start_stream._stream_process.kill()
            start_stream._stream_process.wait()

        start_stream._stream_process = None
        logger.info("[STREAM] GStreamer receiver stopped successfully")
        return {
            "status": "ok",
            "message": "GStreamer receiver stopped",
            "details": "Video stream receiver process terminated",
        }
    except Exception as exc:
        logger.error(f"[STREAM] Error stopping GStreamer: {exc}", exc_info=True)
        # Try to cleanup anyway
        start_stream._stream_process = None
        return {
            "status": "error",
            "message": f"Error stopping GStreamer: {exc}",
            "details": "Stream process may still be running. Check logs for details.",
        }
