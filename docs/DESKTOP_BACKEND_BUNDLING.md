# Backend Python Bundling en Tauri

## Resumen

El backend Python se empaqueta automáticamente en el instalador NSIS usando `bundle.resources` de Tauri. La aplicación resuelve la ruta del backend usando un orden de prioridades.

## Empaquetado

El directorio `backend/` se incluye en el bundle mediante la configuración en `desktop/src-tauri/tauri.conf.json`:

```json
"bundle": {
  "resources": [
    "../backend"
  ]
}
```

En Windows, Tauri copia los recursos al directorio interno de la aplicación. No es necesario manejar la ruta manualmente; se usa `path_resolver` de Tauri.

## Resolución de Ruta

La aplicación resuelve la ruta del backend siguiendo este orden:

1. **Variable de entorno `MINICARS_BACKEND_PATH`** (modo avanzado/debugging)
   - Si existe y es válido, se usa directamente.

2. **Recursos empaquetados de Tauri** (modo producción)
   - Usa `app.path_resolver().resolve_resource("backend")`.
   - Funciona cuando la app está instalada desde el instalador NSIS.

3. **Rutas de desarrollo** (solo en modo desarrollo)
   - Busca en `<workspace_root>/backend` calculado desde `CARGO_MANIFEST_DIR`.
   - Fallback a rutas relativas desde el directorio actual.

## Requisitos del Usuario Final

El usuario solo necesita tener **Python 3.10+** instalado y disponible en PATH. La aplicación detecta automáticamente si Python está disponible como `python` o `py` (Windows).

## Debugging

Para debugging avanzado, puedes usar la variable de entorno:

```bash
set MINICARS_BACKEND_PATH=C:\ruta\a\tu\backend
```

Los logs de la aplicación muestran qué ruta se está usando y los errores incluyen información detallada sobre rutas probadas y comandos ejecutados.

