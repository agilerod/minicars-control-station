# Guía de Pruebas - Backend Bundling en Tauri

## Checklist de Pruebas

### ✅ Pre-requisitos

- [x] `desktop/src-tauri/tauri.conf.json` tiene `"resources": ["../backend"]`
- [x] `main.rs` usa `app.path_resolver().resolve_resource("backend")`
- [x] `ensure_backend_running` recibe `AppHandle` como parámetro
- [x] Código Rust compila sin errores

## Prueba 1: Modo Desarrollo

### Comandos

```bash
cd desktop
npm run tauri:dev
```

### Qué Verificar

1. **Ventana se abre correctamente**
   - La aplicación debería iniciar sin errores
   - No debería aparecer banner rojo de "No se pudo iniciar el backend"

2. **Logs en consola (revisar terminal donde ejecutaste `tauri:dev`)**

   Deberías ver algo como:
   ```
   [Tauri] Development mode detected
   [Tauri] Using backend from workspace root (dev): C:\Users\...\minicars-control-station\backend
   [Tauri] Found Python command: python
   [Tauri] Starting backend:
     Backend path: C:\Users\...\minicars-control-station\backend
     Command: python -m uvicorn main:app --host 127.0.0.1 --port 8000
   [Tauri] Backend process started successfully (PID: ...)
   ```

3. **Backend responde**
   - Hacer clic en botones de la UI debería funcionar
   - El estado del backend debería ser "running" o "ok"

### Si hay errores

- **Error "BACKEND_DIR_NOT_FOUND"**: Verificar que existe `backend/main.py`
- **Error "PYTHON_NOT_FOUND"**: Verificar que Python está en PATH (`python --version`)
- **Error "SPAWN_FAILED"**: Revisar logs detallados en consola para ver comando y error específico

## Prueba 2: Build NSIS

### Comandos

```bash
cd desktop
npm run tauri:build:nsis
```

### Qué Verificar

1. **Build completa sin errores**
   - No debería haber errores de compilación Rust
   - No debería haber errores de empaquetado

2. **Instalador generado**
   - Ubicación: `desktop/src-tauri/target/release/bundle/nsis/`
   - Archivo: `MiniCars Control Station_0.1.0_x64-setup.exe` (o similar)

3. **Recursos incluidos**
   - El instalador debería incluir el directorio `backend/`
   - Verificar tamaño del instalador (debería ser significativamente mayor si incluye backend)

## Prueba 3: Instalación y Ejecución (Producción)

### Pasos

1. **Instalar la aplicación**
   ```bash
   # Ejecutar el instalador generado
   .\desktop\src-tauri\target\release\bundle\nsis\MiniCars Control Station_0.1.0_x64-setup.exe
   ```

2. **Ejecutar la aplicación instalada**
   - Buscar "MiniCars Control Station" en el menú inicio
   - Ejecutar la aplicación

3. **Verificar logs**
   - Abrir Event Viewer o buscar logs de Tauri
   - O revisar la consola si está disponible

   Deberías ver:
   ```
   [Tauri] Production mode detected
   [Tauri] Using backend from Tauri resources: C:\Users\...\AppData\Local\Programs\minicars-control-station\resources\backend
   [Tauri] Found Python command: python
   [Tauri] Starting backend:
     Backend path: C:\Users\...\AppData\Local\Programs\minicars-control-station\resources\backend
     Command: python -m uvicorn main:app --host 127.0.0.1 --port 8000
   [Tauri] Backend process started successfully (PID: ...)
   ```

4. **Funcionalidad**
   - La aplicación debería iniciar sin errores
   - El backend debería estar disponible
   - Los botones deberían funcionar

### Si hay errores en producción

- **Error "Backend folder not found in Tauri resources"**: 
  - Verificar que `tauri.conf.json` tiene `"resources": ["../backend"]`
  - Verificar que el build incluyó el directorio backend

- **Error "main.py not found"**:
  - Verificar que `backend/main.py` existe y se incluyó en el bundle
  - Revisar estructura de directorios en `target/release/bundle/`

## Prueba 4: Variable de Entorno (Debugging)

### Test con MINICARS_BACKEND_PATH

```bash
# Windows PowerShell
$env:MINICARS_BACKEND_PATH="C:\ruta\a\tu\backend\personalizado"
cd desktop
npm run tauri:dev
```

### Qué Verificar

En los logs deberías ver:
```
[Tauri] Development mode detected
[Tauri] Using backend from MINICARS_BACKEND_PATH: C:\ruta\a\tu\backend\personalizado
```

La aplicación debería usar ese backend en lugar del del workspace.

## Solución de Problemas Comunes

### Problema: Backend no se encuentra en producción

**Causa**: El directorio backend no se incluyó en el bundle.

**Solución**:
1. Verificar `tauri.conf.json` tiene `"resources": ["../backend"]`
2. Verificar que `backend/main.py` existe
3. Limpiar y rebuild:
   ```bash
   cd desktop/src-tauri
   cargo clean
   cd ..
   npm run tauri:build:nsis
   ```

### Problema: Python no encontrado

**Causa**: Python no está en PATH del usuario final.

**Solución**: 
- Instalar Python 3.10+ y asegurarse de que está en PATH
- O usar la variable de entorno MINICARS_BACKEND_PATH con un backend que tenga Python embebido (futuro)

### Problema: Build falla con error de recursos

**Causa**: Ruta relativa incorrecta en `resources`.

**Solución**:
- Verificar que desde `src-tauri/` la ruta `../backend` es correcta
- Verificar que `backend/` existe en la ubicación esperada

## Verificación Final

Después de todas las pruebas:

- [ ] Modo desarrollo funciona correctamente
- [ ] Build NSIS se completa sin errores
- [ ] Instalador incluye backend
- [ ] Aplicación instalada inicia backend desde recursos
- [ ] Backend responde a peticiones
- [ ] Variable de entorno MINICARS_BACKEND_PATH funciona (opcional)

