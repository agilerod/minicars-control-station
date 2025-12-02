# MiniCars Jetson Nano Streamer

This directory contains the Jetson-side scripts and configuration for streaming video from the Jetson Nano camera to the control station.

## Files

- `start_streamer.py` - Python script that restarts nvargus-daemon and launches the GStreamer pipeline
- `minicars-streamer.service` - systemd unit template for running the streamer as a service

## Deploying to Jetson Nano

### Prerequisites

- Jetson Nano with JetPack installed
- GStreamer and nvargus-daemon installed
- Network connectivity between Jetson and control station
- User `jetson-rod` exists on the Jetson (or adjust the service file)
- Repositorio clonado en `/home/jetson-rod/minicars-control-station`
- Acceso a Internet (para git pull)
- SSH keys configuradas para GitHub (si se usa SSH)

### Deployment Automático (Recomendado)

El repositorio incluye un script de deployment automático que actualiza el código, sincroniza servicios y reinicia todo automáticamente.

#### Primer Deploy: Copiar script desde laptop

Desde tu laptop (Windows PowerShell), copia el script de deployment a la Jetson:

```powershell
scp deploy_to_jetson.sh jetson-rod@<JETSON_IP>:/home/jetson-rod/
```

Reemplaza `<JETSON_IP>` con la IP o hostname de tu Jetson.

#### En la Jetson: Hacer el script ejecutable

SSH a la Jetson y haz el script ejecutable:

```bash
ssh jetson-rod@<JETSON_IP>
chmod +x ~/deploy_to_jetson.sh
```

#### Ejecutar deployment

Desde la laptop, puedes ejecutar el deployment remotamente:

```powershell
ssh jetson-rod@<JETSON_IP> "~/deploy_to_jetson.sh"
```

O desde la Jetson directamente:

```bash
~/deploy_to_jetson.sh
```

El script:
- ✅ Actualiza el código desde GitHub (`git pull origin main`)
- ✅ Actualiza permisos de scripts
- ✅ Sincroniza el servicio systemd
- ✅ Reinicia nvargus-daemon
- ✅ Reinicia el servicio minicars-streamer
- ✅ Muestra el estado final del servicio

### Deployment Manual (Primera vez o sin script)

Si prefieres hacer el deployment manualmente:

#### Step 1: Clonar repositorio (solo primera vez)

```bash
cd /home/jetson-rod
git clone git@github.com:tu-usuario/minicars-control-station.git
```

#### Step 2: Configurar servicio systemd

```bash
cd /home/jetson-rod/minicars-control-station
chmod +x jetson/start_streamer.py
sudo cp jetson/minicars-streamer.service /etc/systemd/system/minicars-streamer.service
sudo systemctl daemon-reload
sudo systemctl enable minicars-streamer.service
sudo systemctl start minicars-streamer.service
```

#### Step 3: Verificar el servicio

Check the service status:

```bash
sudo systemctl status minicars-streamer.service
```

View live logs:

```bash
journalctl -u minicars-streamer.service -f
```

### Actualizaciones Futuras

Para actualizar el código después del primer deployment, simplemente ejecuta:

```bash
~/deploy_to_jetson.sh
```

O manualmente:

```bash
cd /home/jetson-rod/minicars-control-station
git pull origin main
sudo systemctl restart minicars-streamer
```

### Notas Importantes sobre Redes

#### Cambio entre redes

La Jetson puede estar en cualquier red con acceso a Internet (MiniCars Network o WiFi doméstica). El script de deployment funciona en cualquier red siempre que haya Internet para `git pull`.

**Importante:**
- ✅ **Git pull funciona en cualquier red con Internet** - El deployment puede ejecutarse desde cualquier red
- ⚠️ **El streaming solo funciona cuando Jetson + Laptop están en MiniCars Network** - Para recibir video, ambos dispositivos deben estar en la misma red local
- 🔄 **Cambiar entre redes no afecta Git** - Puedes hacer deployment desde WiFi doméstica y luego cambiar a MiniCars Network para streaming

