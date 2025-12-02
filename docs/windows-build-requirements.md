# Requisitos de build en Windows para MiniCars Control Station (Tauri + Rust)

Este documento resume los prerrequisitos de compilación para la app de escritorio basada en **Tauri + Rust** en Windows 10/11.

## 1. Componentes necesarios

Tauri para Windows usa el toolchain **MSVC** de Visual Studio. Necesitas:

- **Visual Studio Build Tools 2022** (o Visual Studio 2019/2022) con:
  - **MSVC v143 build tools** (o superior)
  - **Windows 10 SDK** y/o **Windows 11 SDK**
- Herramientas de compilación en PATH:
  - `cl.exe` (compilador de C/C++)
  - `link.exe` (linker de MSVC)
- **Rust** instalado con el target MSVC:
  - `rustup default stable-x86_64-pc-windows-msvc`

Si falta `link.exe`, verás errores como:

> error: linker `link.exe` not found

## 2. Instalación de Visual Studio Build Tools (mínimo)

La forma más sencilla es usando **winget**:

```powershell
winget install --id Microsoft.VisualStudio.2022.BuildTools -e
```

Durante la instalación, asegúrate de seleccionar:

- **Workload**: “Desarrollo de escritorio con C++” (Desktop development with C++).
- Componentes individuales (si aparece el selector):
  - `MSVC v143 - VS 2022 C++ x64/x86 build tools`
  - `Windows 10 SDK` (última versión disponible)
  - (Opcional) `Windows 11 SDK` si está disponible.

## 3. Verificación de la instalación

Abre una terminal **PowerShell** nueva y ejecuta:

```powershell
where cl
where link
rustc -vV
```

Esperado:

- `where cl` apunta a una ruta similar a:
  - `C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\...\bin\Hostx64\x64\cl.exe`
- `where link` apunta a:
  - `C:\Program Files\Microsoft Visual Studio\2022\BuildTools\VC\Tools\MSVC\...\bin\Hostx64\x64\link.exe`
- `rustc -vV` muestra un host triple similar a:
  - `x86_64-pc-windows-msvc`

Si `cl.exe` o `link.exe` no se encuentran:

- Reabre la terminal (para que se actualice el PATH).
- Si sigue sin encontrarlos, abre el menú Inicio → “Developer Command Prompt for VS 2022” y prueba allí:

```powershell
where cl
where link
```

Si allí sí aparecen, revisa la configuración de PATH de tu usuario o usa siempre esa terminal para build de Tauri.

## 4. Configuración de Rust para MSVC

Asegúrate de usar el toolchain MSVC (no GNU) en Windows:

```powershell
rustup set default-host x86_64-pc-windows-msvc
rustup default stable
```

Para verificar:

```powershell
rustc -vV
```

Debe indicar `host: x86_64-pc-windows-msvc`.

## 5. Checklist rápido antes de construir Tauri

1. [ ] `rustc -vV` muestra `x86_64-pc-windows-msvc`.
2. [ ] `where cl` devuelve al menos una ruta válida.
3. [ ] `where link` devuelve al menos una ruta válida.
4. [ ] `npm install` se ejecuta correctamente en `desktop/`.
5. [ ] `npm run tauri` (en `desktop/`) ya no muestra `link.exe not found`.

## 6. Troubleshooting común

### 6.1 link.exe not found

Posibles causas:

- Falta el workload de C++ en Visual Studio Build Tools.
- Falta el Windows SDK.
- PATH no se actualizó en la sesión actual.

Solución:

1. Revisa que tengas instalado el workload **Desktop development with C++**.
2. Confirma que `where link` devuelve una ruta válida.
3. Cierra todas las terminales y vuelve a abrir una nueva.
4. Si usas `rustup`, confirma que el host es `x86_64-pc-windows-msvc`.

### 6.2 Mezcla de toolchains GNU y MSVC

Si previamente instalaste Rust con el target GNU, puedes limpiar y forzar MSVC:

```powershell
rustup uninstall stable-x86_64-pc-windows-gnu
rustup set default-host x86_64-pc-windows-msvc
rustup default stable
```

### 6.3 Problemas al compilar crates nativos

Algunos crates pueden requerir componentes adicionales (por ejemplo, bindings con C++/WinRT). En esos casos:

- Asegúrate de tener el SDK correcto (Windows 10/11).
- Actualiza Visual Studio Build Tools desde el instalador.
- Ejecuta de nuevo `npm run tauri` y revisa el mensaje de error concreto.


