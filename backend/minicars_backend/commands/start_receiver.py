"""
Comando para iniciar el receptor GStreamer en Windows.

Este módulo maneja el proceso del receptor de video desde la Jetson Nano.
Usa el chequeo de GStreamer para validar la instalación antes de iniciar.
"""
import logging
import subprocess
from typing import Optional

from ..utils.check_gstreamer import get_gstreamer_path

logger = logging.getLogger(__name__)

# Variable global para almacenar el proceso del receptor
_receiver_process: Optional[subprocess.Popen] = None


def start_receiver() -> dict:
    """
    Inicia el receptor GStreamer en Windows si no está corriendo.

    El receptor escucha en el puerto UDP 5000 y muestra el video en una ventana.

    Returns:
        Dict con status y message indicando el resultado de la operación.
    """
    global _receiver_process

    try:
        # Validar que GStreamer está instalado
        gst_launch = get_gstreamer_path()
        logger.info(f"Usando GStreamer en: {gst_launch}")
    except FileNotFoundError as e:
        return {
            "status": "error",
            "message": str(e),
        }

    # Verificar si ya hay un proceso corriendo
    if _receiver_process is not None and _receiver_process.poll() is None:
        return {
            "status": "ok",
            "message": "Receiver ya está corriendo (proceso existente).",
        }

    # Pipeline GStreamer para recibir video RTP/H264
    # - rtpjitterbuffer latency=30: buffer de 30ms para compensar jitter en WiFi
    # - drop-on-late=true: descarta paquetes tardíos para mantener latencia baja
    pipeline = (
        f'"{gst_launch}" -v '
        'udpsrc port=5000 caps="application/x-rtp,media=video,encoding-name=H264,payload=96,clock-rate=90000" ! '
        'rtpjitterbuffer latency=30 drop-on-late=true ! '
        'rtph264depay ! h264parse ! '
        'avdec_h264 ! videoconvert ! autovideosink sync=false'
    )

    try:
        # shell=True porque usamos la sintaxis de pipeline con "!"
        proc = subprocess.Popen(
            pipeline,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _receiver_process = proc

        logger.info("Receptor GStreamer iniciado correctamente")
        return {
            "status": "ok",
            "message": "Receiver running... GStreamer iniciado para recibir video desde la Jetson.",
        }
    except Exception as exc:
        logger.error(f"Error al iniciar receptor GStreamer: {exc}")
        return {
            "status": "error",
            "message": f"Error al iniciar receptor GStreamer: {exc}",
        }

