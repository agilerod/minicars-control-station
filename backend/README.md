# Backend - minicars-control-station

Este es el backend inicial del proyecto **minicars-control-station**, basado en **FastAPI**.

## Entorno virtual (venv)

En Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

En Linux / macOS (bash/zsh):

```bash
python -m venv .venv
source .venv/bin/activate
```

## Instalación de dependencias

Con el entorno virtual activado:

```bash
pip install -r backend/requirements.txt
```

## Ejecutar el servidor de desarrollo

Desde la raíz del repositorio (donde está la carpeta `backend/`), con el entorno virtual activado:

```bash
uvicorn minicars_backend.api:app --reload
```

Por defecto el servidor se levantará en `http://127.0.0.1:8000`.

## Ejecutar los tests

Desde la raíz del repositorio, con el entorno virtual activado:

```bash
pytest
```


