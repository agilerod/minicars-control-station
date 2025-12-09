"""
Configuración centralizada del backend MiniCars.

Lee variables de entorno con prefijo MINICARS_ desde backend/.env en desarrollo.
"""
from functools import lru_cache
from pathlib import Path
from typing import Optional

try:
    from pydantic_settings import BaseSettings
    from pydantic import AnyHttpUrl
except ImportError:
    # Fallback para Pydantic v1 o si pydantic-settings no está disponible
    try:
        from pydantic import BaseSettings, AnyHttpUrl
    except ImportError:
        # Fallback final: usar os.environ directamente
        import os
        from typing import Any
        
        class BaseSettings:
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        AnyHttpUrl = str


class Settings(BaseSettings):
    """Configuración del backend MiniCars."""
    
    env: str = "dev"
    """Entorno de ejecución: dev, prod, etc."""
    
    # Backend propio (FastAPI)
    backend_host: str = "127.0.0.1"
    """Host donde se ejecuta el servidor FastAPI."""
    
    backend_port: int = 8000
    """Puerto donde se ejecuta el servidor FastAPI."""
    
    # URL base desde donde otros componentes llaman a este backend
    public_backend_url: AnyHttpUrl = "http://127.0.0.1:8000"
    """URL base pública del backend. Usada por el frontend y otros clientes."""
    
    # URL base a la Jetson (pensando en futuro, aunque ahora no se use mucho)
    jetson_base_url: Optional[AnyHttpUrl] = None
    """
    URL base del backend/control que corre en la Jetson Nano.
    Se puede usar en el futuro para enviar comandos o consultar estado directamente a la Jetson.
    Por ejemplo: http://192.168.0.50:9000
    """
    
    # Joystick / Car Control settings
    joystick_target_host: str = "192.168.68.102"
    """Hostname o IP de la Jetson Nano para envío de comandos de joystick.
    Default: 192.168.68.102 (puede sobreescribirse con MINICARS_JOYSTICK_TARGET_HOST).
    Si usas hostname como SKLNx.local, asegúrate de que resuelva correctamente."""
    
    joystick_target_port: int = 5005
    """Puerto TCP en la Jetson para el bridge TCP-UART."""
    
    joystick_send_hz: int = 100
    """Frecuencia de envío de comandos de joystick (Hz).
    Default: 100Hz para mejor responsividad (coincide con car_control_logi.py).
    Puede reducirse a 20Hz si hay problemas de red."""
    
    joystick_reconnect_delay: float = 2.0
    """Delay en segundos entre intentos de reconexión al bridge de Jetson."""
    
    class Config:
        env_prefix = "MINICARS_"
        # Busca .env en el directorio backend (un nivel arriba de minicars_backend/)
        env_file = str(Path(__file__).parent.parent / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la instancia singleton de Settings."""
    return Settings()

