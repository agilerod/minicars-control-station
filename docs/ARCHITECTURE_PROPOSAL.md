# 🏗️ MiniCars Control Station - Propuesta de Arquitectura para Windows

**Fecha**: 2025-12-02  
**Autor**: Software Architect + Pair Programmer  
**Objetivo**: Convertir en aplicación de escritorio profesional sin dependencia de terminal

---

## 📊 FASE 1: ANÁLISIS DEL ESTADO ACTUAL

### Estructura Actual del Repositorio

```
minicars-control-station/
├── backend/                      # FastAPI backend (Python)
│   ├── minicars_backend/
│   │   ├── api.py               # Entrypoint FastAPI
│   │   ├── settings.py          # Config centralizada
│   │   ├── commands/            # Start/stop actions
│   │   ├── joystick/            # Sistema joystick (kid/normal/sport)
│   │   └── utils/               # GStreamer check, etc.
│   ├── requirements.txt         # 6 deps (FastAPI, pygame, etc.)
│   ├── .env.example
│   └── tests/
├── desktop/                      # Tauri + Vite + React
│   ├── src/                     # React/TypeScript UI
│   ├── src-tauri/
│   │   ├── src/main.rs          # Tauri entrypoint (BÁSICO)
│   │   ├── Cargo.toml
│   │   └── tauri.conf.json      # Config Tauri
│   ├── package.json             # npm scripts
│   └── vite.config.ts
├── jetson/                       # Scripts Linux (Jetson Nano)
├── .github/workflows/ci.yml     # CI/CD (parcial)
└── deploy_to_jetson.sh
```

### Flujo Actual en Windows (Desarrollo)

**Usuario tiene que ejecutar manualmente**:

```powershell
# Terminal 1: Backend
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn minicars_backend.api:app --reload

# Terminal 2: Desktop
cd desktop
npm run tauri:dev
```

**Arquitectura runtime actual**:
```
┌─────────────────┐         HTTP          ┌──────────────────┐
│ Tauri Desktop   │──────────────────────→│  FastAPI Backend │
│ (React + Vite)  │   localhost:8000      │  (Python/uvicorn)│
│                 │←──────────────────────│                  │
│ Port: 5173 (dev)│       JSON API        │  Port: 8000      │
└─────────────────┘                       └──────────────────┘
        │                                          │
        │                                          ├→ GStreamer (subprocess)
        │                                          ├→ JoystickSender (pygame)
        │                                          └→ TCP to Jetson (SKLNx.local:5005)
```

### Dependencias Críticas del Backend

1. **FastAPI/uvicorn** - Servidor HTTP
2. **pygame** - Lectura de joystick
3. **subprocess** - Lanzar GStreamer
4. **socket** - TCP a Jetson
5. **Python 3.10+** - Runtime

### Problemas Identificados

| # | Problema | Impacto | Severidad |
|---|----------|---------|-----------|
| 1 | Requiere 2 terminales manuales | Experiencia de usuario pobre | 🔴 ALTA |
| 2 | Backend no empaquetado | No distribuible | 🔴 ALTA |
| 3 | Tauri main.rs vacío | No gestiona backend | 🔴 ALTA |
| 4 | CI solo hace lint | No genera instaladores | 🟡 MEDIA |
| 5 | Sin instalador .msi/.exe | Usuario debe saber npm/Python | 🔴 ALTA |
| 6 | CORS apunta a :5173 (dev) | No funcionará en producción | 🟡 MEDIA |

---

## 🎯 ESTRATEGIAS EVALUADAS

### Opción A: Tauri Lanza Backend Empaquetado ⭐ **RECOMENDADA**

**Arquitectura**:
```
┌────────────────────────────────────────────────┐
│ MiniCars Control Station.exe (Tauri)           │
├────────────────────────────────────────────────┤
│ Tauri (Rust)                                   │
│   ├─ Al iniciar: spawn backend.exe             │
│   ├─ Monitorea backend (health check)          │
│   ├─ Al cerrar: kill backend.exe               │
│   └─ Gestiona errores                          │
├────────────────────────────────────────────────┤
│ WebView (React UI)                             │
│   └─ Conecta a http://localhost:8000           │
└────────────────────────────────────────────────┘
                  ↓ subprocess
┌────────────────────────────────────────────────┐
│ backend.exe (PyInstaller)                      │
│   ├─ FastAPI + uvicorn embebidos              │
│   ├─ pygame incluido                           │
│   ├─ Todas las deps bundled                    │
│   └─ Puerto 8000                               │
└────────────────────────────────────────────────┘
```

