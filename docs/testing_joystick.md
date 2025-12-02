# MiniCars Joystick Control - Testing Guide

## Overview

Esta guía cubre las pruebas del sistema completo de control de joystick después de las mejoras implementadas.

**Sistema**: Laptop (JoystickSender) → TCP → Jetson (Bridge) → UART → Arduino

## Prerrequisitos

### En la Laptop (Windows)

```powershell
# 1. Instalar dependencias
cd backend
pip install -r requirements.txt  # Incluye pygame

# 2. Configurar .env
copy .env.example .env
# Editar .env si es necesario (host/port de Jetson)

# 3. Levantar backend
.\.venv\Scripts\Activate.ps1
uvicorn minicars_backend.api:app --reload

# 4. En otra terminal - levantar desktop
cd desktop
npm run tauri:dev
```

### En la Jetson

```bash
# 1. Deploy
~/deploy_to_jetson.sh

# 2. Instalar pyserial
pip3 install -r /home/jetson-rod/minicars-control-station/jetson/requirements.txt

# 3. Verificar servicios
sudo systemctl status minicars-joystick
sudo systemctl status minicars-streamer
```

### Hardware
- Joystick conectado vía USB a laptop
- Arduino conectado a Jetson vía UART (/dev/ttyTHS1)
- Ambos en **MiniCars Network**

## 1. Pruebas Básicas

### 1.1. Verificar Backend

```powershell
# Health check
Invoke-RestMethod http://127.0.0.1:8000/health

# Ver perfil activo
Invoke-RestMethod http://127.0.0.1:8000/control/profile
```

**Esperado:**
```json
{
  "status": "ok",
  "service": "minicars-control-station-backend",
  ...
}

{
  "active_mode": "normal"
}
```

### 1.2. Verificar Jetson Bridge

```bash
# Ver logs
journalctl -u minicars-joystick -f
```

**Esperado:**
```
[minicars-joystick-bridge] INFO: MiniCars TCP-UART Bridge Starting
[minicars-joystick-bridge] INFO: TCP: 0.0.0.0:5005
[minicars-joystick-bridge] INFO: UART: /dev/ttyTHS1 @ 115200 baud
[minicars-joystick-bridge] INFO: Watchdog: 150ms timeout
[minicars-joystick-bridge] INFO: UART opened: /dev/ttyTHS1 @ 115200 baud
[minicars-joystick-bridge] INFO: TCP server listening on 0.0.0.0:5005
[minicars-joystick-bridge] INFO: Watchdog started (timeout: 150ms)
[minicars-joystick-bridge] INFO: Waiting for client connection...
```

## 2. Pruebas de Modos de Conducción

### 2.1. Modo Kid

```powershell
# Cambiar a modo Kid
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/control/profile -Body '{"active_mode":"kid"}' -ContentType "application/json"
```

**Desde Desktop:**
1. Seleccionar modo "Kid" en UI
2. Presionar "Start Car Control"
3. Probar acelerador

**Comportamiento esperado:**
- ✅ Aceleración MUY suave (máx 40%)
- ✅ Giros limitados (±60%)
- ✅ Respuesta progresiva (curva cuadrática)

**En logs de Jetson:**
```
[minicars-joystick-bridge] INFO: Client connected from 192.168.68.xxx:xxxxx
[minicars-joystick-bridge] DEBUG: Sent to UART: 90,0,0,0,0
```

### 2.2. Modo Normal

**Cambiar a Normal:**
- Desde UI o vía API

**Comportamiento esperado:**
- ✅ Aceleración moderada (máx 75%)
- ✅ Giros amplios (±85%)
- ✅ Respuesta casi lineal

### 2.3. Modo Sport

**Cambiar a Sport:**
- Desde UI o vía API

**Comportamiento esperado:**
- ✅ Aceleración completa (100%)
- ✅ Giros completos (±100%)
- ✅ Respuesta inmediata

## 3. Pruebas de Failsafe

### 3.1. Desconexión de cliente

**Acción:** Presionar "Stop Car Control" en desktop

