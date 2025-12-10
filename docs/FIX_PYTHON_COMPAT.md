# Fix: Compatibilidad Python 3.6+ y Mejora de Errores GStreamer

## Problemas Resueltos

### 1. Error: `ModuleNotFoundError: No module named 'dataclasses'`

**Causa:** La Jetson estaba usando Python 3.6 o anterior, donde `dataclasses` no está disponible (se agregó en Python 3.7).

**Solución:**
- `jetson/stream_config.py` ahora detecta si `dataclasses` está disponible
- Si no está disponible, usa clases simples como fallback
- Compatible con Python 3.6+ (requisito mínimo: 3.6)

### 2. Pipeline GStreamer muere sin mostrar error

**Causa:** La captura de errores de GStreamer no estaba leyendo correctamente `stderr`.

**Solución:**
- `jetson/stream_supervisor.py` ahora usa `communicate()` para capturar todo el output
- Muestra tanto `stdout` como `stderr` cuando el pipeline falla
- Mensajes de error más claros con causas comunes

## Archivos Modificados

1. **`jetson/stream_config.py`**
   - Compatibilidad con Python 3.6+ (fallback sin `dataclasses`)
   - Verificación de versión de Python al inicio
   - Inicialización manual de clases si `dataclasses` no está disponible

2. **`jetson/stream_supervisor.py`**
   - Mejorada captura de errores de GStreamer usando `communicate()`
   - Muestra `stdout` y `stderr` cuando el pipeline falla
   - Mensajes de error más descriptivos

## Cómo Probar

### En la Jetson:

```bash
# 1. Verificar versión de Python
python3 --version  # Debe ser 3.6+

# 2. Probar stream_config.py
cd ~/minicars-control-station/jetson
python3 stream_config.py

# Deberías ver:
# [STREAM-CONFIG] ✓ Configuration valid
# [STREAM-CONFIG]   Host: SKLNx.local
# [STREAM-CONFIG]   Video Port: 5000
# [STREAM-CONFIG]   Backend Port: 8000

# 3. Reiniciar servicio
sudo systemctl restart minicars-streamer.service

# 4. Ver logs (ahora deberían mostrar errores de GStreamer si falla)
sudo journalctl -u minicars-streamer.service -f
```

## Qué Buscar en los Logs

**Si el pipeline falla, ahora verás:**
```
[stream-supervisor] ERROR: Pipeline failed to start (exit code: 1)
[stream-supervisor] ERROR: GStreamer stderr:
[stream-supervisor] ERROR: [mensaje de error real de GStreamer]
```

**En lugar de:**
```
[stream-supervisor] WARNING: Previous pipeline died (exit code: 1)
[stream-supervisor] ERROR: No error output captured.
```

## Próximos Pasos

1. Hacer `git pull` en la Jetson (ver `docs/JETSON_GIT_PULL.md`)
2. Verificar que `python3 stream_config.py` funciona
3. Reiniciar el servicio y ver los logs
4. Si el pipeline sigue fallando, los logs ahora mostrarán el error real de GStreamer