**PROs**:
- ✅ Un solo ejecutable para instalar (Tauri maneja todo)
- ✅ Backend completamente portátil (PyInstaller bundle)
- ✅ Shutdown limpio garantizado (Tauri mata proceso hijo)
- ✅ Health check automático (Tauri puede reiniciar si falla)
- ✅ Experiencia usuario: doble-click → todo funciona
- ✅ Actualizaciones: Tauri updater built-in
- ✅ Baja latencia: localhost, sin overhead
- ✅ Coherente con stack actual (Tauri ya existe)

**CONs**:
- ⚠️ PyInstaller puede ser grande (~50-80 MB con deps)
- ⚠️ Requiere build pipeline para backend.exe
- ⚠️ Debugging ligeramente más complejo (2 procesos)

**Complejidad**: 🟡 Media (worth it)

---

### Opción B: Backend como Servicio Windows

**Arquitectura**:
```
┌───────────────────┐            ┌──────────────────────┐
│ MiniCars.exe      │───HTTP────→│ MiniCars Backend Svc │
│ (Tauri)           │            │ (Windows Service)    │
└───────────────────┘            └──────────────────────┘
   Instalador 1                     Instalador 2
```

**PROs**:
- ✅ Backend corre siempre (como servicio)
- ✅ Separación clara UI/Backend

**CONs**:
- ❌ Requiere 2 instaladores separados
- ❌ Complejidad de Windows Services
- ❌ Actualizaciones más complejas
- ❌ Usuario puede confundirse (¿cuál instalar primero?)
- ❌ Overkill para una app local
- ❌ Mayor fricción

**Complejidad**: 🔴 Alta

**Recomendación**: ❌ NO - Too complex para este use case

---

### Opción C: Launcher Separado

**Arquitectura**:
```
launcher.exe  →  inicia backend.exe  →  abre MiniCars.exe
```

**PROs**:
- ✅ Lógica simple

**CONs**:
- ❌ 3 ejecutables separados
- ❌ Más difícil de mantener
- ❌ Experiencia de usuario fragmentada
- ❌ Actualizaciones complejas

**Complejidad**: 🟡 Media-Alta

**Recomendación**: ❌ NO - Opción A es superior

---

## ⭐ ESTRATEGIA RECOMENDADA: Opción A

**Tauri como proceso principal que gestiona backend empaquetado**

### Justificación Técnica

1. **Baja Latencia** ✅
   - Comunicación localhost (loopback)
   - Sin overhead de IPC complejo
   - Uvicorn en modo producción

2. **Experiencia de Usuario** ✅
   - Un solo .exe/.msi para instalar
   - Doble-click → funciona
   - Auto-updates con Tauri updater

3. **Mantenibilidad** ✅
   - Stack coherente (ya tienes Tauri)
   - CI/CD unificado
   - Un solo instalador

4. **Robustez** ✅
   - Tauri controla ciclo de vida del backend
   - Health checks automáticos
   - Shutdown limpio

5. **Distribuibilidad** ✅
   - PyInstaller bundle completo (sin Python externo)
   - Tauri genera instaladores NSIS
   - GitHub Releases para distribución

---

## 🏗️ ARQUITECTURA PROPUESTA DETALLADA

### Runtime Architecture

```
MiniCars Control Station.exe
│
├─ Tauri Process (Rust)
│   ├─ startup()
│   │   ├─ Check if backend.exe exists in bundle
│   │   ├─ Spawn backend.exe as child process
│   │   ├─ Wait for health check (http://localhost:8000/health)
│   │   ├─ Retry logic (max 3 attempts, 1s cada uno)
│   │   └─ Load WebView if backend OK
│   │
│   ├─ runtime()
│   │   ├─ Monitor backend process (cada 5s)
│   │   ├─ Restart si muere inesperadamente
│   │   └─ Log errors
│   │
│   └─ shutdown()
│       ├─ POST http://localhost:8000/shutdown (graceful)
│       ├─ Wait 2s
│       ├─ Kill backend process si no terminó
│       └─ Exit
│
├─ WebView (Chromium)
│   └─ React App
│       ├─ API calls a http://localhost:8000
│       ├─ Driving mode selector
│       ├─ Stream controls
│       └─ Joystick controls
│
└─ Bundled Resources
    ├─ backend/backend.exe (PyInstaller)
    ├─ frontend/ (Vite build)
    └─ assets/
```

