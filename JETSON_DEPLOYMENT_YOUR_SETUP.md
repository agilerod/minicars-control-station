# 🚀 Deployment en tu Jetson - Pasos Específicos

**Tu setup**:
- Host: `SKLNx.local` (en MiniCars Network)
- Usuario: `jetson-rod`
- Red actual: Con internet (para deployment)
- Red operativa: MiniCars Network (sin internet)

---

## 📡 ESTRATEGIA DE DEPLOYMENT

Como cambias entre redes, el deployment se hace en **2 fases**:

### FASE 1: Con Internet (WiFi con acceso a GitHub)
→ Clonar/actualizar código desde GitHub

### FASE 2: En MiniCars Network (sin internet)
→ Operar con código ya descargado
→ Laptop y Jetson se comunican para streaming y joystick

---

## 🎯 DEPLOYMENT INICIAL (Primera Vez)

### Paso 1: Conectar SSH (con la red que tiene internet AHORA)

```powershell
# Desde tu laptop - necesitas saber la IP en la red con internet
# Puede ser diferente a SKLNx.local

# Opción A: Si sabes la IP actual
ssh jetson-rod@192.168.X.X

# Opción B: Si el hostname funciona en esta red
ssh jetson-rod@jetson-nano.local

# Opción C: Desde el router, busca la IP de la Jetson
```

**Ejemplo para encontrar la IP**:
```powershell
# Si tienes nmap
nmap -sn 192.168.1.0/24 | findstr jetson

# O desde la Jetson (si tienes acceso físico)
# Conectar monitor y teclado, ver IP con:
ip addr show
```

---

### Paso 2: Una vez dentro de la Jetson

```bash
# Verificar que tienes internet AHORA
ping -c 3 github.com
# Debe responder

# Verificar Python y Git
python3 --version  # Debe ser 3.6+
git --version

# Si falta algo:
sudo apt update
sudo apt install -y git python3-pip
```

---

### Paso 3: Clonar el Repositorio (con internet)

```bash
cd /home/jetson-rod

# Clonar con HTTPS (más fácil, no requiere SSH keys)
git clone https://github.com/agilerod/minicars-control-station.git

# Verificar
cd minicars-control-station
ls -la
```

**Esperado**:
```
Cloning into 'minicars-control-station'...
remote: Enumerating objects: ...
Receiving objects: 100% ...
Resolving deltas: 100% ...
```

**Si pide credenciales**:
- Username: `agilerod`
- Password: Tu token de GitHub (crear en GitHub → Settings → Tokens)

---

### Paso 4: Instalar Dependencias Python (con internet)

```bash
cd /home/jetson-rod/minicars-control-station

# Instalar pyserial para el TCP-UART bridge
pip3 install -r jetson/requirements.txt

# Verificar instalación
python3 -c "import serial; print('pyserial OK')"
```

**Esperado**:
```
Successfully installed pyserial-3.5
pyserial OK
```

---

### Paso 5: Configurar Script de Deployment

```bash
# Copiar script a home
cp deploy_to_jetson.sh ~/
chmod +x ~/deploy_to_jetson.sh

# Ejecutar deployment inicial
~/deploy_to_jetson.sh
```

**Qué verás**:
```
==========================================
=== MiniCars Jetson Deployment ===
==========================================

✓ Repositorio encontrado
✓ Código actualizado correctamente  ← Funciona porque tienes internet ahora
✓ Permisos actualizados
✓ Servicios systemd sincronizados
✓ nvargus-daemon reiniciado
✓ Servicios reiniciados

Deployment completado
==========================================
```

---

### Paso 6: Verificar que Todo Está Corriendo

```bash
# Ver estado de servicios
sudo systemctl status minicars-streamer
sudo systemctl status minicars-joystick

# Ambos deben mostrar: Active: active (running)

# Ver logs
journalctl -u minicars-streamer -u minicars-joystick -f
```

**Presiona Ctrl+C para salir de los logs**

---

### Paso 7: CAMBIAR A MiniCars Network (sin internet)

Ahora que el código está descargado, puedes cambiar a MiniCars Network:

```bash
# Ver redes disponibles
sudo nmcli device wifi list

# Conectar a MiniCars Network
sudo nmcli device wifi connect "MiniCars Network" password "tupassword"

# Verificar IP en esta red
ip addr show wlan0
# Debería mostrar 192.168.68.xxx
```

**IMPORTANTE**: 
- El código ya está en disco
- Los servicios siguen corriendo
- Solo cambia la red
- SKLNx.local ahora debería funcionar desde tu laptop

---

## 🔄 ACTUALIZACIONES FUTURAS

### Cuando hagas cambios en el código:

**Desde tu laptop**:
```powershell
# Hacer cambios, commit, push
git add .
git commit -m "feat: nuevo cambio"
git push origin main
```

**En la Jetson**:

**OPCIÓN A - Con internet temporalmente**:
```bash
# 1. Cambiar a WiFi con internet
sudo nmcli device wifi connect "TuWiFiConInternet"

# 2. Actualizar código
~/deploy_to_jetson.sh
# El script hará git pull automáticamente

# 3. Volver a MiniCars Network
sudo nmcli device wifi connect "MiniCars Network"
```

**OPCIÓN B - Sin cambiar de red (modo offline)**:
```bash
# Ejecutar deployment
~/deploy_to_jetson.sh

# Verás: "⚠ No se pudo hacer git pull (posible modo offline)"
# Pero el script CONTINÚA y reinicia servicios con código local

# Para actualizar código, necesitarás internet la próxima vez
```

---

## 🎮 TESTING DESDE LAPTOP

### Una vez que Jetson esté en MiniCars Network:

```powershell
# 1. Conectar laptop a MiniCars Network

# 2. Verificar conectividad
ping SKLNx.local
# Debe responder desde 192.168.68.xxx

Test-NetConnection SKLNx.local -Port 5005
# Debe mostrar: TcpTestSucceeded : True

# 3. Iniciar backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn minicars_backend.api:app --reload

# 4. En otra terminal - desktop
cd desktop
npm run tauri:dev

# 5. En la app:
#    - Start Stream → debe verse video
#    - Start Car Control → debe conectarse a puerto 5005
#    - Mover joystick → coche responde
```

---

## 📋 CHECKLIST DE DEPLOYMENT

### Deployment Inicial (con internet)
- [ ] SSH a Jetson en red con internet
- [ ] `git clone https://github.com/agilerod/minicars-control-station.git`
- [ ] `pip3 install -r jetson/requirements.txt`
- [ ] `cp deploy_to_jetson.sh ~/ && chmod +x ~/deploy_to_jetson.sh`
- [ ] `~/deploy_to_jetson.sh`
- [ ] Verificar servicios: `sudo systemctl status minicars-*`

### Cambiar a MiniCars Network
- [ ] `sudo nmcli device wifi connect "MiniCars Network"`
- [ ] Verificar IP: `ip addr show wlan0`
- [ ] Verificar servicios siguen corriendo
- [ ] Desde laptop: `ping SKLNx.local`

### Testing
- [ ] Laptop en MiniCars Network
- [ ] Backend corriendo
- [ ] Desktop app corriendo
- [ ] Start Stream funciona
- [ ] Start Car Control funciona
- [ ] Joystick controla el coche

---

## 🎯 COMANDOS LISTOS PARA COPIAR

### Deployment completo (con internet):

```bash
cd /home/jetson-rod
git clone https://github.com/agilerod/minicars-control-station.git
cd minicars-control-station
pip3 install -r jetson/requirements.txt
cp deploy_to_jetson.sh ~/
chmod +x ~/deploy_to_jetson.sh
~/deploy_to_jetson.sh
```

### Cambiar a MiniCars Network:

```bash
sudo nmcli device wifi connect "MiniCars Network" password "TU_PASSWORD_AQUI"
```

### Verificar todo OK:

```bash
sudo systemctl status minicars-streamer minicars-joystick
journalctl -u minicars-joystick -u minicars-streamer -f
```

---

**¿Necesitas ayuda con algún paso específico o ya puedes proceder?**

También puedo:
- Darte comandos para verificar si el repo ya existe
- Ayudarte a encontrar la IP de la Jetson
- Debuggear si algo falla durante el deployment

