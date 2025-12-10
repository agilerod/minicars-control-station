# Plan: Fix Stream Supervisor Connectivity Check

## Objetivo
Corregir el check de conectividad del `stream_supervisor.py` para que verifique el backend TCP (puerto 8000) en lugar del puerto UDP de video (5000), permitiendo que el supervisor detecte correctamente cuando la laptop está disponible e inicie el pipeline GStreamer.

## Problema Actual
- El supervisor verifica conectividad a `SKLNx.local:5000` usando TCP
- El puerto 5000 es UDP (para video streaming)
- UDP no responde a conexiones TCP, por lo que el check siempre falla
- El pipeline nunca se inicia porque el supervisor piensa que la laptop no está disponible

## Solución
- Cambiar el check de conectividad para verificar el puerto 8000 (backend FastAPI TCP)
- El backend está siempre disponible cuando la app está corriendo
- Mantener UDP para el video stream (baja latencia)
- Mejorar logging para diagnóstico

---

## Cambios Requeridos

### 1. Actualizar `stream_config.py`
- Agregar campo opcional `backend_port` (default: 8000) para el puerto de verificación
- Mantener `video_port` para el stream UDP real

### 2. Actualizar `stream_supervisor.py`
- Modificar `main_loop()` para usar `backend_port` en el check de conectividad
- Actualizar logs para mostrar claramente qué puerto está verificando
- Mejorar mensajes de log para diagnóstico

### 3. Actualizar `stream_config.json` (opcional)
- Agregar `backend_port: 8000` si queremos explicitarlo, o dejar que use default

---

## Archivos a Modificar

1. `jetson/stream_config.py` - Agregar campo `backend_port`
2. `jetson/stream_supervisor.py` - Cambiar check de conectividad
3. `jetson/config/stream_config.json` - (Opcional) Agregar `backend_port`

---

## Plan de Pruebas

### Prueba 1: Verificación de Configuración
**Objetivo:** Verificar que la configuración se carga correctamente

**Pasos:**
```bash
# En Jetson
cd ~/minicars-control-station/jetson
python3 stream_config.py
```

**Resultado esperado:**
- Configuración válida
- Muestra `backend_port: 8000` (o el valor configurado)

---

### Prueba 2: Check de Conectividad Manual
**Objetivo:** Verificar que el check TCP al puerto 8000 funciona

**Pasos:**
```bash
# En Jetson
python3 << 'EOF'
import socket
from stream_config import load_config

config = load_config()
host = config.control_station_host
backend_port = 8000  # O config.backend_port si lo agregamos

print(f"Verificando conectividad a {host}:{backend_port}...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    result = sock.connect_ex((host, backend_port))
    sock.close()
    if result == 0:
        print(f"✓ Conexión exitosa a {host}:{backend_port}")
    else:
        print(f"✗ Conexión falló (código: {result})")
except Exception as e:
    print(f"✗ Error: {e}")
EOF
```

**Pre-requisito:** Backend debe estar corriendo en laptop (puerto 8000)

**Resultado esperado:**
- Conexión exitosa cuando backend está corriendo
- Conexión falla cuando backend está detenido

---

### Prueba 3: Supervisor Detecta Backend Disponible
**Objetivo:** Verificar que el supervisor detecta cuando el backend está disponible

**Pasos:**
1. **Asegurar backend NO está corriendo:**
   ```bash
   # En laptop, detener backend si está corriendo
   ```

2. **Reiniciar servicio del supervisor:**
   ```bash
   # En Jetson
   sudo systemctl restart minicars-streamer.service
   sudo journalctl -u minicars-streamer.service -f
   ```

3. **Verificar logs:**
   - Debe mostrar "Waiting for connectivity..." o similar
   - NO debe iniciar pipeline

4. **Iniciar backend en laptop:**
   ```bash
   # En laptop
   cd desktop
   npm run tauri:dev
   ```

5. **Observar logs del supervisor:**
   ```bash
   # En Jetson (ya corriendo journalctl -f)
   ```

**Resultado esperado:**
- Logs muestran "Backend reachable" o similar
- Pipeline se inicia automáticamente
- Logs muestran "GStreamer pipeline started successfully"

---

