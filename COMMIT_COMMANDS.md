# Comandos para Commit

## Opción 1: Commit completo (todos los cambios)

```bash
# Agregar todos los archivos nuevos y modificados
git add backend/minicars_backend/joystick/throttle_mapper.py
git add backend/minicars_backend/joystick/protocol.py
git add backend/minicars_backend/joystick/sender.py
git add backend/minicars_backend/commands/start_car_control.py
git add backend/minicars_backend/commands/start_stream.py
git add backend/minicars_backend/api.py
git add jetson/minicars-streamer.service
git add jetson/tcp_uart_bridge.py
git add jetson/config/stream_config.json
git add jetson/stream_config.py
git add jetson/stream_supervisor.py
git add jetson/deploy_services.sh
git add docs/FLUJO_ANALISIS_FASE1.md
git add docs/CORRECCIONES_FASE_2_5.md
git add docs/FASE0_ANALISIS_SERVICIOS.md
git add docs/STREAMING_JETSON_AUTOSTART.md
git add docs/RESUMEN_STREAMING_SUPERVISOR.md

# Commit
git commit -m "feat: Implementar streaming supervisor y corregir protocolo joystick

- Backend: Alinear emisor joystick con car_control_logi.py
  - Nuevo throttle_mapper.py con lógica idéntica
  - Protocolo TCP 6 campos compatible con bridge
  - Mejoras en logging y manejo de errores

- Jetson: Sistema de streaming con supervisor
  - Supervisor Python que monitorea conectividad
  - Configuración centralizada en JSON
  - Script de despliegue automático
  - Migración de start_streamer.py a stream_supervisor.py

- Bridge: Compatibilidad con formatos 5 y 6 campos
  - Acepta formato legacy (5 campos) y nuevo (6 campos)
  - Backward compatible con car_control_logi.py

- Documentación completa de cambios y guías de uso"
```

## Opción 2: Commit separado por funcionalidad

### Commit 1: Correcciones de joystick

```bash
git add backend/minicars_backend/joystick/throttle_mapper.py
git add backend/minicars_backend/joystick/protocol.py
git add backend/minicars_backend/joystick/sender.py
git add backend/minicars_backend/commands/start_car_control.py
git add backend/minicars_backend/api.py
git add jetson/tcp_uart_bridge.py
git add docs/FLUJO_ANALISIS_FASE1.md
git add docs/CORRECCIONES_FASE_2_5.md

git commit -m "fix: Corregir protocolo joystick y alinear con car_control_logi.py

- Nuevo throttle_mapper.py con lógica idéntica a car_control_logi.py
- Protocolo TCP 6 campos para compatibilidad con bridge
- Bridge acepta formatos 5 y 6 campos (backward compatible)
- Mejoras en logging y manejo de errores
- Documentación de análisis de flujo"
```

### Commit 2: Sistema de streaming supervisor

```bash
git add jetson/minicars-streamer.service
git add jetson/config/stream_config.json
git add jetson/stream_config.py
git add jetson/stream_supervisor.py
git add jetson/deploy_services.sh
git add docs/FASE0_ANALISIS_SERVICIOS.md
git add docs/STREAMING_JETSON_AUTOSTART.md
git add docs/RESUMEN_STREAMING_SUPERVISOR.md

git commit -m "feat: Implementar supervisor de streaming para Jetson

- Supervisor Python que monitorea conectividad y gestiona pipeline
- Configuración centralizada en JSON (host, puerto, SSID, etc.)
- Verificación de conectividad TCP y SSID opcional
- Reintentos inteligentes con backoff
- Script de despliegue automático de servicios
- Migración de start_streamer.py a stream_supervisor.py
- Documentación completa de uso y troubleshooting"
```

### Commit 3: Mejoras menores en stream

```bash
git add backend/minicars_backend/commands/start_stream.py

git commit -m "refactor: Mejorar detección de procesos en start_stream

- Mejor detección de procesos terminados
- Mensaje informativo sobre streamer en Jetson"
```

## Opción 3: Git add con wildcards (más rápido)

```bash
# Agregar todos los archivos nuevos del backend/jetson/docs
git add backend/minicars_backend/joystick/
git add backend/minicars_backend/commands/
git add backend/minicars_backend/api.py
git add jetson/*.py
git add jetson/*.service
git add jetson/config/
git add jetson/*.sh
git add docs/*.md

# Commit
git commit -m "feat: Implementar streaming supervisor y corregir protocolo joystick

- Backend: Alinear emisor joystick con car_control_logi.py
  - Nuevo throttle_mapper.py con lógica idéntica
  - Protocolo TCP 6 campos compatible con bridge
  - Mejoras en logging y manejo de errores

- Jetson: Sistema de streaming con supervisor
  - Supervisor Python que monitorea conectividad
  - Configuración centralizada en JSON
  - Script de despliegue automático
  - Migración de start_streamer.py a stream_supervisor.py

- Bridge: Compatibilidad con formatos 5 y 6 campos
  - Acepta formato legacy (5 campos) y nuevo (6 campos)
  - Backward compatible con car_control_logi.py

- Documentación completa de cambios y guías de uso"
```

## Nota sobre archivos que NO deberían estar en el commit

Estos archivos aparecen modificados pero probablemente son cambios locales/desarrollo:

- `backend/config/control_profile.json` - Config local (modo "kid")
- `desktop/package.json`, `package-lock.json` - Dependencias npm
- `desktop/src-tauri/*` - Configuraciones Tauri
- `desktop/src/App.tsx` - Cambios de desarrollo
- `.github/workflows/build-windows.yml` - CI/CD
- `backend/main.py` - Cambios menores

**Recomendación**: Revisar estos archivos antes de commitear. Puedes usar:

```bash
# Ver qué cambió en cada archivo
git diff backend/config/control_profile.json
git diff desktop/package.json
git diff backend/main.py

# Si quieres excluirlos del commit:
git restore backend/config/control_profile.json  # Descartar cambios
# O agregarlos al .gitignore si son archivos de desarrollo local
```

## Comando final recomendado

```bash
# 1. Agregar solo los archivos relacionados con las correcciones
git add backend/minicars_backend/joystick/
git add backend/minicars_backend/commands/start_car_control.py
git add backend/minicars_backend/commands/start_stream.py
git add backend/minicars_backend/api.py
git add jetson/minicars-streamer.service
git add jetson/tcp_uart_bridge.py
git add jetson/config/
git add jetson/stream_config.py
git add jetson/stream_supervisor.py
git add jetson/deploy_services.sh
git add docs/

# 2. Verificar qué se va a commitear
git status

# 3. Commit
git commit -m "feat: Implementar streaming supervisor y corregir protocolo joystick

- Backend: Alinear emisor joystick con car_control_logi.py
  - Nuevo throttle_mapper.py con lógica idéntica
  - Protocolo TCP 6 campos compatible con bridge
  - Mejoras en logging y manejo de errores

- Jetson: Sistema de streaming con supervisor
  - Supervisor Python que monitorea conectividad
  - Configuración centralizada en JSON
  - Script de despliegue automático
  - Migración de start_streamer.py a stream_supervisor.py

- Bridge: Compatibilidad con formatos 5 y 6 campos
  - Acepta formato legacy (5 campos) y nuevo (6 campos)
  - Backward compatible con car_control_logi.py

- Documentación completa de cambios y guías de uso"
```

