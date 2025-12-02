from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .settings import get_settings
from .commands.start_stream import start_stream
from .commands.start_car_control import start_car_control
from .commands.start_receiver import start_receiver
from .commands.stop_stream import stop_stream
from .commands.stop_car_control import stop_car_control
from .commands.stop_receiver import stop_receiver
from .process_registry import list_status
from .control_profiles import (
    load_profile,
    save_profile,
    VALID_MODES,
    DEFAULT_MODE,
)

settings = get_settings()

app = FastAPI()

origins = [
    "http://localhost:5173",  # Vite dev
    "http://127.0.0.1:5173",
    "tauri://localhost",  # Tauri prod
    "https://tauri.localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class ControlProfile(BaseModel):
    active_mode: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "minicars-control-station-backend",
        "backend_url": str(settings.public_backend_url),
        "env": settings.env,
    }


@app.get("/status")
def status():
    return list_status()


@app.post("/actions/start_stream")
def actions_start_stream():
    """
    Endpoint para lanzar el viewer de GStreamer en la laptop.
    """
    return start_stream()


@app.post("/actions/stop_stream")
def actions_stop_stream():
    """
    Endpoint para detener el viewer de GStreamer en la laptop.
    """
    return stop_stream()


@app.post("/actions/start_receiver")
def actions_start_receiver():
    """
    Endpoint para iniciar el receptor GStreamer en la laptop.
    """
    return start_receiver()


@app.post("/actions/stop_receiver")
def actions_stop_receiver():
    """
    Endpoint para detener el receptor GStreamer en la laptop.
    """
    return stop_receiver()


@app.post("/actions/start_car_control")
def actions_start_car_control():
    result = start_car_control()

    if result.get("status") == "ok":
        return result

    raise HTTPException(status_code=500, detail=result)


@app.post("/actions/stop_car_control")
def actions_stop_car_control():
    result = stop_car_control()

    if result.get("status") == "ok":
        return result

    raise HTTPException(status_code=500, detail=result)


@app.get("/control/profile", response_model=ControlProfile)
def get_control_profile() -> ControlProfile:
    """Obtiene el perfil de control actual (modo de conducción activo)."""
    data = load_profile()
    return ControlProfile(**data)


@app.post("/control/profile", response_model=ControlProfile)
def set_control_profile(profile: ControlProfile) -> ControlProfile:
    """Establece el perfil de control (modo de conducción)."""
    if profile.active_mode not in VALID_MODES:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Modo inválido",
                "allowed_modes": sorted(VALID_MODES),
                "received": profile.active_mode,
            },
        )
    saved = save_profile(profile.dict())
    return ControlProfile(**saved)


@app.post("/shutdown")
async def shutdown():
    """
    Graceful shutdown endpoint para cuando Tauri cierra la aplicación.
    
    Este endpoint permite que Tauri solicite un cierre limpio del backend
    antes de matar el proceso.
    """
    import signal
    import os
    from threading import Thread
    import time
    
    def delayed_shutdown():
        """Shutdown después de responder."""
        time.sleep(0.5)  # Dar tiempo para responder
        os.kill(os.getpid(), signal.SIGTERM)
    
    # Iniciar shutdown en thread separado
    Thread(target=delayed_shutdown, daemon=True).start()
    
    return {"status": "shutting down", "message": "Backend shutdown initiated"}


