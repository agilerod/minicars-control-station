"""
Comando para detener el receptor GStreamer en Windows.
"""
import logging
import subprocess

from . import start_receiver

logger = logging.getLogger(__name__)


def stop_receiver() -> dict:
    """
    Detiene el receptor GStreamer si está corriendo.

    Returns:
        Dict con status y message indicando el resultado de la operación.
    """
    # Acceder a la variable global del módulo start_receiver
    if start_receiver._receiver_process is None or start_receiver._receiver_process.poll() is not None:
        return {
            "status": "ok",
            "message": "No había proceso de receiver corriendo.",
        }

    try:
        start_receiver._receiver_process.terminate()
        # Esperar un poco para que termine limpiamente
        try:
            start_receiver._receiver_process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            # Si no termina en 2 segundos, forzar cierre
            start_receiver._receiver_process.kill()
            start_receiver._receiver_process.wait()

        start_receiver._receiver_process = None
        logger.info("Receptor GStreamer detenido correctamente")
        return {
            "status": "ok",
            "message": "Proceso de receiver GStreamer detenido.",
        }
    except Exception as exc:
        logger.error(f"Error al detener receptor GStreamer: {exc}")
        return {
            "status": "error",
            "message": f"Error al detener receiver GStreamer: {exc}",
        }

