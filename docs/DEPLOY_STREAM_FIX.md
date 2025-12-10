# Guía de Despliegue: Fix Stream Supervisor

## Archivos Modificados

Los siguientes archivos fueron modificados y deben ser desplegados en la Jetson:

1. `jetson/stream_config.py` - Agregado campo `backend_port`
2. `jetson/stream_supervisor.py` - Cambio de check de conectividad a puerto 8000 TCP
3. `jetson/config/stream_config.json` - Agregado `backend_port: 8000`

---

## Paso 1: Commit y Push desde Laptop

**En la laptop (desde el directorio del repo):**

```bash
# Verificar cambios
git status

# Ver qué archivos fueron modificados
git diff jetson/stream_config.py jetson/stream_supervisor.py jetson/config/stream_config.json

# Agregar archivos modificados
git add jetson/stream_config.py \
        jetson/stream_supervisor.py \
        jetson/config/stream_config.json

# Commit con mensaje descriptivo
git commit -m "fix: stream supervisor ahora verifica backend TCP (8000) en lugar de UDP (5000)

- Agregado campo backend_port en stream_config.py (default: 8000)
- Supervisor verifica conectividad al puerto 8000 (backend FastAPI) en lugar de 5000 (UDP)
- Mejorado logging para mostrar claramente qué puerto se verifica
- Agregadas verificaciones para evitar duplicidad de servicios/pipelines
- Actualizado stream_config.json con backend_port explícito"

# Push a GitHub (o tu repositorio remoto)
git push
```

---

## Paso 2: Desplegar en Jetson

**En la Jetson:**

### 2.1 Conectar Jetson a Internet

Asegúrate de que la Jetson tenga conexión a internet para poder hacer `git pull`.

```bash
# Verificar conectividad
ping -c 3 8.8.8.8

# Verificar que puedes acceder a GitHub (o tu repositorio)
ping -c 3 github.com
```

### 2.2 Descargar Cambios

```bash
# Ir al directorio del repo en Jetson
cd ~/minicars-control-station

# Verificar que estás en la rama correcta (probablemente main o master)
git branch

# Descargar cambios
git pull

# Verificar que los archivos fueron actualizados
git log --oneline -1
git diff HEAD~1 HEAD -- jetson/stream_config.py jetson/stream_supervisor.py jetson/config/stream_config.json
```

### 2.3 Verificar Configuración

```bash
# Verificar que la configuración se carga correctamente
cd ~/minicars-control-station/jetson
python3 stream_config.py
```

**Resultado esperado:**
```
[STREAM-CONFIG] ✓ Configuration valid
[STREAM-CONFIG]   Host: SKLNx.local
[STREAM-CONFIG]   Video Port: 5000
[STREAM-CONFIG]   Backend Port: 8000
[STREAM-CONFIG]   SSID: (no check)
...
```

---

## Paso 3: Reiniciar Servicio

**En la Jetson:**

```bash
# Recargar systemd (por si hay cambios en archivos .service)
sudo systemctl daemon-reload

# Reiniciar el servicio para aplicar cambios
sudo systemctl restart minicars-streamer.service

# Verificar que el servicio inició correctamente
sudo systemctl status minicars-streamer.service

# Ver logs en tiempo real para verificar que está funcionando
sudo journalctl -u minicars-streamer.service -f
```

---

## Paso 4: Verificar que los Cambios se Aplicaron

### 4.1 Verificar Logs del Servicio

En los logs deberías ver:

```
[stream-supervisor] ============================================================
[stream-supervisor] MiniCars Stream Supervisor Starting
[stream-supervisor] ============================================================
[stream-supervisor] Control station: SKLNx.local
[stream-supervisor]   Video stream (UDP): port 5000
[stream-supervisor]   Backend check (TCP): port 8000    <-- NUEVO
[stream-supervisor] SSID check: (disabled)
[stream-supervisor] Resolution: 1280x720@30fps
[stream-supervisor] Bitrate: 8000000 bps
[stream-supervisor] ============================================================
```

