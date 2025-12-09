"""
MiniCars Backend - Production Entrypoint

Este es el entrypoint para el backend empaquetado con PyInstaller.
En desarrollo, usar: uvicorn minicars_backend.api:app --reload

Para uso con Tauri, este módulo expone `app` directamente para que
uvicorn pueda ejecutarlo con: uvicorn main:app
"""
from minicars_backend.api import app

# Exponer app directamente para que uvicorn pueda usarlo con main:app
__all__ = ["app"]