### Backend Empaquetado (PyInstaller)

```
backend.exe (generado con PyInstaller)
│
├─ Python 3.11 runtime (embebido)
├─ FastAPI + uvicorn
├─ pygame (para joystick)
├─ pydantic-settings
├─ Todas las deps de requirements.txt
├─ minicars_backend/ (código completo)
└─ config/ (control_profile.json)

Tamaño estimado: ~60-80 MB
Inicio: <2 segundos en SSD
```

### Build Artifacts

```
Desarrollo:
- backend/ (código Python)
- desktop/ (código TypeScript)

Build (local o CI):
- backend/dist/backend.exe         (PyInstaller)
- desktop/dist/ (Vite build)        (HTML/JS/CSS)
- desktop/src-tauri/target/release/ (Tauri compilado)

Distribución (GitHub Releases):
- MiniCars-Control-Station_0.1.0_x64-setup.exe  (Instalador NSIS)
- MiniCars-Control-Station_0.1.0_x64.msi        (Instalador MSI)
```

---

## 📁 ESTRUCTURA DE CARPETAS PROPUESTA

```
minicars-control-station/
├── backend/
│   ├── minicars_backend/        # Código fuente
│   ├── requirements.txt
│   ├── requirements-dev.txt     # NUEVO (pytest, etc.)
│   ├── build.py                 # NUEVO - Script PyInstaller
│   ├── backend.spec             # NUEVO - PyInstaller spec
│   └── dist/                    # NUEVO - Output (gitignored)
│       └── backend.exe          # PyInstaller output
│
├── desktop/
│   ├── src/                     # React/TS código
│   ├── src-tauri/
│   │   ├── src/
│   │   │   ├── main.rs          # MODIFICAR - Backend lifecycle
│   │   │   ├── backend.rs       # NUEVO - Backend manager
│   │   │   └── lib.rs           # NUEVO - Utils
│   │   ├── Cargo.toml
│   │   └── tauri.conf.json      # MODIFICAR - Bundle backend.exe
│   ├── dist/                    # Vite build output (gitignored)
│   └── package.json
│
├── .github/workflows/
│   ├── ci.yml                   # MODIFICAR - Tests
│   ├── build-windows.yml        # NUEVO - Build completo
│   └── release.yml              # NUEVO - GitHub Releases
│
├── .gitignore                   # VERIFICAR
├── README.md                    # ACTUALIZAR
└── docs/
    ├── DEVELOPMENT.md           # NUEVO - Dev guide
    └── USER_GUIDE.md            # NUEVO - User manual
```

---

## 🔧 PLAN DE IMPLEMENTACIÓN (7 Pasos)

### PASO 1: Limpieza y .gitignore ✅ (Ya hecho parcialmente)

**Objetivo**: Asegurar que no se suban binarios

**Archivos a modificar**:
- `.gitignore`

**Acciones**:
- ✅ Verificar que `target/`, `dist/`, `node_modules/`, `__pycache__/` están ignorados
- ✅ Agregar `backend/dist/`, `backend/build/`
- ✅ Verificar con `git status --ignored`

**Validación**:
```bash
git status --ignored | grep target
# No debe aparecer nada
```

---

### PASO 2: Empaquetar Backend con PyInstaller

**Objetivo**: Crear `backend.exe` standalone

**Archivos a crear**:

#### `backend/build.py`
```python
"""
Build script para empaquetar backend con PyInstaller.
Genera backend.exe con todas las dependencias embebidas.
"""
import PyInstaller.__main__
import shutil
from pathlib import Path

# Configuración
ENTRY_POINT = "minicars_backend/api.py"
OUTPUT_NAME = "backend"
ICON_PATH = None  # Opcional: "../desktop/src-tauri/icons/icon.ico"

def build():
    args = [
        ENTRY_POINT,
        '--name', OUTPUT_NAME,
        '--onefile',
        '--noconfirm',
        '--clean',
        # Incluir dependencias críticas
        '--hidden-import', 'uvicorn',
        '--hidden-import', 'uvicorn.logging',
        '--hidden-import', 'uvicorn.loops',
        '--hidden-import', 'uvicorn.loops.auto',
        '--hidden-import', 'uvicorn.protocols',
        '--hidden-import', 'uvicorn.protocols.http',
        '--hidden-import', 'uvicorn.protocols.http.auto',
        '--hidden-import', 'uvicorn.lifespan',
        '--hidden-import', 'uvicorn.lifespan.on',
        '--hidden-import', 'pygame',
        # Agregar datos
        '--add-data', 'config;config',
        # Console para logs (cambiar a --noconsole en producción)
        '--console',
    ]
    
    if ICON_PATH and Path(ICON_PATH).exists():
        args.extend(['--icon', ICON_PATH])
    
    PyInstaller.__main__.run(args)
    print("✓ Backend empaquetado en dist/backend.exe")

if __name__ == "__main__":
    build()
```

