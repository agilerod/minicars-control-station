"""
Comando para detener el control del vehículo RC.
"""
import logging

logger = logging.getLogger(__name__)


def stop_car_control() -> dict:
    """
    Detiene el sistema de control del vehículo RC.
    
    Detiene el JoystickSender y envía un comando de failsafe
    antes de cerrar la conexión.
    
    Returns:
        Dict con status y message indicando el resultado.
    """
    # Import here to access the global variable from start_car_control
    from . import start_car_control
    
    if start_car_control._joystick_sender is None:
        return {
            "status": "ok",
            "message": "Car control not running",
        }
    
    try:
        start_car_control._joystick_sender.stop()
        start_car_control._joystick_sender = None
        
        logger.info("Joystick sender stopped")
        return {
            "status": "ok",
            "message": "Joystick sender stopped",
        }
    except Exception as e:
        logger.error(f"Failed to stop joystick sender: {e}", exc_info=True)
        # Try to cleanup anyway
        start_car_control._joystick_sender = None
        return {
            "status": "error",
            "message": f"Failed to stop: {str(e)}",
        }


