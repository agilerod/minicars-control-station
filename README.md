# minicars-control-station

Dashboard local para controlar el stream de la Jetson Nano y el auto RC. Este repositorio contiene la estación de control (backend FastAPI, scripts de control y app de escritorio con Tauri) separada del código onboard del vehículo.

## Prerrequisitos

- Python 3.10+ (recomendado 3.11+)
- Node.js 18+ (npm o pnpm)
- Git + OpenSSH Client
- GStreamer para Windows (instalado en `C:\Program Files\gstreamer\1.0\mingw_x86_64\bin\`)
- Rust stable con target `x86_64-pc-windows-msvc` (solo para Tauri)
- Visual Studio Build Tools 2022 (workload C++ / Desktop development with C++) (solo para Tauri)

Para más detalle sobre requisitos de build en Windows (MSVC, SDKs, etc.), consulta `docs/windows-build-requirements.md`.

## Laptop Setup (Windows)

### 1. Instalación de dependencias

#### Python y entorno virtual

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

#### Node.js y dependencias del frontend

```powershell
cd desktop
npm install
```

#### GStreamer

1. Descarga GStreamer desde: https://gstreamer.freedesktop.org/download/
2. Instala la versión completa (Full installer) para Windows
3. Por defecto se instala en: `C:\Program Files\gstreamer\1.0\mingw_x86_64\bin\`
4. Verifica la instalación ejecutando:
   ```powershell
   & "C:\Program Files\gstreamer\1.0\mingw_x86_64\bin\gst-launch-1.0.exe" --version
   ```

### 2. Levantar el backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn minicars_backend.api:app --reload
```

El backend estará disponible en `http://127.0.0.1:8000`

### 3. Levantar el desktop (Tauri)

En una nueva terminal:

```powershell
cd desktop
npm run tauri:dev
```

O para build de producción:

```powershell
npm run tauri:build
```

### 4. Receptor GStreamer

El receptor GStreamer puede iniciarse de dos formas:

**Desde la API (recomendado):**
- Usa el botón "Start Stream" en la aplicación Tauri
- O llama al endpoint: `POST /actions/start_receiver`

**Manualmente:**
```powershell
cd backend
python start_receiver.py
```

O usando el script PowerShell:
```powershell
.\desktop\scripts\win\receiver_gstreamer.ps1 -Action start
```

## Configuración y entornos

El proyecto utiliza archivos `.env` para gestionar configuraciones y secretos de forma segura. Los archivos `.env` no se suben a git; solo se incluyen archivos `.env.example` como plantillas.

### Backend

El backend lee variables de entorno con prefijo `MINICARS_*` desde `backend/.env` en desarrollo.

1. Copia `backend/.env.example` a `backend/.env`:
   ```powershell
   cd backend
   copy .env.example .env
   ```

2. Edita `backend/.env` y ajusta los valores según tu entorno:
   - `MINICARS_ENV`: Entorno de ejecución (dev, prod, etc.)
   - `MINICARS_BACKEND_HOST`: Host donde se ejecuta el servidor (por defecto: 127.0.0.1)
   - `MINICARS_BACKEND_PORT`: Puerto del servidor (por defecto: 8000)
   - `MINICARS_PUBLIC_BACKEND_URL`: URL base pública del backend (usada por el frontend)
   - `MINICARS_JETSON_BASE_URL`: (Opcional) URL base del backend/control en la Jetson Nano. Se puede usar en el futuro para enviar comandos o consultar estado directamente a la Jetson cuando el código esté integrado.

### Desktop

La app desktop lee la variable de entorno `VITE_MINICARS_BACKEND_URL` desde `desktop/.env`.

1. Copia `desktop/.env.example` a `desktop/.env`:
   ```powershell
   cd desktop
   copy .env.example .env
   ```

2. Edita `desktop/.env` y ajusta la URL del backend si es necesario:
   - `VITE_MINICARS_BACKEND_URL`: URL base del backend FastAPI (por defecto: http://127.0.0.1:8000)

**Nota**: Los archivos `*.env` y `*.env.local` están configurados en `.gitignore` y no se suben a git. Solo se versionan los archivos `*.env.example`.

## Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn minicars_backend.api:app --reload
```

## Desktop (Tauri)

Instalación:

```powershell
cd desktop
npm install
```

Modo desarrollo (app de escritorio):

```powershell
npm run tauri:dev
```

Build de la app nativa (Tauri build):

```powershell
npm run tauri:build
```

## Configuración Git y GitHub

### Verificar conexión SSH a GitHub

```powershell
ssh -T git@github.com
```

Deberías ver un mensaje como: `Hi username! You've successfully authenticated...`

### Verificar remoto del repositorio

```powershell
git remote -v
```

Deberías ver algo como:
```
origin  git@github.com:tu-usuario/minicars-control-station.git (fetch)
origin  git@github.com:tu-usuario/minicars-control-station.git (push)
```

### Flujo de trabajo básico

```powershell
# Agregar cambios
git add .

# Commit con mensaje descriptivo
git commit -m "feat: stable Windows dev setup"

# Push a GitHub
git push origin main
```

### Sincronización con Jetson

Después de hacer push desde la laptop, en la Jetson:

```bash
cd /home/jetson-rod/minicars-jetson
git pull origin main
```

## Estructura del proyecto

```
minicars-control-station/
├── backend/
│   ├── minicars_backend/
│   │   ├── commands/          # Comandos para GStreamer y control
│   │   ├── utils/             # Utilidades (check_gstreamer, etc.)
│   │   ├── api.py             # API FastAPI principal
│   │   └── settings.py        # Configuración centralizada
│   ├── start_receiver.py      # Script standalone para receptor
│   ├── requirements.txt
│   └── .env.example
├── desktop/
│   ├── src/                   # React + TypeScript
│   ├── src-tauri/             # Tauri wrapper
│   ├── scripts/
│   │   └── win/               # Scripts PowerShell para Windows
│   └── package.json
├── jetson/                    # Scripts para Jetson Nano
│   ├── start_streamer.py
│   └── minicars-streamer.service
├── docs/                      # Documentación adicional
└── scripts/                   # Utilidades de desarrollo
```

- `backend/`: API FastAPI, comandos para GStreamer/PowerShell y control del vehículo, tests con pytest.
- `desktop/`: SPA React + Vite + TypeScript y wrapper Tauri (`src-tauri/`) para la app de escritorio.
- `jetson/`: Scripts y configuración para el lado Jetson (streamer).
- `docs/`: documentación adicional (por ejemplo, requisitos de build en Windows).
- `scripts/`: utilidades como chequeos de entorno para Windows.
