# 🚀 MiniCars Jetson Deployment - Guía Paso a Paso

**Fecha**: 2025-12-02  
**Repositorio**: https://github.com/agilerod/minicars-control-station.git

---

## 📋 Pre-requisitos

Antes de empezar, verifica que tengas:

### En tu Laptop (Windows)
- [ ] IP de la Jetson (o hostname)
- [ ] Usuario: `jetson-rod`
- [ ] Contraseña o SSH key configurada
- [ ] Conexión a la misma red que la Jetson

### En la Jetson
- [ ] JetPack instalado (con Python 3.6+)
- [ ] Usuario `jetson-rod` existe
- [ ] sudo privileges configurados

---

## 🔍 PASO 0: Identificar tu situación

**¿Es la primera vez que deployeas en esta Jetson?**

### Opción A: Primera vez (repo NO existe)
→ Ir a **DEPLOYMENT INICIAL** (Sección 1)

### Opción B: Ya tenías código viejo
→ Ir a **ACTUALIZACIÓN DESDE CÓDIGO VIEJO** (Sección 2)

### Opción C: Ya clonaste el repo antes
→ Ir a **ACTUALIZACIÓN SIMPLE** (Sección 3)

---

## 1️⃣ DEPLOYMENT INICIAL (Primera Vez)

### Paso 1.1: Conectar a Jetson por SSH

Desde PowerShell en tu laptop:

```powershell
# Reemplaza <JETSON_IP> con la IP real (ej: 192.168.68.124)
ssh jetson-rod@<JETSON_IP>
```

**Ejemplo**:
```powershell
ssh jetson-rod@192.168.68.124
# O si usas hostname:
ssh jetson-rod@jetson-nano.local
```

**¿Qué esperar?**
- Pide contraseña
- Te muestra prompt: `jetson-rod@jetson-nano:~$`

---

### Paso 1.2: Verificar Python y Git

Una vez dentro de la Jetson:

```bash
# Verificar Python
python3 --version
# Debe mostrar: Python 3.6.x o superior

# Verificar Git
git --version
# Debe mostrar: git version 2.x.x

# Verificar pip
pip3 --version
# Debe mostrar: pip 9.x.x o superior
```

**Si algo falta**, instalar:
```bash
sudo apt update
sudo apt install -y git python3-pip
```

---

### Paso 1.3: Clonar el Repositorio

```bash
cd /home/jetson-rod
git clone https://github.com/agilerod/minicars-control-station.git
```

**¿Qué esperar?**
```
Cloning into 'minicars-control-station'...
remote: Enumerating objects: ...
remote: Counting objects: 100% ...
Receiving objects: 100% ...
Resolving deltas: 100% ...
```

**Si pide credenciales**:
- Usuario: `agilerod`
- Token: Crear en GitHub → Settings → Developer settings → Personal access tokens

**Alternativa con SSH** (si tienes keys configuradas):
```bash
git clone git@github.com:agilerod/minicars-control-station.git
```

---

### Paso 1.4: Instalar Dependencias Python

```bash
cd minicars-control-station
pip3 install -r jetson/requirements.txt
```

**Esperado**:
```
Successfully installed pyserial-3.5
```

---

### Paso 1.5: Copiar Script de Deployment

```bash
# Copiar a home directory
cp deploy_to_jetson.sh ~/
chmod +x ~/deploy_to_jetson.sh
```

**Verificar**:
```bash
ls -lh ~/deploy_to_jetson.sh
# Debe mostrar: -rwxr-xr-x ... deploy_to_jetson.sh
```

---

### Paso 1.6: Ejecutar Deployment Inicial

```bash
~/deploy_to_jetson.sh
```

**Qué hace el script:**
1. ✅ Verifica que el repo existe
2. ⚠️ Intenta `git pull` (puede fallar si no hay internet, OK)
3. ✅ Actualiza permisos de scripts
4. ✅ Copia services a systemd
5. ✅ Reinicia nvargus-daemon
6. ✅ Reinicia ambos servicios (streamer + joystick)
7. ✅ Muestra estado final

