# Streaming de Cámara - Autostart en Jetson

## Visión General

El sistema de streaming de cámara en la Jetson ahora usa un **supervisor Python** que:

- ✅ Monitorea conectividad hacia la control station (laptop)
- ✅ Verifica SSID de WiFi si está configurado
- ✅ Inicia/detiene el pipeline GStreamer automáticamente
- ✅ Maneja reinicios de nvargus-daemon cuando es necesario
- ✅ Gestiona errores y reintentos de forma inteligente

## Arquitectura

```
[Jetson Nano]
    ↓
systemd: minicars-streamer.service
    ↓
stream_supervisor.py
    ├── Carga config desde jetson/config/stream_config.json
    ├── Verifica conectividad (host:port)
    ├── Verifica SSID (opcional)
    └── Gestiona pipeline GStreamer
         ├── Inicia cuando host accesible
         └── Detiene cuando host no accesible
```

```
[Laptop/Control Station]
    ↓
backend/minicars_backend/commands/start_stream.py
    ↓
GStreamer receptor (udpsrc port=5000)
```

## Configuración

### Archivo de Configuración

**Ubicación**: `jetson/config/stream_config.json`

```json
{
  "control_station_host": "SKLNx.local",
  "video_port": 5000,
  "camera_device": "nvarguscamerasrc",
  "ssid": null,
  "resolution": {
    "width": 1280,
    "height": 720
  },
  "framerate": 30,
  "bitrate": 8000000,
  "flip_method": 2
}
```

### Campos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `control_station_host` | string | IP o hostname de la laptop (ej: "192.168.68.101" o "SKLNx.local") |
| `video_port` | int | Puerto UDP para video stream (default: 5000) |
| `camera_device` | string | Dispositivo de cámara (default: "nvarguscamerasrc") |
| `ssid` | string\|null | SSID de WiFi requerido (null = no verificar SSID) |
| `resolution.width` | int | Ancho de video (default: 1280) |
| `resolution.height` | int | Alto de video (default: 720) |
| `framerate` | int | FPS del video (default: 30) |
| `bitrate` | int | Bitrate en bps (default: 8000000 = 8 Mbps) |
| `flip_method` | int | Método de volteo (0=none, 2=180°, etc.) |

### Ejemplos de Configuración

#### Solo iniciar cuando esté en MiniCars Network (por SSID)

```json
{
  "control_station_host": "192.168.68.101",
  "video_port": 5000,
  "ssid": "MiniCars Network",
  ...
}
```

#### No verificar SSID (iniciar en cualquier red)

```json
{
  "control_station_host": "SKLNx.local",
  "video_port": 5000,
  "ssid": null,
  ...
}
```

#### Cambiar resolución y bitrate

```json
{
  "control_station_host": "192.168.68.101",
  "video_port": 5000,
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "framerate": 30,
  "bitrate": 12000000,
  ...
}
```

## Despliegue

### Prerrequisitos

- Jetson Nano con JetPack instalado
- GStreamer instalado
- Python 3.x
- Repositorio clonado en `/home/jetson-rod/minicars-control-station`
- Usuario `jetson-rod` existe (o ajustar paths en service files)

### Paso 1: Configurar

Edita `jetson/config/stream_config.json` con tus parámetros:

```bash
cd /home/jetson-rod/minicars-control-station
nano jetson/config/stream_config.json
```

### Paso 2: Desplegar Servicios

Usa el script de despliegue automático:

```bash
cd /home/jetson-rod/minicars-control-station/jetson
chmod +x deploy_services.sh
./deploy_services.sh
```

El script:
1. ✅ Verifica que el repositorio existe
2. ✅ Copia service files a `/etc/systemd/system/`
3. ✅ Ejecuta `systemctl daemon-reload`
4. ✅ Habilita y reinicia `minicars-streamer.service`
5. ✅ Habilita y reinicia `minicars-joystick.service` (si no estaba habilitado)
6. ✅ Muestra estado de los servicios

### Paso 3: Verificar

```bash
# Ver estado del servicio
sudo systemctl status minicars-streamer.service

# Ver logs en tiempo real
journalctl -u minicars-streamer.service -f

# Ver últimas 50 líneas
journalctl -u minicars-streamer.service -n 50
```

## Comandos Útiles

### Ver Logs

```bash
# Streamer logs (tiempo real)
journalctl -u minicars-streamer.service -f

# Últimas 100 líneas
journalctl -u minicars-streamer.service -n 100

# Desde una fecha específica
journalctl -u minicars-streamer.service --since "2025-01-01 10:00:00"
```

### Controlar Servicio

```bash
# Reiniciar servicio (útil después de cambiar config)
sudo systemctl restart minicars-streamer.service

# Detener servicio
sudo systemctl stop minicars-streamer.service

# Iniciar servicio
sudo systemctl start minicars-streamer.service

# Deshabilitar autostart
sudo systemctl disable minicars-streamer.service

# Habilitar autostart
sudo systemctl enable minicars-streamer.service
```

### Actualizar Configuración

```bash
# 1. Editar configuración
nano jetson/config/stream_config.json

# 2. Reiniciar servicio para aplicar cambios
sudo systemctl restart minicars-streamer.service

# 3. Verificar que inició correctamente
journalctl -u minicars-streamer.service -n 20
```

## Comportamiento del Supervisor

### Estados

