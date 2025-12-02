"""
MiniCars Backend - Production Entrypoint

Este es el entrypoint para el backend empaquetado con PyInstaller.
En desarrollo, usar: uvicorn minicars_backend.api:app --reload
"""
import sys
import uvicorn
from minicars_backend.api import app
from minicars_backend.settings import get_settings

def main():
    """Inicia el servidor uvicorn en modo producción."""
    settings = get_settings()
    
    print(f"[MiniCars Backend] Starting on {settings.backend_host}:{settings.backend_port}")
    print(f"[MiniCars Backend] Environment: {settings.env}")
    
    uvicorn.run(
        app,
        host=settings.backend_host,
        port=settings.backend_port,
        log_level="info",
        access_log=False,  # Reducir verbosidad en producción
    )

if __name__ == "__main__":
    main()

