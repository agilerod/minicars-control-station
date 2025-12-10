# Comandos para Commit: Fix Stream Supervisor + Backend Bundling

## Nota: Dos Commits Separados

Hay cambios de dos fixes diferentes. Se recomienda hacer dos commits separados:

1. **Commit 1: Backend Bundling Fix** (cambios anteriores)
2. **Commit 2: Stream Supervisor Fix** (cambios nuevos)

---

## COMMIT 1: Backend Bundling Fix

```bash
# 1. Agregar archivos del fix de backend bundling
git add desktop/src-tauri/tauri.conf.json \
        desktop/src-tauri/src/main.rs \
        desktop/src/App.tsx \
        docs/DESKTOP_BACKEND_BUNDLING.md \
        docs/PRUEBAS_BACKEND_BUNDLING.md

# 2. Commit
git commit -m "fix: bundle Python backend and resolve path via Tauri resources

- Agregado backend/ a bundle.resources en tauri.conf.json
- Resolución robusta de ruta: MINICARS_BACKEND_PATH -> Tauri resources -> dev paths
- Mejorado manejo de errores con mensajes claros para frontend
- App.tsx muestra errores específicos de backend startup
- Documentación de bundling y pruebas"

# 3. Verificar
git log --oneline -1
```

---

## COMMIT 2: Stream Supervisor Fix + Backend Network Access

**IMPORTANTE:** `desktop/src-tauri/src/main.rs` ya está en el commit anterior, pero tiene UN CAMBIO ADICIONAL (0.0.0.0). Tienes dos opciones:

### Opción A: Incluir el cambio de 0.0.0.0 en este commit (recomendado)

```bash
# 1. Agregar archivos del fix de stream supervisor
git add jetson/stream_config.py \
        jetson/stream_supervisor.py \
        jetson/config/stream_config.json \
        docs/PLAN_FIX_STREAM_SUPERVISOR.md \
        docs/DEPLOY_STREAM_FIX.md \
        docs/JETSON_SUDO_CONFIG.md \
        COMMIT_STREAM_FIX.md

# 2. Agregar cambio de backend network access (modificación adicional en main.rs)
# Este archivo ya estaba modificado, pero tiene un cambio adicional (0.0.0.0)
git add desktop/src-tauri/src/main.rs

# 3. Commit
git commit -m "fix: stream supervisor verifica backend TCP y backend accesible desde red

- Backend ahora escucha en 0.0.0.0:8000 (antes 127.0.0.1) para acceso desde Jetson
- Supervisor verifica conectividad al puerto 8000 (backend TCP) en lugar de 5000 (UDP)
- Agregado campo backend_port en stream_config.py (default: 8000)
- Mejorado logging para mostrar claramente qué puerto se verifica
- Agregadas verificaciones para evitar duplicidad de servicios/pipelines
- Reinicio de nvargus-daemon ahora es opcional (continúa si falla)
- Mejorada captura de errores de GStreamer para diagnóstico
- Documentación completa: plan, despliegue y configuración sudo"

# 4. Verificar
git log --oneline -2
```

### Opción B: Hacer un commit separado solo para el cambio de 0.0.0.0

```bash
# Commit intermedio solo para el cambio de network access
git add desktop/src-tauri/src/main.rs
git commit -m "fix: backend escucha en 0.0.0.0:8000 para acceso desde red

- Cambio de 127.0.0.1 a 0.0.0.0 para permitir conexiones desde Jetson
- Requerido para que stream supervisor pueda verificar conectividad"

# Luego el commit 2 sin main.rs
git add jetson/stream_config.py \
        jetson/stream_supervisor.py \
        jetson/config/stream_config.json \
        docs/PLAN_FIX_STREAM_SUPERVISOR.md \
        docs/DEPLOY_STREAM_FIX.md \
        docs/JETSON_SUDO_CONFIG.md \
        COMMIT_STREAM_FIX.md
git commit -m "fix: stream supervisor verifica backend TCP (puerto 8000)

- Supervisor verifica conectividad al puerto 8000 (backend TCP) en lugar de 5000 (UDP)
- Agregado campo backend_port en configuración
- Protecciones contra duplicidad y mejoras en logging"
```

---

## OPCIÓN: Commit Único (No Recomendado pero Válido)

Si prefieres hacer un solo commit de todo:

```bash
# Agregar todos los archivos modificados y nuevos
git add desktop/src-tauri/tauri.conf.json \
        desktop/src-tauri/src/main.rs \
        desktop/src/App.tsx \
        jetson/stream_config.py \
        jetson/stream_supervisor.py \
        jetson/config/stream_config.json \
        docs/DESKTOP_BACKEND_BUNDLING.md \
        docs/PRUEBAS_BACKEND_BUNDLING.md \
        docs/PLAN_FIX_STREAM_SUPERVISOR.md \
        docs/DEPLOY_STREAM_FIX.md \
        docs/JETSON_SUDO_CONFIG.md \
        COMMIT_STREAM_FIX.md

# Commit único
git commit -m "fix: backend bundling + network access + stream supervisor TCP check

Backend Bundling:
- Bundle Python backend via Tauri resources
- Resolución robusta de ruta backend
- Mejor manejo de errores

Network Access:
- Backend escucha en 0.0.0.0:8000 para acceso desde Jetson

Stream Supervisor:
- Supervisor verifica puerto 8000 (backend TCP) en lugar de 5000 (UDP)
- Protecciones contra duplicidad y mejoras en logging
- Documentación completa"
```

---

## Push (después de commits)

```bash
# Push todos los commits
git push
```

---

## Verificación Post-Commit

```bash
# Ver últimos commits
git log --oneline -5

# Ver cambios de un commit específico
git show <commit-hash> --stat
```

---

## Notas Importantes

- **`desktop/src-tauri/src/main.rs`** tiene cambios de AMBOS fixes (bundling + network access)
- Si haces commits separados, el segundo commit incluirá el cambio de 0.0.0.0
- **Archivos opcionales** (puedes excluirlos del commit si quieres):
  - `COMMIT_STREAM_FIX.md` (este archivo)
  - `COMMIT_COMMANDS.md` (si existe, es temporal)