**Salida esperada**:
```
==========================================
=== MiniCars Jetson Deployment ===
==========================================

✓ Repositorio encontrado en /home/jetson-rod/minicars-control-station
✓ Código actualizado correctamente (o: ⚠ modo offline)
✓ Permisos actualizados
✓ Servicio systemd sincronizado
✓ nvargus-daemon reiniciado
✓ Servicio minicars-streamer reiniciado
✓ Servicio minicars-joystick reiniciado

Estado de los servicios:
--- Servicio Streamer (GStreamer) ---
● minicars-streamer.service - MiniCars Jetson GStreamer sender
   Active: active (running)

--- Servicio Joystick (TCP-UART Bridge) ---
● minicars-joystick.service - MiniCars Jetson TCP-to-UART joystick bridge
   Active: active (running)

==========================================
Deployment completado
==========================================
```

---

### Paso 1.7: Verificar Servicios

```bash
# Ver estado
sudo systemctl status minicars-streamer
sudo systemctl status minicars-joystick

# Ver logs en tiempo real
journalctl -u minicars-streamer -u minicars-joystick -f
```

**Logs esperados para streamer**:
```
[minicars-jetson] INFO: Resolved SKLNx.local to 192.168.68.xxx
[minicars-jetson] INFO: Restarting nvargus-daemon...
[minicars-jetson] INFO: nvargus-daemon restarted successfully.
[minicars-jetson] INFO: Starting GStreamer pipeline...
```

**Logs esperados para joystick**:
```
[minicars-joystick-bridge] INFO: MiniCars TCP-UART Bridge Starting
[minicars-joystick-bridge] INFO: TCP: 0.0.0.0:5005
[minicars-joystick-bridge] INFO: UART: /dev/ttyTHS1 @ 115200 baud
[minicars-joystick-bridge] INFO: UART opened
[minicars-joystick-bridge] INFO: TCP server listening on 0.0.0.0:5005
[minicars-joystick-bridge] INFO: Watchdog started (timeout: 150ms)
[minicars-joystick-bridge] INFO: Waiting for client connection...
```

---

## 2️⃣ ACTUALIZACIÓN DESDE CÓDIGO VIEJO

### Si ya tenías código en otra ubicación

```bash
# Hacer backup del código viejo
cd /home/jetson-rod
mv minicars-jetson minicars-jetson-backup  # Si existe

# Clonar repo nuevo
git clone https://github.com/agilerod/minicars-control-station.git

# Copiar configuraciones personalizadas si las tenías
# (por ejemplo, si editaste IPs o puertos)

# Continuar con Paso 1.4 en adelante
```

---

## 3️⃣ ACTUALIZACIÓN SIMPLE (Repo Ya Existe)

### Si ya clonaste el repo antes:

```bash
cd /home/jetson-rod/minicars-control-station

# Actualizar código
git pull origin main

# O usar el script (recomendado)
~/deploy_to_jetson.sh
```

---

## 🔥 TROUBLESHOOTING

### Problema: "Could not resolve host: github.com"

**Causa**: Jetson sin internet

**Solución A - Usar el script (modo offline)**:
```bash
~/deploy_to_jetson.sh
# El script ahora CONTINÚA aunque git pull falle
# Usará el código que ya tienes en disco
```

**Solución B - Conectar a red con internet temporalmente**:
```bash
# Cambiar a WiFi con internet
sudo nmcli device wifi list
sudo nmcli device wifi connect "TuWiFi" password "tupassword"

# Hacer pull
cd /home/jetson-rod/minicars-control-station
git pull origin main

# Volver a MiniCars Network si lo necesitas
sudo nmcli device wifi connect "MiniCars Network" password "..."
```

---

### Problema: "Permission denied (publickey)"

**Solución - Usar HTTPS en lugar de SSH**:

```bash
cd /home/jetson-rod/minicars-control-station
git remote set-url origin https://github.com/agilerod/minicars-control-station.git
git pull origin main
```

