# FASE 0 - Análisis de Servicios Existentes

## Resumen de Servicios Systemd

### ✅ Servicio 1: `minicars-joystick.service`

**Ubicación**: `jetson/minicars-joystick.service`

**Descripción**: MiniCars Jetson TCP-to-UART joystick bridge

**ExecStart**: `/usr/bin/python3 /home/jetson-rod/minicars-control-station/jetson/tcp_uart_bridge.py`

**Función**: 
- ✅ Bridge TCP→UART para joystick
- ✅ Recibe comandos TCP en puerto 5005
- ✅ Envía comandos a Arduino vía UART (/dev/ttyTHS1)
- ✅ **NO TOCAR** - Funciona correctamente

**Dependencias**:
- After=network-online.target
- Wants=network-online.target

**Variables de entorno**:
- MINICARS_BRIDGE_HOST=0.0.0.0
- MINICARS_BRIDGE_PORT=5005
- MINICARS_UART_DEVICE=/dev/ttyTHS1
- MINICARS_UART_BAUD=115200
- MINICARS_WATCHDOG_MS=150
- MINICARS_LOG_LEVEL=INFO

### ✅ Servicio 2: `minicars-streamer.service`

**Ubicación**: `jetson/minicars-streamer.service`

**Descripción**: MiniCars Jetson GStreamer sender

**ExecStart**: `/usr/bin/python3 /home/jetson-rod/minicars-control-station/jetson/start_streamer.py`

**Función**:
- ✅ Streaming de cámara GStreamer
- ✅ Envía video H.264 vía UDP a la laptop
- ⚠️ **MODIFICAR**: Migrar lógica a supervisor con configuración dinámica

**Dependencias**:
- After=network-online.target
- (Falta `Wants=network-online.target` - añadir)

**Estado actual**:
- Restart=on-failure
- RestartSec=5
- El script `start_streamer.py` lanza pipeline directamente
- Host hardcodeado: "SKLNx.local"
- Puerto hardcodeado: 5000

## Script Actual de Streaming

### `jetson/start_streamer.py`

**Comando EXACTO que usa hoy**:
```python
gst_cmd = [
    "gst-launch-1.0", "-e",
    "nvarguscamerasrc",
    "!", 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1',
    "!", "nvvidconv", "flip-method=2",
    "!", 'video/x-raw(memory:NVMM),format=NV12',
    "!", "nvv4l2h264enc",
    "insert-sps-pps=true",
    "maxperf-enable=1",
    "control-rate=2",
    "bitrate=8000000",
    "iframeinterval=10",
    "!", "h264parse",
    "!", "rtph264pay", "config-interval=1", "pt=96",
    "!", "udpsink",
    "host=SKLNx.local",  # ← HARDCODEADO
    "port=5000",         # ← HARDCODEADO
    "sync=false",
    "async=false",
]
```

**Lógica actual**:
1. Resuelve hostname "SKLNx.local"
2. Reinicia nvargus-daemon
3. Espera 2 segundos
4. Lanza pipeline GStreamer (foreground, bloqueante)
5. Si pipeline falla → sys.exit(1) → systemd reinicia

**Problemas identificados**:
- ❌ Host y puerto hardcodeados
- ❌ No verifica conectividad antes de iniciar
- ❌ No verifica SSID (si está configurado)
- ❌ Si host no está disponible, el pipeline falla inmediatamente
- ❌ Reinicia nvargus-daemon en cada inicio (puede ser innecesario si ya está corriendo)

## Autostarts No-Systemd

### ❌ No se encontraron autostarts alternativos

- ❌ No hay referencias a crontab
- ❌ No hay referencias a .bashrc
- ❌ No hay referencias a .config/autostart
- ✅ Todo está gestionado vía systemd

## Conclusión

### ✅ Servicios a MIGRAR

1. **`minicars-streamer.service`**:
   - Mantener nombre del servicio (evitar duplicidades)
   - Cambiar `ExecStart` para apuntar a `stream_supervisor.py`
   - La lógica antigua de `start_streamer.py` se integrará en el supervisor

### ✅ Servicios a NO TOCAR

1. **`minicars-joystick.service`**:
   - Funciona correctamente
   - Independiente del streaming
   - No modificar

### 📋 Plan de Migración

1. Crear configuración centralizada (`jetson/config/stream_config.json`)
2. Crear supervisor (`jetson/stream_supervisor.py`)
3. Modificar `minicars-streamer.service` para usar supervisor
4. Mantener `start_streamer.py` como referencia (o deprecar si no se necesita)

