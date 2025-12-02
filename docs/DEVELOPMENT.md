# 🛠️ MiniCars Control Station - Development Guide

## Modo Desarrollo (2 Terminales)

### Terminal 1: Backend
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn minicars_backend.api:app --reload
```

### Terminal 2: Desktop
```powershell
cd desktop
npm install
npm run tauri:dev
```

---

## 🏗️ Build para Producción (Windows)

### Build Backend
```powershell
cd backend
pip install -r requirements-dev.txt
python build.py
```

**Output**: `backend/dist/backend.exe` (~60-80 MB)

**Test standalone**:
```powershell
.\dist\backend.exe
# Visitar: http://localhost:8000/health
# Debe responder: {"status": "ok", ...}
```

### Build Desktop (con backend bundled)
```powershell
cd desktop
npm run tauri:build
```

**Output**:
- `desktop/src-tauri/target/release/bundle/nsis/MiniCars Control Station_0.1.0_x64-setup.exe`
- `desktop/src-tauri/target/release/bundle/msi/MiniCars Control Station_0.1.0_x64_en-US.msi`

---

## 🧪 Testing Local

### Backend standalone:
```powershell
cd backend
.\dist\backend.exe
# En otro terminal:
curl http://localhost:8000/health
```

### App completa:
```powershell
cd desktop/src-tauri/target/release
.\minicars-control-station.exe
# Backend debe iniciarse automáticamente
```

---

## 📦 Artifacts en GitHub Actions

Los workflows generan instaladores automáticamente.

**Descargar**:
1. Ve a: https://github.com/agilerod/minicars-control-station/actions
2. Click en el workflow más reciente
3. Scroll abajo → Artifacts
4. Descargar: `minicars-installer-nsis` o `minicars-installer-msi`

