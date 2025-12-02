# 🎮 MiniCars Joystick Control - Deployment Guide

**Sistema**: Laptop → Jetson → Arduino  
**Estado**: ✅ LISTO PARA DEPLOYMENT  
**Última actualización**: 2025-12-02

---

## 🚀 Quick Start (5 minutos)

### 1. Laptop - Instalar dependencias

```powershell
cd backend
pip install -r requirements.txt  # Instala pygame y otras dependencias
```

### 2. Laptop - Configurar .env (opcional)

```powershell
cd backend
copy .env.example .env
# Editar .env solo si Jetson NO usa hostname SKLNx.local
```

### 3. Jetson - Deploy

```bash
# Conectar por SSH
ssh jetson-rod@<JETSON_IP>

# Ejecutar deployment
~/deploy_to_jetson.sh

# Instalar pyserial
pip3 install -r /home/jetson-rod/minicars-control-station/jetson/requirements.txt
```

### 4. Verificar servicios en Jetson

```bash
# Ambos servicios deben estar running
sudo systemctl status minicars-joystick
sudo systemctl status minicars-streamer
```

### 5. Laptop - Iniciar sistema

```powershell
# Terminal 1: Backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn minicars_backend.api:app --reload

# Terminal 2: Desktop
cd desktop
npm run tauri:dev
```

### 6. Probar en Desktop App

1. Conectar joystick vía USB
2. Seleccionar modo (Kid/Normal/Sport)
3. Presionar "Start Car Control"
4. ✅ Mover joystick → coche debe responder

---

## 📋 Checklist Pre-Deployment

### Laptop
- [ ] Python 3.10+ instalado
- [ ] Node.js 18+ instalado
- [ ] GStreamer instalado (para video)
- [ ] Joystick conectado vía USB
- [ ] En MiniCars Network (WiFi)

### Jetson
- [ ] Usuario jetson-rod existe
- [ ] Git configurado (SSH keys para GitHub)
- [ ] pyserial instalado
- [ ] Arduino conectado a /dev/ttyTHS1
- [ ] En MiniCars Network (WiFi)

### Red
- [ ] Jetson y Laptop en misma red
- [ ] SKLNx.local resuelve desde Jetson: `ping SKLNx.local`
- [ ] Puerto 5005 abierto (firewall)

---

## 🎯 Modos de Conducción

### Kid Mode (Seguro)
- **Throttle**: Máximo 40%, curva suave (x²)
- **Servo**: ±60% del rango total
- **Uso**: Niños, aprendizaje, áreas cerradas

### Normal Mode (Equilibrado)
- **Throttle**: Máximo 75%, casi lineal
- **Servo**: ±85% del rango total
- **Uso**: Conducción general, exteriores

### Sport Mode (Performance)
- **Throttle**: 100%, respuesta directa
- **Servo**: ±100%, giros completos
- **Uso**: Expertos, pistas abiertas

---

## 🛡️ Seguridad (Failsafe)

El sistema tiene **3 capas de seguridad**:

### Capa 1: Sender (Laptop)
- Al presionar "Stop Car Control" → envía comando de freno total

### Capa 2: Watchdog (Jetson)
- Si no recibe datos por > 150ms → activa failsafe automático
- Failsafe: servo centrado, throttle 0, brake 100%

### Capa 3: Reconexión
- Sender reintenta cada 2s si pierde conexión
- Al reconectar, estado seguro primero

**Resultado:** Coche SIEMPRE se detiene de forma segura si se pierde conexión.

---

## 📡 Protocolo de Comunicación

### TCP (Laptop → Jetson)
```
formato: servo,throttle,brake,handbrake,turbo,mode\n
ejemplo: 0.250,0.650,0.000,0.000,0.000,normal\n
```

### UART (Jetson → Arduino)
```
formato: servo_angle,accel_pct,brake_pct,hbrake_flag,turbo_flag\n
ejemplo: 112,65,0,0,0\n
```

**Conversión:**
- servo: -1.0..1.0 → 0..180°
- throttle: 0.0..1.0 → 0..100%
- brake: 0.0..1.0 → 0..100%
- flags: > 0.5 → 1, else 0

---

## 🔍 Troubleshooting

### "No joystick detected"
```powershell
python -c "import pygame; pygame.init(); pygame.joystick.init(); print(pygame.joystick.get_count())"
```
- Si devuelve 0: conectar joystick y reintentar
- Verificar en Device Manager (Windows)

### "Failed to connect to SKLNx.local"
```powershell
ping SKLNx.local
Test-NetConnection SKLNx.local -Port 5005
```
- Verificar que ambos están en MiniCars Network
- Como alternativa, usar IP en backend/.env

### "Watchdog activa constantemente"
```bash
# En Jetson - aumentar timeout
sudo systemctl edit minicars-joystick
# Agregar:
# Environment="MINICARS_WATCHDOG_MS=300"
sudo systemctl restart minicars-joystick
```

### "pygame not installed"
```powershell
cd backend
pip install pygame
```

---

## 📊 Logs y Monitoring

### Ver logs en tiempo real

**Jetson:**
```bash
# Solo joystick
journalctl -u minicars-joystick -f

# Solo streaming
journalctl -u minicars-streamer -f

# Ambos
journalctl -u minicars-joystick -u minicars-streamer -f
```

**Laptop:**
- Stdout de uvicorn muestra logs de JoystickSender
- Prefijo: `[joystick-sender]`

### Niveles de log

**Cambiar a DEBUG temporalmente:**
```bash
sudo systemctl set-environment MINICARS_LOG_LEVEL=DEBUG
sudo systemctl restart minicars-joystick
```

**Volver a INFO:**
```bash
sudo systemctl unset-environment MINICARS_LOG_LEVEL
sudo systemctl restart minicars-joystick
```

---

## 🔄 Workflow de Desarrollo

### 1. Hacer cambios en código
```powershell
# Editar archivos en backend/minicars_backend/joystick/ o jetson/
```

### 2. Commit y push
```powershell
git add .
git commit -m "fix: ajuste de parámetros de modo kid"
git push origin main
```

### 3. Deploy a Jetson
```bash
# SSH a Jetson
ssh jetson-rod@<JETSON_IP>

# Deploy
~/deploy_to_jetson.sh
```

### 4. Restart backend en laptop
```powershell
# Ctrl+C en terminal de uvicorn, luego:
uvicorn minicars_backend.api:app --reload
```

---

## 📞 Support

**Documentación:**
- Design: `docs/joystick_control_notes.md`
- Testing: `docs/testing_joystick.md`
- Audit: `docs/JOYSTICK_AUDIT_REPORT.md`
- Status: `docs/JOYSTICK_SUBSYSTEM_STATUS.md`

**Issues comunes:** Ver sección Troubleshooting arriba

**Sistema funcionando:** Sin cambios necesarios

---

✅ **Sistema listo para producción**  
🎮 **Happy driving!**

