"""
Comando para lanzar el viewer de GStreamer en Windows.

Este módulo maneja el proceso del stream de video desde la Jetson Nano.
"""
import subprocess
from pathlib import Path
from typing import Optional

# Ruta del ejecutable de GStreamer en Windows
GST_LAUNCH = Path(r"C:\Program Files\gstreamer\1.0\mingw_x86_64\bin\gst-launch-1.0.exe")

# Variable global simple para almacenar el proceso del viewer
_stream_process: Optional[subprocess.Popen] = None


def start_stream() -> dict:
    """
    Lanza el viewer de GStreamer en Windows si no está corriendo.

    Este comando reemplaza al gst-launch que hoy se ejecuta manualmente
    en PowerShell.
    """
    global _stream_process

    # 1) Validar que existe el binario
    if not GST_LAUNCH.exists():
        return {
            "status": "error",
            "message": f"No se encontró gst-launch en '{GST_LAUNCH}'. "
                       "Verifica la instalación de GStreamer o ajusta la ruta en start_stream.py.",
        }

    # 2) Si ya hay un proceso vivo, no lanzar otro
    if _stream_process is not None and _stream_process.poll() is None:
        return {
            "status": "ok",
            "message": "Stream ya está corriendo (proceso existente).",
        }

    # 3) Pipeline GStreamer receptor optimizada
    # - rtpjitterbuffer latency=30: buffer de 30ms para compensar jitter en WiFi
    # - drop-on-late=true: descarta paquetes tardíos para mantener latencia baja
    pipeline = (
        f'"{GST_LAUNCH}" -v '
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
        )
        _stream_process = proc

        return {
            "status": "ok",
            "message": "GStreamer lanzado para recibir video desde la Jetson.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "message": f"Error al lanzar GStreamer: {exc}",
        }