### 4.2 Verificar que Detecta Backend

**Con backend corriendo en laptop (puerto 8000 activo):**

Deberías ver en los logs:

```
[stream-supervisor] Backend reachable at SKLNx.local:8000, starting pipeline...
[stream-supervisor] Starting GStreamer pipeline to SKLNx.local:5000...
[stream-supervisor] GStreamer pipeline started successfully
```

**Con backend NO corriendo en laptop:**

Deberías ver:

```
[stream-supervisor] Waiting for backend connectivity... (backend unreachable at SKLNx.local:8000)
```

---

## Paso 5: Prueba End-to-End

1. **Backend corriendo en laptop** (puerto 8000 activo)
2. **Supervisor corriendo en Jetson** (verificado en Paso 4)
3. **En laptop, hacer clic en "Start Stream"**
4. **Verificar en Jetson:**
   ```bash
   # Ver logs
   sudo journalctl -u minicars-streamer.service -f
   
   # Verificar que pipeline está corriendo
   ps aux | grep gst-launch
   ```
5. **Verificar en laptop:** Ventana de video debe aparecer

---

## Rollback (Si Algo Falla)

Si necesitas revertir los cambios:

```bash
# En Jetson
cd ~/minicars-control-station

# Ver historial de commits
git log --oneline -5

# Revertir al commit anterior (reemplaza COMMIT_HASH con el hash del commit anterior)
git checkout <COMMIT_HASH> -- jetson/stream_config.py jetson/stream_supervisor.py jetson/config/stream_config.json

# Reiniciar servicio
sudo systemctl restart minicars-streamer.service
```

O simplemente volver a hacer `git pull` del commit anterior.

---

## Verificación de Duplicidad de Servicios

Antes de reiniciar, verifica que NO hay servicios duplicados:

```bash
# Verificar servicios relacionados
systemctl list-units --all | grep -E "minicar|minicars"

# Deberías ver solo:
# minicars-joystick.service
# minicars-streamer.service
# 
# NO deberías ver:
# minicar-ctrl.service (debe estar disabled/stopped)
```

Si ves `minicar-ctrl.service` activo, detenerlo:

```bash
sudo systemctl stop minicar-ctrl.service
sudo systemctl disable minicar-ctrl.service
```

---

## Checklist de Despliegue

- [ ] Cambios commiteados y pusheados desde laptop
- [ ] Jetson conectada a internet
- [ ] `git pull` ejecutado en Jetson
- [ ] Configuración verificada (`python3 stream_config.py`)
- [ ] Servicio reiniciado (`sudo systemctl restart minicars-streamer.service`)
- [ ] Logs verificados (muestra "Backend check (TCP): port 8000")
- [ ] No hay servicios duplicados
- [ ] Prueba end-to-end exitosa

---

## Troubleshooting

### Error: "Configuration error" al cargar config
```bash
# Verificar que stream_config.json tiene backend_port
cat ~/minicars-control-station/jetson/config/stream_config.json | grep backend_port
```

### Error: "ModuleNotFoundError" o errores de importación
```bash
# Verificar que estás en el directorio correcto
cd ~/minicars-control-station/jetson

# Verificar que los archivos existen
ls -la stream_config.py stream_supervisor.py
```

### El supervisor no detecta el backend
```bash
# Verificar conectividad manual
python3 << 'EOF'
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2.0)
result = sock.connect_ex(("SKLNx.local", 8000))
sock.close()
print("✓ Conexión exitosa" if result == 0 else f"✗ Conexión falló (código: {result})")
EOF
```

---

## Notas Importantes

- **NO ejecutar `git` desde el asistente** - El usuario debe ejecutar los comandos manualmente
- Los cambios solo se aplican después de reiniciar el servicio
- Verificar siempre los logs después de reiniciar
- Mantener el backend corriendo en la laptop durante las pruebas

