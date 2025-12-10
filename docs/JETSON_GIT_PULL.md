# Guía: Git Pull en Jetson

## Pasos para Actualizar el Código en la Jetson

### 1. Conectar Jetson a Internet

Asegúrate de que la Jetson tenga conexión a internet:

```bash
# Verificar conectividad
ping -c 3 8.8.8.8

# Verificar acceso a GitHub
ping -c 3 github.com
```

### 2. Ir al Directorio del Repositorio

```bash
cd ~/minicars-control-station
```

### 3. Ver Estado Actual

```bash
# Ver en qué rama estás (probablemente main o master)
git branch

# Ver estado actual
git status

# Ver últimos commits remotos (sin descargar aún)
git fetch origin
git log HEAD..origin/main --oneline
```

### 4. Hacer Pull de los Cambios

```bash
# Descargar y aplicar cambios
git pull

# O si estás en otra rama o quieres ser específico:
git pull origin main
# O
git pull origin master
```

### 5. Verificar Cambios Descargados

```bash
# Ver el último commit
git log --oneline -3

# Ver qué archivos cambiaron
git diff HEAD~1 HEAD --name-status

# Ver cambios específicos en archivos importantes
git diff HEAD~1 HEAD -- jetson/stream_supervisor.py jetson/stream_config.py
```

### 6. Verificar Versión de Python

```bash
# Verificar versión de Python (debe ser 3.6+)
python3 --version
```

**Si ves error `ModuleNotFoundError: No module named 'dataclasses'`:**
- El código ahora es compatible con Python 3.6+, pero verifica la versión
- Ver `docs/JETSON_PYTHON_VERSION.md` para más detalles

### 7. Verificar Configuración

```bash
# Ir al directorio jetson
cd ~/minicars-control-station/jetson

# Verificar que la configuración se carga correctamente
python3 stream_config.py
```

**Deberías ver:**
```
[STREAM-CONFIG] ✓ Configuration valid
[STREAM-CONFIG]   Host: SKLNx.local
[STREAM-CONFIG]   Video Port: 5000
[STREAM-CONFIG]   Backend Port: 8000  <-- Debe aparecer esto
```

**Si ves error de `dataclasses`:**
- El código ahora maneja esto automáticamente (compatible con Python 3.6+)
- Si persiste, verifica que estás usando `python3` (no `python`)

### 8. Reiniciar Servicios

```bash
# Recargar systemd (por si hay cambios en archivos .service)
sudo systemctl daemon-reload

# Reiniciar el servicio de stream
sudo systemctl restart minicars-streamer.service

# Verificar estado
sudo systemctl status minicars-streamer.service

# Ver logs en tiempo real
sudo journalctl -u minicars-streamer.service -f
```

### 9. Verificar que los Cambios se Aplicaron

En los logs deberías ver:

```
[stream-supervisor] Control station: SKLNx.local
[stream-supervisor]   Video stream (UDP): port 5000
[stream-supervisor]   Backend check (TCP): port 8000  <-- Debe aparecer esto
```

Y cuando el backend esté disponible:

```
[stream-supervisor] Backend reachable at SKLNx.local:8000, starting pipeline...
```

---

## Troubleshooting

### Error: "Your local changes would be overwritten"

Si tienes cambios locales que no quieres perder:

```bash
# Ver qué archivos tienen cambios locales
git status

# Opción 1: Guardar cambios en stash
git stash
git pull
git stash pop  # Restaurar cambios locales (puede tener conflictos)

# Opción 2: Descartar cambios locales (CUIDADO: se pierden)
git reset --hard HEAD
git pull
```

### Error: "Failed to connect to github.com"

Verifica conectividad:

```bash
# Probar conectividad básica
ping -c 3 8.8.8.8

# Probar DNS
nslookup github.com

# Ver configuración de red
ip addr show
```

### Error: "Permission denied"

Asegúrate de tener permisos de escritura:

```bash
# Ver permisos
ls -la ~/minicars-control-station

# Si necesitas cambiar permisos (ajusta según tu caso)
sudo chown -R jetson-rod:jetson-rod ~/minicars-control-station
```

### Error: "ModuleNotFoundError: No module named 'dataclasses'"

El código ahora es compatible con Python 3.6+, pero si ves este error:

```bash
# Verificar versión de Python
python3 --version

# Si es < 3.6, necesitas actualizar Python
# Ver docs/JETSON_PYTHON_VERSION.md para más detalles
```

**Nota:** El código ahora maneja automáticamente la ausencia de `dataclasses` usando clases simples como fallback.

---

## Resumen Rápido (Copy-Paste)

```bash
cd ~/minicars-control-station
git pull
cd jetson
python3 stream_config.py  # Verificar config
sudo systemctl daemon-reload
sudo systemctl restart minicars-streamer.service
sudo journalctl -u minicars-streamer.service -f
```