### Prueba 4: End-to-End - Stream Completo
**Objetivo:** Verificar que el stream funciona end-to-end

**Pasos:**
1. **Backend corriendo en laptop** (puerto 8000 activo)

2. **Supervisor corriendo en Jetson:**
   ```bash
   sudo systemctl status minicars-streamer.service
   ```

3. **En laptop, hacer clic en "Start Stream"**

4. **Verificar en Jetson:**
   ```bash
   # Ver logs del supervisor
   sudo journalctl -u minicars-streamer.service -f
   
   # Verificar que pipeline está corriendo
   ps aux | grep gst-launch
   ps aux | grep nvarguscamerasrc
   ```

5. **Verificar en laptop:**
   - Ventana de video debe aparecer
   - Video debe fluir desde la cámara de la Jetson

**Resultado esperado:**
- Supervisor detecta backend → inicia pipeline
- Pipeline GStreamer está corriendo en Jetson
- Video aparece en laptop
- Stream fluye sin problemas

---

### Prueba 5: Supervisor Detiene Pipeline cuando Backend se Detiene
**Objetivo:** Verificar que el supervisor detiene el pipeline cuando el backend no está disponible

**Pasos:**
1. **Con stream funcionando (Prueba 4 completada)**

2. **Detener backend en laptop:**
   - Cerrar aplicación Tauri o detener backend

3. **Observar logs del supervisor:**
   ```bash
   # En Jetson
   sudo journalctl -u minicars-streamer.service -f
   ```

4. **Verificar que pipeline se detuvo:**
   ```bash
   ps aux | grep gst-launch
   ```

**Resultado esperado:**
- Logs muestran "Backend unreachable, stopping pipeline"
- Pipeline se detiene correctamente
- Supervisor espera a que backend vuelva a estar disponible

---

### Prueba 6: Verificación de Logs Claros
**Objetivo:** Verificar que los logs son claros y útiles para diagnóstico

**Pasos:**
```bash
# En Jetson
sudo journalctl -u minicars-streamer.service -n 50
```

**Resultado esperado:**
- Logs muestran claramente qué puerto está verificando (8000)
- Logs muestran estado de conectividad ("Backend reachable" / "Backend unreachable")
- Logs muestran cuándo pipeline inicia/detiene
- Logs son fáciles de entender

---

## Criterios de Éxito

✅ **Configuración:**
- `stream_config.py` carga correctamente con `backend_port`
- Configuración es backward compatible (funciona sin `backend_port` en JSON)

✅ **Conectividad:**
- Supervisor detecta correctamente cuando backend (puerto 8000) está disponible
- Supervisor detecta correctamente cuando backend NO está disponible

✅ **Pipeline:**
- Pipeline se inicia automáticamente cuando backend está disponible
- Pipeline se detiene automáticamente cuando backend no está disponible
- Pipeline envía video correctamente a laptop (UDP 5000)

✅ **End-to-End:**
- Usuario hace clic en "Start Stream" → receptor inicia en laptop
- Supervisor detecta backend → inicia pipeline en Jetson
- Video fluye correctamente

✅ **Logs:**
- Logs son claros y útiles para diagnóstico
- Fácil identificar problemas

---

## Rollback Plan

Si algo falla:

1. **Revertir cambios en código:**
   ```bash
   git checkout jetson/stream_config.py jetson/stream_supervisor.py
   ```

2. **Restaurar configuración:**
   ```bash
   # Si se modificó stream_config.json
   git checkout jetson/config/stream_config.json
   ```

3. **Reiniciar servicio:**
   ```bash
   sudo systemctl restart minicars-streamer.service
   ```

---

## Notas

- **No romper funcionalidad existente:** Los cambios deben ser backward compatible
- **Logging mejorado:** Los logs deben ayudar a diagnosticar problemas rápidamente
- **Pruebas incrementales:** Ejecutar pruebas en orden, verificar cada una antes de continuar
- **Documentación:** Actualizar README o docs si es necesario

---

## Próximos Pasos Después del Fix

1. Verificar que todo funciona en producción
2. Documentar el flujo completo en `docs/`
3. Considerar agregar tests automatizados si es necesario
4. Revisar si hay optimizaciones adicionales posibles

