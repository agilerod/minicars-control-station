#!/usr/bin/env python3
"""
Script standalone para iniciar el receptor GStreamer en Windows.

Este script puede ejecutarse directamente desde la línea de comandos
para iniciar el receptor de video desde la Jetson Nano.

Uso:
    python start_receiver.py
"""
import sys
from pathlib import Path

# Agregar el directorio minicars_backend al path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from minicars_backend.commands.start_receiver import start_receiver

if __name__ == "__main__":
    result = start_receiver()
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    sys.exit(0 if result['status'] == 'ok' else 1)

