"""
Utilidad para verificar la instalación de GStreamer en Windows.

Este módulo busca el ejecutable gst-launch-1.0.exe en las ubicaciones comunes
y valida que esté disponible para su uso.
"""
import os
import shutil
from pathlib import Path
from typing import Optional


def find_gstreamer_executable() -> Optional[Path]:
    """
    Busca el ejecutable gst-launch-1.0.exe en las ubicaciones comunes.

    Busca en:
    1. C:\Program Files\gstreamer\1.0\mingw_x86_64\bin\gst-launch-1.0.exe
    2. C:\gstreamer\1.0\mingw_x86_64\bin\gst-launch-1.0.exe
    3. PATH del sistema

    Returns:
        Path al ejecutable si se encuentra, None en caso contrario.
    """
    # Rutas comunes de instalación
    common_paths = [
        Path(r"C:\Program Files\gstreamer\1.0\mingw_x86_64\bin\gst-launch-1.0.exe"),
        Path(r"C:\gstreamer\1.0\mingw_x86_64\bin\gst-launch-1.0.exe"),
    ]

    # Verificar rutas comunes
    for path in common_paths:
        if path.exists() and path.is_file():
            return path

    # Buscar en PATH
    gst_launch = shutil.which("gst-launch-1.0.exe")
    if gst_launch:
        return Path(gst_launch)

    return None


def check_gstreamer_installation() -> dict:
    """
    Verifica que GStreamer esté instalado y disponible.

    Returns:
        Dict con:
            - installed: bool indicando si está instalado
            - path: Path al ejecutable si está instalado, None en caso contrario
            - message: Mensaje descriptivo del estado
    """
    executable_path = find_gstreamer_executable()

    if executable_path:
        return {
            "installed": True,
            "path": str(executable_path),
            "message": f"GStreamer encontrado en: {executable_path}",
        }

    return {
        "installed": False,
        "path": None,
        "message": (
            "GStreamer no encontrado. "
            "Por favor, instala GStreamer desde https://gstreamer.freedesktop.org/download/ "
            "o verifica que esté en el PATH del sistema."
        ),
    }


def get_gstreamer_path() -> Path:
    """
    Obtiene la ruta del ejecutable de GStreamer.

    Raises:
        FileNotFoundError: Si GStreamer no está instalado.

    Returns:
        Path al ejecutable gst-launch-1.0.exe
    """
    executable_path = find_gstreamer_executable()
    if executable_path is None:
        raise FileNotFoundError(
            "GStreamer no está instalado o no se encuentra en el PATH. "
            "Instala GStreamer desde https://gstreamer.freedesktop.org/download/"
        )
    return executable_path