---

### Problema: "Failed to open UART /dev/ttyTHS1"

**Verificar Arduino conectado**:
```bash
ls -l /dev/ttyTHS1
# Debe existir

# Agregar usuario a grupo dialout
sudo usermod -a -G dialout jetson-rod

# Logout y login, o:
sudo reboot
```

---

### Problema: "nvargus-daemon restart failed"

**Es normal si no tienes cámara CSI conectada**

El script continúa de todas formas. Si no usas cámara:
```bash
# Deshabilitar nvargus-daemon restart editando deploy_to_jetson.sh
# O ignorar el warning
```

---

### Problema: "service not found"

**Primera vez**, los services no existen hasta que corras el deployment:

```bash
~/deploy_to_jetson.sh
# Esto los instala automáticamente
```

---

## ✅ VERIFICACIÓN POST-DEPLOYMENT

### Check 1: Servicios corriendo

```bash
sudo systemctl status minicars-streamer
sudo systemctl status minicars-joystick
```

Ambos deben mostrar: `Active: active (running)`

### Check 2: Logs sin errores

```bash
journalctl -u minicars-joystick -n 50
journalctl -u minicars-streamer -n 50
```

No debe haber líneas con `ERROR` o `CRITICAL`

### Check 3: Puerto TCP abierto

```bash
sudo netstat -tlnp | grep 5005
```

Debe mostrar:
```
tcp  0  0  0.0.0.0:5005  0.0.0.0:*  LISTEN  12345/python3
```

### Check 4: Hostname resolution

```bash
ping SKLNx.local
```

Debe resolver a la IP de tu laptop (solo funciona en MiniCars Network)

---

## 🎮 TESTING END-TO-END

### Desde tu Laptop:

```powershell
# 1. Iniciar backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn minicars_backend.api:app --reload

# 2. En otra terminal - iniciar desktop
cd desktop
npm run tauri:dev

# 3. En la app desktop:
#    - Presionar "Start Stream" → debería verse video de Jetson
#    - Presionar "Start Car Control" → debería conectarse a bridge
#    - Mover joystick → coche debe responder
```

### Verificar en Jetson:

```bash
# Ver logs en tiempo real
journalctl -u minicars-streamer -u minicars-joystick -f
```

**Esperado al conectar joystick**:
```
[minicars-joystick-bridge] INFO: Client connected from 192.168.68.xxx:xxxxx
[minicars-joystick-bridge] DEBUG: Sent to UART: 90,0,0,0,0
```

---

## 🆘 SI ALGO FALLA

### Logs completos:

```bash
# Últimos 100 mensajes de cada servicio
journalctl -u minicars-streamer -n 100
journalctl -u minicars-joystick -n 100

# Con timestamps
journalctl -u minicars-joystick -u minicars-streamer --since "10 minutes ago"
```

### Reiniciar servicios:

```bash
sudo systemctl restart minicars-streamer
sudo systemctl restart minicars-joystick
```

### Reinstalar servicios:

```bash
cd /home/jetson-rod/minicars-control-station
sudo cp jetson/minicars-streamer.service /etc/systemd/system/
sudo cp jetson/minicars-joystick.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable minicars-streamer minicars-joystick
sudo systemctl restart minicars-streamer minicars-joystick
```

---

## 📞 COMANDOS RÁPIDOS DE REFERENCIA

```bash
# Ver estado de servicios
sudo systemctl status minicars-streamer minicars-joystick

# Logs en tiempo real
journalctl -u minicars-joystick -f

# Reiniciar todo
~/deploy_to_jetson.sh

# Ver si puerto está abierto
sudo netstat -tlnp | grep 5005

# Test manual del bridge (sin systemd)
cd /home/jetson-rod/minicars-control-station/jetson
python3 tcp_uart_bridge.py

# Test manual del streamer (sin systemd)
python3 start_streamer.py
```

---

**Ahora dime: ¿Es la primera vez que deployeas en esta Jetson o ya tenías código antiguo?**

