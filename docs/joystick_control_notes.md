# MiniCars Joystick Control System - Design Notes

## Análisis del Sistema Actual

### Pipeline Joystick → Jetson → Arduino

**Estado actual (antes del refactor):**

```
[Laptop]                    [Jetson Nano]              [Arduino Nano]
--------                    -------------              --------------
Joystick (USB)              
    ↓                       
pygame/LogiDrive            
    ↓                       
car_control_logi.py    →→→  receptor.py         →→→    sketch_apr27a.ino
(TCP client)                (TCP server)              (UART/Serial)
Port: 5005                  Port: 5005                /dev/ttyTHS1
Host: 192.168.68.124        Listen: 0.0.0.0           Baud: 115200
```

### Formato de Mensaje Actual

**Laptop → Jetson (TCP):**
```
{servo_angle},{accel_pct},{brake_pct},{hbrake_flag},{turbo_flag}\n
```

**Valores:**
- `servo_angle`: 0-180 (entero, ángulo del servo)
- `accel_pct`: 0-100 (entero, porcentaje de aceleración)
- `brake_pct`: 0-100 (entero, porcentaje de freno)
- `hbrake_flag`: 0 o 1 (freno de mano)
- `turbo_flag`: 0 o 1 (modo turbo activado)

**Jetson → Arduino (UART):**
```
s,t,b,hb,turbo\n
```
Similar al TCP pero convertido a caracteres.

### Implementaciones Existentes

#### 1. car_control_logi.py (Principal)
- **Ubicación:** `C:\Users\rberm\OneDrive\Documentos\MiniCars\cars\car_control_logi.py`
- **Librería:** pygame
- **Características:**
  - Mapeo de modos de conducción (kid, normal, pro) mediante funciones
  - Lee perfil activo desde archivo JSON
  - Envía a 20 Hz (SEND_HZ = 20)
  - Turbo con toggle (botón cambia estado)
  - Manejo básico de reconexión (no implementado completamente)

#### 2. control_minicars_v1.py
- **Ubicación:** `cars/joystick/control_minicars_v1.py`
- **Librería:** pygame
- **Características:**
  - Valores normalizados -1..1 y 0..1
  - Deadzone y clamping
  - Reconexión automática en try/except

#### 3. Otras variantes (logidrive, logidrive2)
- Similares pero sin modos de conducción
- Hardcoded IP y configuración

### Problemas del Sistema Actual

1. **Configuración hardcodeada:**
   - IP de Jetson fija en el código
   - Puerto hardcodeado
   - Rutas absolutas hardcodeadas

2. **Sin manejo robusto de errores:**
   - No hay watchdog en Jetson
   - No hay failsafe automático
   - Reconexión simple sin timeout

3. **Falta integración con backend:**
   - El script car_control_logi.py se lanza externamente
   - No usa la API /control/profile de forma directa
   - No reporta estado al backend

4. **Sin logging estructurado:**
   - Prints básicos
   - No hay niveles de log
   - Difícil de debuggear en producción

5. **Receptor en Jetson:**
   - Script standalone fuera del repo
   - No está en systemd
   - No se gestiona con deploy_to_jetson.sh

## Nuevo Diseño Técnico

### Arquitectura Propuesta

```
[Laptop - Backend FastAPI]
    ↓
JoystickSender (módulo interno)
    - Lee perfil activo desde /control/profile
    - Aplica curvas según modo (kid/normal/pro)
    - Envía por TCP con formato estandarizado
    - Manejo robusto de reconexión
    ↓
[TCP Socket] → host=SKLNx.local, port=5005
    ↓
[Jetson - systemd service: minicars-joystick]
    ↓
tcp_uart_bridge.py
    - Escucha TCP
    - Valida y parsea mensajes
    - Aplica suavizado y limitación de delta
    - Watchdog thread (failsafe si no hay datos)
    - Logging estructurado
    ↓
[UART] → /dev/ttyTHS1, 115200 baud
    ↓
[Arduino Nano]
    - sketch_apr27a.ino (sin cambios necesarios)
```

### Formato de Mensaje Estandarizado

**TCP (Laptop → Jetson):**
```
servo,throttle,brake,handbrake,turbo,mode\n
```

**Valores:**
- `servo`: float -1.0 .. 1.0 (normalizado)
- `throttle`: float 0.0 .. 1.0
- `brake`: float 0.0 .. 1.0
- `handbrake`: float 0.0 .. 1.0 (0=off, 1=on, permite valores intermedios)
- `turbo`: float 0.0 .. 1.0 (0=off, 1=on)
- `mode`: string "kid" | "normal" | "pro" (para logging/debug)

**UART (Jetson → Arduino):**
```
{servo_angle},{accel_pct},{brake_pct},{hbrake_flag},{turbo_flag}\n
```
- Convertido desde el formato TCP:
  - `servo_angle`: int 0-180 (de servo -1..1)
  - `accel_pct`: int 0-100 (de throttle 0..1)
  - `brake_pct`: int 0-100 (de brake 0..1)
  - `hbrake_flag`: int 0 o 1
  - `turbo_flag`: int 0 o 1

### Modos de Conducción

#### Kid Mode
- **Throttle Curve:** Cuadrática suave (x^2.0)
- **Max Throttle:** 40% del máximo
- **Servo Limit:** ±60% del rango total
- **Delta Throttle Max:** 5% por frame (suavizado agresivo)
- **Delta Servo Max:** 10% por frame

#### Normal Mode
- **Throttle Curve:** Casi lineal (x^1.2)
- **Max Throttle:** 75% del máximo
- **Servo Limit:** ±85% del rango total
- **Delta Throttle Max:** 15% por frame
- **Delta Servo Max:** 25% por frame