#### Configuración SSH para GitHub

Si `git pull` falla con errores de autenticación, configura SSH keys:

1. **Verificar SSH con GitHub:**
   ```bash
   ssh -T git@github.com
   ```

2. **Si no funciona, generar nueva clave SSH:**
   ```bash
   ssh-keygen -t ed25519 -C "jetson-rod@jetson"
   cat ~/.ssh/id_ed25519.pub
   ```

3. **Agregar la clave pública a GitHub:**
   - Copia el output del comando anterior
   - Ve a GitHub → Settings → SSH and GPG keys → New SSH key
   - Pega la clave pública

4. **Verificar nuevamente:**
   ```bash
   ssh -T git@github.com
   ```

#### Hostname SKLNx.local

El streaming usa el hostname `SKLNx.local` (mDNS) para encontrar la laptop. Si el streaming no funciona:

- Verifica que la laptop esté en **MiniCars Network**
- Verifica que mDNS/Bonjour esté funcionando
- Como alternativa, edita `jetson/start_streamer.py` y cambia `host=SKLNx.local` por la IP de la laptop

### Configuration

The GStreamer pipeline is configured in `start_streamer.py` with the following defaults:

- **Resolution**: 1280x720
- **Framerate**: 30 fps
- **Bitrate**: 6 Mbps
- **Target host**: `SKLNx.local` (mDNS hostname)
- **UDP port**: 5000

To change bitrate, resolution, or target host, edit the `gst_cmd` list in `start_streamer.py`.

**Note**: The sender uses `host=SKLNx.local` as configured in the GStreamer pipeline. Make sure this hostname resolves correctly on your network (mDNS/Bonjour) or change it to an IP address if needed.

### Troubleshooting

#### Deployment

- **"Error al hacer git pull"**: 
  - Verifica conexión a Internet: `ping 8.8.8.8`
  - Verifica SSH con GitHub: `ssh -T git@github.com`
  - Verifica el remoto: `git remote -v`
  - Si usas HTTPS en lugar de SSH, actualiza el remoto: `git remote set-url origin https://github.com/usuario/repo.git`

- **"El repositorio no existe"**: 
  - Clona el repositorio primero: `git clone git@github.com:usuario/minicars-control-station.git /home/jetson-rod/minicars-control-station`

#### Streaming

- **"Failed to create CaptureSession"**: The script automatically restarts nvargus-daemon to avoid this error.

- **Hostname resolution issues**: The script will log a warning if `SKLNx.local` cannot be resolved but will continue. If streaming fails:
  - Verifica que la laptop esté en **MiniCars Network**
  - Verifica mDNS: `ping SKLNx.local`
  - Como alternativa, edita `jetson/start_streamer.py` y cambia `host=SKLNx.local` por la IP de la laptop

- **Service won't start**: 
  - Check logs: `journalctl -u minicars-streamer.service -n 50`
  - Verifica que el servicio esté habilitado: `sudo systemctl enable minicars-streamer.service`
  - Verifica permisos del script: `ls -l jetson/start_streamer.py`

- **Permission errors**: 
  - Ensure the user specified in the service file has permission to run `sudo systemctl restart nvargus-daemon` without password
  - Configure via sudoers: `sudo visudo` y agregar: `jetson-rod ALL=(ALL) NOPASSWD: /bin/systemctl restart nvargus-daemon`

#### Ver logs

Para ver logs en tiempo real:

```bash
journalctl -u minicars-streamer.service -f
```

Para ver las últimas 50 líneas:

```bash
journalctl -u minicars-streamer.service -n 50
```

### Manual testing

To test the script manually without systemd:

```bash
cd /home/jetson-rod/minicars-jetson
./start_streamer.py
```

Press Ctrl+C to stop.