1. **Host accesible + Pipeline no corriendo**:
   - Supervisor intenta iniciar pipeline
   - Si falla, espera 10s antes de reintentar
   - Después de 5 fallos consecutivos, espera 30s

2. **Host accesible + Pipeline corriendo**:
   - Supervisor verifica periódicamente (cada 3s) que pipeline sigue vivo
   - Si pipeline muere, intenta reiniciarlo

3. **Host NO accesible + Pipeline corriendo**:
   - Supervisor detiene pipeline inmediatamente
   - Envía señal de terminación, luego kill si no responde

4. **Host NO accesible + Pipeline no corriendo**:
   - Supervisor espera (solo log cada ~30s)

### Verificación de Conectividad

El supervisor verifica conectividad intentando establecer una conexión TCP al puerto configurado (no solo ping). Esto asegura que:

- La red está funcionando
- El host está accesible
- El puerto no está bloqueado por firewall

### Verificación de SSID

Si `ssid` está configurado (no null ni vacío):

- Supervisor ejecuta `iwgetid -r` para obtener SSID actual
- Compara con SSID requerido
- Solo inicia pipeline si SSID coincide
- Si `iwgetid` falla (no WiFi, comando no instalado), considera SSID como no coincidente

## Troubleshooting

### Pipeline no inicia

**Síntoma**: Logs muestran "Host reachable" pero pipeline no inicia

**Posibles causas**:
1. nvargus-daemon no está corriendo
2. Cámara no disponible
3. Permisos insuficientes

**Solución**:
```bash
# Verificar nvargus-daemon
sudo systemctl status nvargus-daemon

# Ver logs detallados
journalctl -u minicars-streamer.service -n 100 | grep -i error

# Probar pipeline manualmente
cd /home/jetson-rod/minicars-control-station/jetson
python3 stream_supervisor.py
```

### Host siempre "unreachable"

**Síntoma**: Supervisor nunca inicia pipeline, logs muestran "Host unreachable"

**Posibles causas**:
1. IP/hostname incorrecto en config
2. Laptop no está en la misma red
3. Firewall bloqueando conexión
4. mDNS no funciona (si usas hostname como "SKLNx.local")

**Solución**:
```bash
# Verificar configuración
cat jetson/config/stream_config.json

# Probar conectividad manualmente
ping <control_station_host>
telnet <control_station_host> <video_port>

# Si usas mDNS, verificar resolución
ping SKLNx.local
# Si falla, usa IP directa en config
```

### SSID nunca coincide

**Síntoma**: Supervisor no inicia pipeline aunque host es accesible, logs muestran "SSID mismatch"

**Posibles causas**:
1. SSID configurado incorrectamente
2. `iwgetid` no está instalado
3. Jetson no está en WiFi

**Solución**:
```bash
# Ver SSID actual
iwgetid -r

# Verificar que coincide exactamente con config (mayúsculas/minúsculas)
cat jetson/config/stream_config.json | grep ssid

# Si no necesitas verificar SSID, ponlo en null:
# "ssid": null
```

### Pipeline se reinicia constantemente

**Síntoma**: Pipeline inicia pero muere inmediatamente, supervisor lo reinicia, ciclo se repite

**Posibles causas**:
1. Error en pipeline GStreamer
2. Cámara no disponible
3. nvargus-daemon con problemas

**Solución**:
```bash
# Ver stderr del pipeline en logs
journalctl -u minicars-streamer.service -n 200 | grep -A 5 -i error

# Reiniciar nvargus-daemon manualmente
sudo systemctl restart nvargus-daemon

# Verificar que cámara está disponible
ls -l /dev/video*
```

### Servicio no inicia al boot

**Síntoma**: Servicio no arranca automáticamente después de reiniciar Jetson

**Solución**:
```bash
# Verificar que está habilitado
systemctl is-enabled minicars-streamer.service

# Si dice "disabled", habilitarlo
sudo systemctl enable minicars-streamer.service

# Verificar dependencias
systemctl list-dependencies minicars-streamer.service
```

## Servicios Relacionados

### minicars-joystick.service

Este servicio es **independiente** del streaming:

- Maneja bridge TCP→UART para joystick
- No interfiere con streaming
- Debe estar habilitado para control del vehículo

### nvargus-daemon

El supervisor reinicia `nvargus-daemon` antes de iniciar el pipeline. Si esto causa problemas:

1. Verificar permisos sudo (supervisor necesita ejecutar `sudo systemctl restart nvargus-daemon`)
2. Configurar sudoers si es necesario:
   ```bash
   sudo visudo
   # Agregar línea:
   jetson-rod ALL=(ALL) NOPASSWD: /bin/systemctl restart nvargus-daemon
   ```

## Migración desde start_streamer.py

El servicio `minicars-streamer.service` ahora usa `stream_supervisor.py` en lugar de `start_streamer.py`.

**Cambios principales**:
- ✅ Configuración centralizada en JSON
- ✅ Supervisión de conectividad
- ✅ Verificación de SSID opcional
- ✅ Manejo robusto de errores
- ✅ Reintentos inteligentes

El archivo `start_streamer.py` se mantiene como referencia pero **no se usa** por el servicio systemd. Puede eliminarse si no se necesita.

## Actualizaciones Futuras

Para actualizar el código después del primer despliegue:

```bash
cd /home/jetson-rod/minicars-control-station
git pull origin main
cd jetson
./deploy_services.sh
```

Esto actualizará los service files y reiniciará los servicios automáticamente.