**Esperado en logs de Jetson:**
```
[minicars-joystick-bridge] INFO: Client disconnected
[minicars-joystick-bridge] WARNING: Failsafe activated - sending safe command to Arduino
[minicars-joystick-bridge] INFO: Client connection closed
[minicars-joystick-bridge] INFO: Waiting for client connection...
```

**Verificar Arduino:**
- Servo → 90° (centrado)
- Throttle → 0
- Brake → 100%

### 3.2. Pérdida de red

**Acción:** Desconectar WiFi de laptop

**Esperado:**
- Watchdog detecta timeout en < 200ms
- Failsafe activado automáticamente
- Arduino en estado seguro

### 3.3. Crash de desktop app

**Acción:** Cerrar app desktop abruptamente (Alt+F4)

**Esperado:**
- Mismo comportamiento que desconexión
- Sistema NO se queda "colgado"
- Puede reconectar al reabrir app

## 4. Pruebas de Reconexión

### 4.1. Reconexión automática

**Secuencia:**
1. Start Car Control (conecta)
2. Reiniciar servicio en Jetson: `sudo systemctl restart minicars-joystick`
3. Observar en laptop

**Esperado:**
- Sender detecta conexión perdida
- Logs: "Connection lost. Reconnecting..."
- Reconecta automáticamente cada 2s
- Al volver servicio, conexión se reestablece

### 4.2. Cambio de modo en caliente

**Secuencia:**
1. Start Car Control en modo Normal
2. SIN detener, cambiar a Kid
3. Observar comportamiento del vehículo

**Esperado:**
- Cambio inmediato de comportamiento
- No requiere reiniciar control
- Logs muestran nuevo modo en mensajes TCP

## 5. Pruebas de Robustez

### 5.1. Mensajes inválidos

**Simular mensaje malformado:**
```bash
# En Jetson, con bridge corriendo:
echo "malformed,data" | nc localhost 5005
```

**Esperado:**
```
[minicars-joystick-bridge] WARNING: Invalid message: malformed,data
```

- Bridge NO crashea
- Mensaje ignorado
- Siguiente mensaje válido procesa correctamente

### 5.2. UART desconectado

**Acción:** Desconectar Arduino físicamente

**Esperado:**
```
[minicars-joystick-bridge] ERROR: Failed to write to UART: ...
```

- Bridge cierra conexión TCP limpiamente
- Al reconectar Arduino y reiniciar servicio, todo funciona

### 5.3. Sin joystick

**Acción:** Start Car Control sin joystick conectado

**Esperado:**
```json
{
  "status": "error",
  "message": "Failed to start: No joystick detected"
}
```

- Backend NO crashea
- Mensaje claro al usuario
- Puede conectar joystick y reintentar

## 6. Pruebas de Performance

### 6.1. Latencia end-to-end

**Método:**
- Mover joystick bruscamente
- Observar respuesta del coche
- Medir con cronómetro

**Target:** < 100ms de latencia perceptible

### 6.2. Frecuencia de envío

**Verificar en logs DEBUG:**
```bash
# En Jetson, activar DEBUG:
sudo systemctl set-environment MINICARS_LOG_LEVEL=DEBUG
sudo systemctl restart minicars-joystick
journalctl -u minicars-joystick -f
```

**Esperado:**
- ~20 mensajes por segundo
- Timestamps consistentes
- No hay gaps > 100ms

### 6.3. Watchdog timing

**Test:**
1. Start control
2. Pausar/suspender laptop (Sleep)
3. Esperar 1 segundo
4. Despertar laptop

**Esperado:**
- Failsafe activado en Jetson durante sleep
- Reconexión automática al despertar

## 7. Comandos Útiles

### Jetson

```bash
# Ver ambos servicios
journalctl -u minicars-joystick -u minicars-streamer -f

# Reiniciar joystick
sudo systemctl restart minicars-joystick

# Ver configuración activa
sudo systemctl show minicars-joystick --property=Environment

# Cambiar log level temporalmente
sudo systemctl set-environment MINICARS_LOG_LEVEL=DEBUG
sudo systemctl restart minicars-joystick

# Ver puerto TCP
sudo netstat -tlnp | grep 5005

# Test de conectividad
nc -v SKLNx.local 5005
```

