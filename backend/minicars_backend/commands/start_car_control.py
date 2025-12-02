"""
Comando para iniciar el control del vehículo RC.

Usa el nuevo sistema de joystick con JoystickSender que envía
comandos a la Jetson vía TCP.
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
        Dict con status y message indicando el resultado.
    """
    global _joystick_sender
    
    # Verificar si ya está corriendo
    if _joystick_sender is not None:
        return {
            "status": "ok",
            "message": "Car control already running",
        }
    
    try:
        # Obtener modo activo
        profile_data = load_profile()
        active_mode = profile_data.get("active_mode", "normal")
        
        # Crear y iniciar sender usando settings centralizados
        _joystick_sender = JoystickSender(
            target_host=settings.joystick_target_host,
            target_port=settings.joystick_target_port,
            send_hz=settings.joystick_send_hz,
        )
        _joystick_sender.start()
        
        logger.info(f"Joystick sender started (mode: {active_mode})")
        return {
            "status": "ok",
            "message": f"Joystick sender started in {active_mode} mode",
        }
    except Exception as e:
        logger.error(f"Failed to start joystick sender: {e}", exc_info=True)
        _joystick_sender = None
        return {
            "status": "error",
            "message": f"Failed to start: {str(e)}",
        }


