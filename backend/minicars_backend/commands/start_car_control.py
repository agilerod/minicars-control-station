"""
Comando para iniciar el control del vehículo RC.

Usa el nuevo sistema de joystick con JoystickSender que envía
comandos a la Jetson vía TCP, alineado con car_control_logi.py.
"""
import logging
from typing import Optional

from ..joystick import JoystickSender
from ..control_profiles import load_profile
from ..settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global sender instance
_joystick_sender: Optional[JoystickSender] = None


def start_car_control() -> dict:
    """
    Inicia el sistema de control del vehículo RC.
    
    Lanza el JoystickSender que lee el joystick y envía comandos
    a la Jetson vía TCP, aplicando el perfil de conducción activo.
    
    Returns:
        Dict con status, message y details indicando el resultado.
    """
    global _joystick_sender
    
    # Verificar si ya está corriendo
    if _joystick_sender is not None and _joystick_sender._running:
        logger.info("[CAR CONTROL] Joystick sender already running")
        return {
            "status": "already_running",
            "message": "Car control already running",
            "details": f"Target: {settings.joystick_target_host}:{settings.joystick_target_port}",
        }
    
    try:
        # Obtener modo activo
        profile_data = load_profile()
        active_mode = profile_data.get("active_mode", "normal")
        
        logger.info(
            f"[CAR CONTROL] Starting joystick sender with "
            f"JETSON_IP={settings.joystick_target_host}, "
            f"PORT={settings.joystick_target_port}, "
            f"FREQ={settings.joystick_send_hz}Hz, "
            f"MODE={active_mode}"
        )
        
        # Crear y iniciar sender usando settings centralizados
        _joystick_sender = JoystickSender(
            target_host=settings.joystick_target_host,
            target_port=settings.joystick_target_port,
            send_hz=settings.joystick_send_hz,
        )
        _joystick_sender.start()
        
        # Verificar que realmente se inició
        if not _joystick_sender._running:
            _joystick_sender = None
            return {
                "status": "error",
                "message": "Failed to start joystick sender (check logs for details)",
                "details": "Joystick sender thread did not start. Check if joystick is connected and pygame is installed.",
            }
        
        logger.info(f"[CAR CONTROL] Joystick sender started successfully (mode: {active_mode})")
        return {
            "status": "ok",
            "message": f"Joystick sender started in {active_mode} mode",
            "details": f"Connected to {settings.joystick_target_host}:{settings.joystick_target_port} at {settings.joystick_send_hz}Hz",
        }
    except Exception as e:
        logger.error(f"[CAR CONTROL] Failed to start joystick sender: {e}", exc_info=True)
        _joystick_sender = None
        return {
            "status": "error",
            "message": f"Failed to start: {str(e)}",
            "details": f"Exception: {type(e).__name__}. Check logs for full traceback.",
        }


