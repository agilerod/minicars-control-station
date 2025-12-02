# MiniCars Joystick Control - Implementation TODO

## Status: EN PROGRESO - Continuación

### Estado Actual (Batch de Implementación)

✅ **YA COMPLETADO:**
- Documentación de diseño
- Módulo de perfiles (profiles.py)
- Protocolo TCP (protocol.py)
- Sender básico (sender.py)

✅ **COMPLETADO EN ESTE BATCH:**
- [x] `jetson/tcp_uart_bridge.py` - Bridge completo con watchdog
- [x] `jetson/minicars-joystick.service` - Systemd unit
- [x] Actualización de `deploy_to_jetson.sh`
- [x] Integración de JoystickSender con endpoints
- [x] Componente UI `DrivingModeSelector` (ya existía, está OK)
- [x] `docs/testing_joystick.md`
- [x] Dependencias agregadas (pygame, pyserial)

Se han creado los componentes fundamentales del sistema. Continuando con la implementación completa...

## ✅ Completado

1. **Documentación de diseño**: `docs/joystick_control_notes.md`
2. **Módulo de perfiles**: `backend/minicars_backend/joystick/profiles.py`
3. **Protocolo TCP**: `backend/minicars_backend/joystick/protocol.py`
4. **Sender básico**: `backend/minicars_backend/joystick/sender.py`

## 🚧 Pendiente (CRÍTICO)

### 1. Jetson TCP-UART Bridge
**Archivo**: `minicars-control-station/jetson/tcp_uart_bridge.py`

```python
#!/usr/bin/env python3
"""
MiniCars TCP-to-UART Bridge for Jetson Nano.
Receives joystick commands via TCP and forwards to Arduino via UART.
"""
import logging
import os
import socket
import threading
import time
from typing import Optional

import serial

# Configuración desde variables de entorno
BRIDGE_HOST = os.getenv("MINICARS_BRIDGE_HOST", "0.0.0.0")
BRIDGE_PORT = int(os.getenv("MINICARS_BRIDGE_PORT", "5005"))
UART_DEVICE = os.getenv("MINICARS_UART_DEVICE", "/dev/ttyTHS1")
UART_BAUD = int(os.getenv("MINICARS_UART_BAUD", "115200"))
WATCHDOG_MS = int(os.getenv("MINICARS_WATCHDOG_MS", "150"))
LOG_LEVEL = os.getenv("MINICARS_LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='[minicars-joystick-bridge] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# TODO: Implementar:
# 1. Clase TCPUARTBridge con:
#    - Socket TCP servidor
#    - Puerto serial/UART
#    - Thread watchdog
#    - Variables de estado (last_msg_ts, last_servo, last_throttle)
# 2. Método main loop:
#    - Escucha conexiones TCP
#    - Lee líneas, parsea con protocol.parse_message()
#    - Valida y aplica suavizado
#    - Convierte a formato UART con msg.to_uart_format()
#    - Escribe a serial
# 3. Thread watchdog:
#    - Revisa cada 20ms si han pasado >WATCHDOG_MS sin mensaje
#    - Si timeout, envía failsafe a UART
# 4. Manejo de señales para shutdown graceful

if __name__ == "__main__":
    logger.info("Starting MiniCars TCP-UART Bridge")
    logger.info(f"TCP: {BRIDGE_HOST}:{BRIDGE_PORT}")
    logger.info(f"UART: {UART_DEVICE} @ {UART_BAUD} baud")
    # TODO: Instanciar y ejecutar bridge
```

### 2. Systemd Unit para Joystick
**Archivo**: `minicars-control-station/jetson/minicars-joystick.service`