#### `backend/requirements-dev.txt`
```
pyinstaller>=6.0.0
-r requirements.txt
```

**Comandos de build**:
```powershell
cd backend
pip install -r requirements-dev.txt
python build.py
# Output: dist/backend.exe
```

**Validación**:
```powershell
# Test standalone
.\dist\backend.exe
# Debe iniciar uvicorn en puerto 8000
```

**Tamaño estimado**: 60-80 MB (todo embebido)

---

### PASO 3: Integrar Backend en Tauri

**Objetivo**: Tauri gestiona ciclo de vida del backend

**Archivos a modificar/crear**:

#### `desktop/src-tauri/src/backend.rs` (NUEVO)

```rust
use std::process::{Child, Command};
use std::thread;
use std::time::Duration;
use tauri::Manager;

pub struct BackendManager {
    process: Option<Child>,
    port: u16,
}

impl BackendManager {
    pub fn new(port: u16) -> Self {
        BackendManager {
            process: None,
            port,
        }
    }
    
    /// Inicia el backend y espera a que esté listo
    pub fn start(&mut self, backend_path: &str) -> Result<(), String> {
        println!("[Backend] Starting backend from: {}", backend_path);
        
        let child = Command::new(backend_path)
            .env("MINICARS_BACKEND_PORT", self.port.to_string())
            .env("MINICARS_ENV", "production")
            .spawn()
            .map_err(|e| format!("Failed to start backend: {}", e))?;
        
        self.process = Some(child);
        
        // Esperar a que el backend esté listo
        for attempt in 1..=10 {
            thread::sleep(Duration::from_millis(500));
            
            if self.health_check() {
                println!("[Backend] Ready after {} attempts", attempt);
                return Ok(());
            }
        }
        
        Err("Backend failed to start (health check timeout)".to_string())
    }
    
    /// Health check HTTP
    fn health_check(&self) -> bool {
        match reqwest::blocking::get(format!("http://localhost:{}/health", self.port)) {
            Ok(response) => response.status().is_success(),
            Err(_) => false,
        }
    }
    
    /// Detiene el backend de forma limpia
    pub fn stop(&mut self) {
        if let Some(mut child) = self.process.take() {
            println!("[Backend] Stopping backend...");
            
            // Intento graceful shutdown
            let _ = reqwest::blocking::post(format!("http://localhost:{}/shutdown", self.port));
            thread::sleep(Duration::from_secs(2));
            
            // Si no terminó, kill
            let _ = child.kill();
            let _ = child.wait();
            
            println!("[Backend] Stopped");
        }
    }
}

impl Drop for BackendManager {
    fn drop(&mut self) {
        self.stop();
    }
}
```

#### `desktop/src-tauri/src/main.rs` (MODIFICAR)