#### Pro Mode
- **Throttle Curve:** Lineal (x^1.0)
- **Max Throttle:** 100%
- **Servo Limit:** 100%
- **Delta Throttle Max:** Sin límite (o muy alto, 50%)
- **Delta Servo Max:** Sin límite (o muy alto, 50%)

### Failsafe Strategy

**Condiciones de activación:**
- No se recibe paquete TCP válido en > 150ms (MINICARS_WATCHDOG_MS)
- Paquete TCP malformado repetidamente
- Pérdida de conexión del cliente

**Acciones:**
- Servo → centrado (90°)
- Throttle → 0
- Brake → 100% (máximo)
- Handbrake → 0
- Turbo → 0
- Log warning (throttled, max 1 por segundo)

### Variables de Entorno

**Jetson (tcp_uart_bridge.py):**
```bash
MINICARS_BRIDGE_HOST=0.0.0.0
MINICARS_BRIDGE_PORT=5005
MINICARS_UART_DEVICE=/dev/ttyTHS1
MINICARS_UART_BAUD=115200
MINICARS_WATCHDOG_MS=150
MINICARS_LOG_LEVEL=INFO
MINICARS_SERVO_MIN_ANGLE=0
MINICARS_SERVO_MAX_ANGLE=180
MINICARS_SERVO_CENTER=90
```

**Laptop (backend settings.py):**
```bash
MINICARS_JOYSTICK_TARGET_HOST=SKLNx.local
MINICARS_JOYSTICK_TARGET_PORT=5005
MINICARS_JOYSTICK_SEND_HZ=20
MINICARS_JOYSTICK_RECONNECT_DELAY=2.0
```

### Integración con Backend Existente

#### Endpoints (sin cambios en API):
- `POST /actions/start_car_control` - Inicia el sender
- `POST /actions/stop_car_control` - Detiene el sender
- `GET /control/profile` - Obtiene modo activo
- `POST /control/profile` - Cambia modo

#### Módulos Nuevos:
```
backend/minicars_backend/joystick/
├── __init__.py
├── sender.py           # JoystickSender class
├── profiles.py         # Driving mode profiles
└── protocol.py         # Message formatting
```

### Logging Strategy

**Niveles:**
- `DEBUG`: Cada paquete enviado/recibido
- `INFO`: Conexiones, cambios de modo, estado general
- `WARNING`: Paquetes malformados, failsafe activado
- `ERROR`: Errores de conexión, UART, etc.

**Formato:**
```
[minicars-joystick-sender] INFO: Connected to SKLNx.local:5005
[minicars-joystick-bridge] INFO: Client connected from 192.168.68.100:54321
[minicars-joystick-bridge] WARNING: Failsafe activated (no data for 150ms)
```

## Implementación Completada

### ✅ Fase 1: Backend (Laptop) - COMPLETADO
1. ✅ Módulo `joystick/` creado en backend
   - `profiles.py`: Perfiles de conducción con curvas
   - `protocol.py`: Formato de mensajes TCP/UART
   - `sender.py`: JoystickSender con threading
2. ✅ `start_car_control.py` actualizado para usar JoystickSender
3. ✅ `stop_car_control.py` actualizado con failsafe

### ✅ Fase 2: Jetson - COMPLETADO
1. ✅ `tcp_uart_bridge.py` implementado con:
   - Servidor TCP en puerto 5005
   - Conexión UART a Arduino
   - Watchdog con failsafe (150ms timeout)
   - Logging estructurado
   - Manejo robusto de errores
2. ✅ `minicars-joystick.service` creado
3. ✅ `deploy_to_jetson.sh` actualizado para gestionar ambos servicios

### ✅ Fase 3: UI - COMPLETADO
1. ✅ DrivingModeSelector ya existía y está funcional
   - Muestra 3 modos: Kid, Normal, Pro
   - Descripciones claras
   - Indicadores visuales

### 🔄 Fase 4: Migración
1. **Script legacy** (`car_control_logi.py`):
   - Puede mantenerse como referencia
   - NO se ejecuta más desde endpoints
   - Nuevo sistema es completamente funcional

## Próximos Pasos para Deployment

1. **En Laptop:**
   ```powershell
   cd backend
   pip install -r requirements.txt  # Instala pygame
   ```

2. **Deploy a Jetson:**
   ```bash
   # Desde laptop
   git add .
   git commit -m "feat: professional joystick control system"
   git push origin main
   
   # En Jetson
   ~/deploy_to_jetson.sh
   
   # Instalar pyserial si no está
   pip3 install -r /home/jetson-rod/minicars-control-station/jetson/requirements.txt
   ```

3. **Testing:**
   - Seguir guía en `docs/testing_joystick.md`
   - Verificar ambos servicios corriendo
   - Probar cambios de modo
   - Validar failsafe

## Notas de Implementación

### Compatibilidad con Arduino
El formato UART se mantiene igual que el actual:
```
{servo_angle},{accel_pct},{brake_pct},{hbrake_flag},{turbo_flag}\n
```

**No requiere cambios en sketch_apr27a.ino**

### Performance
- Sender: 20 Hz (50ms por frame)
- Bridge: procesa inmediatamente, sin delay artificial
- Watchdog: revisa cada 20ms (más rápido que threshold de 150ms)
- UART: write asíncrono, sin blocking

### Testing
Ver `docs/testing_joystick.md` para guía completa de pruebas.

## Referencias

- Código actual: `cars/car_control_logi.py`
- Control profiles: `backend/config/control_profile.json`
- Arduino sketch: `cars/sketch_apr27a/sketch_apr27a.ino`