```ini
[Unit]
Description=MiniCars Jetson TCP-to-UART bridge (joystick)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=jetson-rod
Group=jetson-rod
WorkingDirectory=/home/jetson-rod/minicars-control-station/jetson
Environment="MINICARS_BRIDGE_HOST=0.0.0.0"
Environment="MINICARS_BRIDGE_PORT=5005"
Environment="MINICARS_UART_DEVICE=/dev/ttyTHS1"
Environment="MINICARS_UART_BAUD=115200"
Environment="MINICARS_WATCHDOG_MS=150"
Environment="MINICARS_LOG_LEVEL=INFO"
ExecStart=/usr/bin/python3 /home/jetson-rod/minicars-control-station/jetson/tcp_uart_bridge.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 3. Actualizar deploy_to_jetson.sh
**Agregar al final del script existente**:

```bash
# Sincronizar servicio joystick
echo "Sincronizando servicio minicars-joystick..."
echo "-----------------------------------"
if [ -f "jetson/minicars-joystick.service" ]; then
    sudo cp jetson/minicars-joystick.service /etc/systemd/system/minicars-joystick.service
    sudo systemctl daemon-reload
    sudo systemctl enable minicars-joystick.service
    sudo systemctl restart minicars-joystick.service
    echo -e "${GREEN}✓${NC} Servicio minicars-joystick sincronizado y reiniciado"
else
    echo -e "${YELLOW}⚠${NC} No se encontró jetson/minicars-joystick.service"
fi
echo ""

# Mostrar estado del servicio joystick
echo "=========================================="
echo "Estado del servicio joystick:"
echo "=========================================="
sudo systemctl status minicars-joystick --no-pager || true
echo ""
```

### 4. Actualizar start_car_control.py

```python
from minicars_backend.joystick import JoystickSender

_joystick_sender: Optional[JoystickSender] = None

def start_car_control() -> dict:
    global _joystick_sender
    
    if _joystick_sender is not None:
        return {"status": "ok", "message": "Car control already running"}
    
    try:
        _joystick_sender = JoystickSender(
            target_host="SKLNx.local",
            target_port=5005,
            send_hz=20,
        )
        _joystick_sender.start()
        return {"status": "ok", "message": "Joystick sender started"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to start: {e}"}
```

### 5. Actualizar stop_car_control.py

```python
def stop_car_control() -> dict:
    global _joystick_sender
    
    if _joystick_sender is None:
        return {"status": "ok", "message": "Car control not running"}
    
    try:
        _joystick_sender.stop()
        _joystick_sender = None
        return {"status": "ok", "message": "Joystick sender stopped"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to stop: {e}"}
```

### 6. Mejorar UI Desktop - DrivingModeSelector
**Archivo**: `desktop/src/components/DrivingModeSelector.tsx`

```typescript
// Actualizar para mostrar descripciones de cada modo
// Agregar indicador visual de sensibilidad
// Estilos para hacerlo más atractivo visualmente
```

### 7. Testing Guide
**Archivo**: `minicars-control-station/docs/testing_joystick.md`

Crear guía completa con:
- Pruebas en Jetson (journalctl)
- Pruebas en laptop (backend + desktop)
- Verificación de failsafe
- Cambio entre modos

## 📋 Checklist Final - ✅ COMPLETADO

- [x] Completar `jetson/tcp_uart_bridge.py` con watchdog y serial
- [x] Crear `jetson/minicars-joystick.service`
- [x] Actualizar `deploy_to_jetson.sh`
- [x] Actualizar `start_car_control.py` y `stop_car_control.py`
- [x] UI desktop (DrivingModeSelector ya existe y funciona)
- [x] Crear `docs/testing_joystick.md`
- [x] Alinear modos a "kid/normal/sport" en todo el sistema
- [x] Agregar settings de joystick a settings.py
- [x] Pygame import con manejo robusto de errores
- [x] Logging estructurado con prefijos consistentes
- [x] Agregar pygame a requirements.txt
- [x] Agregar pyserial a jetson/requirements.txt
- [ ] **ÚNICO PENDIENTE**: Probar end-to-end con hardware real

## ✅ SISTEMA LISTO PARA DEPLOYMENT Y TESTING

## 🔧 Dependencias Faltantes

### Backend (laptop):
```txt
pygame>=2.5.0
```

### Jetson:
```txt
pyserial>=3.5
```

## 🚀 Para Continuar

1. Completar el archivo `tcp_uart_bridge.py` con toda la lógica
2. Probar localmente el sender con un servidor TCP dummy
3. Deploy a Jetson y probar el bridge
4. Integrar UI
5. Testing exhaustivo

Ver `docs/joystick_control_notes.md` para el diseño completo.