```rust
#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod backend;

use backend::BackendManager;
use std::sync::Mutex;
use tauri::{Manager, State};

struct AppState {
    backend: Mutex<BackendManager>,
}

#[tauri::command]
fn backend_status(state: State<AppState>) -> Result<String, String> {
    Ok("Backend running".to_string())
}

fn main() {
    // Detectar path del backend.exe
    let backend_exe = if cfg!(debug_assertions) {
        // Modo desarrollo: asumir backend corriendo externamente
        None
    } else {
        // Modo producción: backend.exe bundled
        let exe_dir = std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|p| p.to_path_buf()));
        
        exe_dir.map(|dir| dir.join("backend.exe"))
    };
    
    let mut backend_manager = BackendManager::new(8000);
    
    // Iniciar backend si está en modo producción
    if let Some(backend_path) = backend_exe {
        if backend_path.exists() {
            if let Err(e) = backend_manager.start(backend_path.to_str().unwrap()) {
                eprintln!("Failed to start backend: {}", e);
                // Mostrar error al usuario
            }
        }
    }
    
    tauri::Builder::default()
        .manage(AppState {
            backend: Mutex::new(backend_manager),
        })
        .invoke_handler(tauri::generate_handler![backend_status])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

#### `desktop/src-tauri/Cargo.toml` (AGREGAR DEPS)

```toml
[dependencies]
tauri = { version = "1.6", features = ["shell-open"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
reqwest = { version = "0.11", features = ["blocking"] }  # NUEVO - health check
```

#### `desktop/src-tauri/tauri.conf.json` (MODIFICAR)

```json
{
  "build": {
    "beforeBuildCommand": "npm run build",
    "beforeDevCommand": "npm run dev",
    "devPath": "http://localhost:5173",
    "distDir": "../dist"
  },
  "package": {
    "productName": "MiniCars Control Station",
    "version": "0.1.0"
  },
  "tauri": {
    "bundle": {
      "identifier": "com.minicars.controlstation",
      "icon": ["icons/icon.ico"],
      "targets": ["nsis", "msi"],
      "resources": [
        "../../backend/dist/backend.exe"
      ],
      "windows": {
        "webviewInstallMode": {
          "type": "embedBootstrapper"
        }
      }
    },
    "allowlist": {
      "shell": {
        "open": true
      }
    },
    "windows": [
      {
        "title": "MiniCars Control Station",
        "width": 1200,
        "height": 800,
        "resizable": true
      }
    ]
  }
}
```

---

### PASO 4: Agregar Endpoint de Shutdown en Backend

**Archivo**: `backend/minicars_backend/api.py`

```python
@app.post("/shutdown")
async def shutdown():
    """Graceful shutdown para cuando Tauri cierra."""
    import signal
    import os
    
    # Dar tiempo para responder
    def delayed_shutdown():
        import time
        time.sleep(1)
        os.kill(os.getpid(), signal.SIGTERM)
    
    from threading import Thread
    Thread(target=delayed_shutdown, daemon=True).start()
    
    return {"status": "shutting down"}
```

---

### PASO 5: GitHub Actions Workflows

#### `.github/workflows/build-windows.yml` (NUEVO)

```yaml
name: Build Windows Release

on:
  push:
    branches: [main]
    tags: ['v*']
  workflow_dispatch:

jobs:
  build-backend:
    name: Build Backend (PyInstaller)
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements-dev.txt
      
      - name: Build backend.exe
        run: |
          cd backend
          python build.py
      
      - name: Upload backend.exe
        uses: actions/upload-artifact@v4
        with:
          name: backend-exe
          path: backend/dist/backend.exe
          retention-days: 7
  
  build-tauri:
    name: Build Tauri App
    needs: build-backend
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: desktop/package-lock.json
      
      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
      
      - name: Rust cache
        uses: Swatinem/rust-cache@v2
        with:
          workspaces: desktop/src-tauri
      
      - name: Download backend.exe
        uses: actions/download-artifact@v4
        with:
          name: backend-exe
          path: backend/dist
      
      - name: Install frontend dependencies
        run: |
          cd desktop
          npm ci
      
      - name: Build Tauri app
        run: |
          cd desktop
          npm run tauri:build
      
      - name: Upload installers
        uses: actions/upload-artifact@v4
        with:
          name: minicars-installers
          path: |
            desktop/src-tauri/target/release/bundle/nsis/*.exe
            desktop/src-tauri/target/release/bundle/msi/*.msi
```

#### `.github/workflows/release.yml` (NUEVO)

```yaml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  create-release:
    runs-on: windows-latest
    steps:
      # Trigger build-windows workflow
      # Upload to GitHub Releases
      # (Implementation details...)
```

---

### PASO 6: Configuración para Dev vs Prod

#### Backend - Detectar modo

```python
# settings.py
env: str = "dev"  # Ya existe

# api.py - CORS dinámico
origins = [
    "http://localhost:5173",  # Vite dev
    "http://127.0.0.1:5173",
    "tauri://localhost",      # Tauri prod
    "https://tauri.localhost",
]
```

#### Frontend - API URL dinámica

```typescript
// src/api/client.ts (ya existe)
const DEFAULT_BASE_URL = "http://127.0.0.1:8000";

function getBaseUrl(): string {
  const envUrl = import.meta.env.VITE_MINICARS_BACKEND_URL;
  return envUrl || DEFAULT_BASE_URL;
}
```

**Producción**: Hardcoded a `http://localhost:8000` (backend siempre local)

---

### PASO 7: Documentación

#### `README.md` - Actualizar secciones

```markdown
## Para Desarrolladores

### Modo Desarrollo
1. Terminal 1: `cd backend && uvicorn minicars_backend.api:app --reload`
2. Terminal 2: `cd desktop && npm run tauri:dev`

### Build Local
```powershell
# Backend
cd backend && python build.py

# Desktop + Backend bundled
cd desktop && npm run tauri:build
```

## Para Usuarios Finales

### Instalación
1. Descargar de [GitHub Releases](https://github.com/agilerod/minicars-control-station/releases)
2. Ejecutar `MiniCars-Control-Station_x64-setup.exe`
3. Seguir el wizard
4. Doble-click en el ícono de escritorio

### Uso
- Abrir "MiniCars Control Station"
- Backend se inicia automáticamente
- Seleccionar modo de conducción
- Start Stream / Car Control

### Requisitos
- Windows 10/11 (64-bit)
- GStreamer (para video)
- Joystick/Volante USB
```

---

## 📊 COMPARACIÓN DE ESFUERZO

| Tarea | Tiempo Estimado | Complejidad |
|-------|-----------------|-------------|
| Paso 1: .gitignore | 15 min | 🟢 Baja |
| Paso 2: PyInstaller setup | 1-2 horas | 🟡 Media |
| Paso 3: Tauri backend manager | 2-3 horas | 🟡 Media |
| Paso 4: Endpoint shutdown | 15 min | 🟢 Baja |
| Paso 5: GitHub Actions | 1-2 horas | 🟡 Media |
| Paso 6: Config dev/prod | 30 min | 🟢 Baja |
| Paso 7: Docs | 1 hora | 🟢 Baja |
| **TOTAL** | **6-10 horas** | 🟡 Media |

---

## 🎯 BENEFICIOS ESPERADOS

### Para el Usuario Final
- ✅ Instalador profesional (.msi/.exe)
- ✅ Un solo click para abrir la app
- ✅ Backend se inicia automáticamente
- ✅ Shutdown limpio
- ✅ Auto-updates posibles (Tauri updater)

### Para el Desarrollador
- ✅ Modo dev sin cambios (2 terminales)
- ✅ Build automatizado (GitHub Actions)
- ✅ Releases en GitHub
- ✅ CI/CD robusto

### Para el Proyecto
- ✅ Profesional y distribuible
- ✅ Mantenible
- ✅ Sin dependencias externas para usuario final
- ✅ Baja latencia (localhost)

---

## ⚠️ RIESGOS Y MITIGACIONES

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| PyInstaller falla con pygame | Media | Alto | Testing exhaustivo, alternativa: cx_Freeze |
| Backend.exe grande | Alta | Bajo | Acceptable (60-80MB es normal) |
| Antivirus bloquea .exe | Media | Alto | Code signing (opcional), documentar |
| Puerto 8000 ocupado | Baja | Medio | Retry con puertos 8001-8010 |

---

## 📝 DECISIONES CLAVE

### ¿Por qué PyInstaller?
- ✅ Más maduro que alternativas
- ✅ Soporta uvicorn/FastAPI bien
- ✅ Onefile mode = distribución simple
- ✅ Comunidad grande

**Alternativas consideradas**:
- cx_Freeze: Menos soporte para FastAPI
- Nuitka: Compilación lenta
- py2exe: Desactualizado

### ¿Por qué Tauri gestiona backend?
- ✅ Control total del ciclo de vida
- ✅ Health monitoring
- ✅ Restart automático
- ✅ Un solo instalador

### ¿Por qué NSIS + MSI?
- ✅ NSIS: Instalador moderno con UI
- ✅ MSI: Empresas/IT departments
- ✅ Tauri genera ambos automáticamente

---

## ✅ PRÓXIMOS PASOS

**DECISIÓN REQUERIDA**:

¿Apruebas esta arquitectura (Opción A con Tauri + PyInstaller)?

Si SÍ → Procedo a implementar los 7 pasos en orden.

Si prefieres ajustes → Dime qué modificar y ajusto el plan.

**Plan de trabajo propuesto**:
1. Implementar Pasos 1-4 (core functionality)
2. Testing local
3. Implementar Pasos 5-7 (CI/CD y docs)
4. Testing end-to-end
5. Primera release

**Tiempo estimado total**: 1-2 días de trabajo

---

**¿Procedo con la implementación de la Opción A?**

