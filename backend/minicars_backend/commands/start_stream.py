"""
Comando para lanzar el viewer de GStreamer en Windows.

Este módulo maneja el proceso del stream de video desde la Jetson Nano.
Unificado con start_receiver para usar la misma lógica de detección de GStreamer.
"""
import logging
import subprocess
from typing import Optional

from ..utils.check_gstreamer import get_gstreamer_path

logger = logging.getLogger(__name__)

# Variable global simple para almacenar el proceso del viewer
_stream_process: Optional[subprocess.Popen] = None


def start_stream() -> dict:
    """
    Lanza el viewer de GStreamer en Windows si no está corriendo.

    Este comando lanza el receptor de video que escucha en UDP 5000
    y muestra el stream desde la Jetson Nano.

    Returns:
        Dict con status, message y details indicando el resultado.
    """
    global _stream_process

    try:
        # Validar que GStreamer está instalado (usa el mismo sistema que start_receiver)
        gst_launch = get_gstreamer_path()
        logger.info(f"[STREAM] Using GStreamer at: {gst_launch}")
    except FileNotFoundError as e:
        logger.error(f"[STREAM] GStreamer not found: {e}")
        return {
            "status": "error",
            "message": str(e),
            "details": "GStreamer is required to receive video stream from Jetson. Please install GStreamer.",
        }

    # Verificar si ya hay un proceso vivo
    if _stream_process is not None:
        poll_result = _stream_process.poll()
        if poll_result is None:
            # Proceso aún corriendo
            logger.info("[STREAM] Stream receiver already running")
            return {
                "status": "already_running",
                "message": "Stream receiver already running",
                "details": "GStreamer receiver process is already active on UDP port 5000",
            }
        else:
            # Proceso terminó, limpiar referencia
            logger.info(f"[STREAM] Previous process ended (exit code: {poll_result}), starting new one")
            _stream_process = None

    # Pipeline GStreamer receptor optimizada
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
        logger.info("[STREAM] Starting camera receiver on UDP port 5000...")
        # shell=True porque usamos la sintaxis de pipeline con "!"
        proc = subprocess.Popen(
            pipeline,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _stream_process = proc

        logger.info("[STREAM] GStreamer receiver started successfully")
        logger.info("[STREAM] NOTE: Ensure Jetson streamer is running (minicars-streamer.service or manually)")
        return {
            "status": "ok",
            "message": "GStreamer receiver started for video stream from Jetson",
            "details": "Listening on UDP port 5000. Video window should appear shortly. Ensure Jetson streamer is running.",
        }
    except Exception as exc:
        logger.error(f"[STREAM] Error launching GStreamer: {exc}", exc_info=True)
        return {
            "status": "error",
            "message": f"Error launching GStreamer: {exc}",
            "details": f"Failed to start GStreamer process. Check GStreamer installation and logs.",
        }
