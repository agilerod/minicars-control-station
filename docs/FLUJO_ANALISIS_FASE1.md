# FASE 1 - Análisis de Flujo Actual (Solo Lectura)

## Endpoints FastAPI

### 1. "Start Car Control" - `/actions/start_car_control`

**Archivo**: `backend/minicars_backend/api.py`  
**Función**: `actions_start_car_control()` (línea 91-98)  
**Dispara**: `start_car_control()` desde `backend/minicars_backend/commands/start_car_control.py`

**Flujo**:
- `start_car_control()` crea un `JoystickSender` (línea 56-60)
- `JoystickSender` está en `backend/minicars_backend/joystick/sender.py`
- Usa settings de `backend/minicars_backend/settings.py`:
  - `joystick_target_host` (default: "192.168.68.102")
  - `joystick_target_port` (default: 5005)
  - `joystick_send_hz` (default: 100 Hz)
- Lee perfil activo de `backend/config/control_profile.json`
- **NO lanza proceso externo** - ejecuta en thread interno del backend

**Problema detectado**:
- `JoystickSender` usa `to_uart_format()` que envía **5 campos** (formato: `servo_angle,accel_pct,brake_pct,hbrake_flag,turbo_flag\n`)
- El bridge en Jetson (`jetson/tcp_uart_bridge.py`) espera **6 campos** (formato: `servo,throttle,brake,handbrake,turbo,mode\n`)
- Por lo tanto, todos los mensajes son rechazados por el bridge

**Lógica de mapeo**:
- `JoystickSender` usa `DrivingProfile` de `backend/minicars_backend/joystick/profiles.py`
- `car_control_logi.py` usa `map_pedal_to_throttle()` con deadzone, expo, y ramp más sofisticados
- Las dos lógicas son diferentes

### 2. "Start Stream" - `/actions/start_stream`

**Archivo**: `backend/minicars_backend/api.py`  
**Función**: `actions_start_stream()` (línea 59-64)  
**Dispara**: `start_stream()` desde `backend/minicars_backend/commands/start_stream.py`

**Flujo**:
- Valida que GStreamer esté instalado (usa `get_gstreamer_path()`)
- Lanza `subprocess.Popen` con pipeline GStreamer (líneas 66-71)
- Pipeline: receptor UDP en puerto 5000
- **Comando ejecutado**: `gst-launch-1.0` con pipeline de recepción RTP/H264

**Problema detectado**:
- Solo lanza el **receptor** en la laptop
- **NO lanza el emisor** en la Jetson (ese debe correr manualmente o vía systemd)
- El script `jetson/start_streamer.py` existe pero no se llama desde el backend

## Configuración

**Archivo**: `backend/config/control_profile.json`
- Contiene: `{"active_mode": "kid"}` (o "normal", "sport")
- La IP y puertos están en `backend/minicars_backend/settings.py`:
  - `joystick_target_host = "192.168.68.102"` (hardcodeado, pero puede sobrescribirse con env var)
  - `joystick_target_port = 5005`

**Comandos hardcodeados**:
- GStreamer pipeline está hardcodeado en `start_stream.py`
- IP de Jetson está en settings pero no se lee desde `control_profile.json`

## Comparación: car_control_logi.py vs JoystickSender

| Aspecto | car_control_logi.py | JoystickSender (backend) |
|---------|-------------------|------------------------|
| Formato mensaje | 5 campos (enteros) | 5 campos (enteros) pero bridge espera 6 |
| Throttle mapping | `map_pedal_to_throttle()` con deadzone, expo, ramp | `DrivingProfile.apply_throttle_curve()` más simple |
| Frecuencia | 100 Hz | 100 Hz (configurable) |
| Modo activo | Lee de variable global | Lee de `control_profile.json` |
| Turbo | Toggle con botón 10 | Toggle con botón 10 ✅ |
| Ejes | AXIS_STEER=0, ACCEL=1, BRAKE=2, HBRAKE=3 | Mismo ✅ |

## Resumen de Problemas

1. **PROTOCOLO**: Backend envía 5 campos, bridge espera 6 campos → mensajes rechazados
2. **LÓGICA**: Algoritmo de throttle diferente entre `car_control_logi.py` y `JoystickSender`
3. **STREAM**: Solo lanza receptor, no emisor en Jetson
4. **LOGGING**: No hay logs rotativos para debug
5. **PROCESOS DUPLICADOS**: No hay protección robusta contra procesos duplicados