### Laptop

```powershell
# Start control vía API
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/actions/start_car_control

# Stop control
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/actions/stop_car_control

# Cambiar modo
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/control/profile -Body '{"active_mode":"sport"}' -ContentType "application/json"

# Test de conectividad a Jetson
Test-NetConnection SKLNx.local -Port 5005
```

## 8. Troubleshooting

### Problema: "pygame not installed"

```powershell
cd backend
pip install pygame
```

### Problema: "Failed to connect to SKLNx.local:5005"

**Verificar:**
```powershell
# Ping a Jetson
ping SKLNx.local

# Test port
Test-NetConnection SKLNx.local -Port 5005
```

**Soluciones:**
- Verificar que ambos están en MiniCars Network
- Verificar que servicio minicars-joystick está corriendo
- Usar IP en lugar de hostname (editar .env)

### Problema: "No joystick detected"

**Verificar:**
```powershell
python -c "import pygame; pygame.init(); pygame.joystick.init(); print(f'Joysticks: {pygame.joystick.get_count()}')"
```

**Soluciones:**
- Conectar joystick vía USB
- Verificar en Device Manager
- Reiniciar joystick

### Problema: Watchdog activa constantemente

**Causas:**
- Latencia de red muy alta
- Sender no enviando a 20Hz

**Soluciones:**
- Aumentar `MINICARS_WATCHDOG_MS` en service
- Verificar latencia: `ping SKLNx.local`
- Ver logs de sender para errores

### Problema: Arduino no responde

**Verificar en Jetson:**
```bash
ls -l /dev/ttyTHS1
# Debe existir y tener permisos

# Test manual
echo "90,0,0,0,0" > /dev/ttyTHS1
```

**Soluciones:**
- Verificar conexión física
- Agregar usuario a grupo: `sudo usermod -a -G dialout jetson-rod`
- Verificar baudrate en Arduino sketch (115200)

## 9. Checklist de Testing Completo

### Pre-deployment
- [ ] Backend inicia sin errores
- [ ] Desktop app compila y abre
- [ ] Joystick detectado
- [ ] Jetson alcanzable (ping)

### Deployment
- [ ] `deploy_to_jetson.sh` ejecuta sin errores
- [ ] Ambos servicios running
- [ ] Logs limpios (sin errors)

### Functional Testing
- [ ] Start/Stop car control funciona
- [ ] Modo Kid: respuesta limitada
- [ ] Modo Normal: respuesta moderada
- [ ] Modo Sport: respuesta completa
- [ ] Cambio de modo en caliente funciona
- [ ] Turbo toggle funciona

### Safety Testing
- [ ] Failsafe activa al desconectar
- [ ] Watchdog funciona (<200ms)
- [ ] Reconexión automática funciona
- [ ] Mensajes inválidos ignorados (no crash)

### Performance
- [ ] Latencia < 100ms perceptible
- [ ] Frecuencia ~20 Hz
- [ ] Sin drops en red estable

### Integration
- [ ] GStreamer + Joystick coexisten sin problemas
- [ ] Ambos servicios reinician correctamente
- [ ] UI refleja estado correcto

## 10. Métricas de Éxito

✅ **Sistema Funcional:**
- Latencia total < 100ms
- Failsafe < 200ms
- Uptime > 99% en 1 hora

✅ **Usuario:**
- Cambio de modo claro y efectivo
- Errores mostrados de forma útil
- No require comandos manuales

✅ **Mantenibilidad:**
- Logs informativos
- Configuración vía .env
- Deployment en 1 comando

## 11. Próximos Pasos

Después del testing exitoso:
1. Ajustar parámetros de modos si necesario
2. Documentar edge cases encontrados
3. Considerar tests automatizados (pytest)
4. Optimizar performance si se detectan issues

## Referencias

- **Audit**: `docs/JOYSTICK_AUDIT_REPORT.md`
- **Design**: `docs/joystick_control_notes.md`
- **Code**: `backend/minicars_backend/joystick/`
- **Bridge**: `jetson/tcp_uart_bridge.py`
