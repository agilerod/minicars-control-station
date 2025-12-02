"""
Módulo para gestionar perfiles de control del vehículo (modos de conducción).

Persiste el perfil activo en un archivo JSON dentro de backend/config/control_profile.json.
"""
import json
from pathlib import Path

VALID_MODES = {"kid", "normal", "sport"}
DEFAULT_MODE = "normal"


def get_config_dir() -> Path:
    """
    Obtiene el directorio de configuración (backend/config).
    Si existe minicars_backend.config con BASE_DIR, lo usa.
    Si no, calcula a partir de este archivo.
    """
    try:
        from .config import BASE_DIR  # si ya existe
        base = Path(BASE_DIR)
    except (ImportError, AttributeError):
        # Calcular desde este archivo: backend/minicars_backend/control_profiles.py
        # Subir dos niveles: minicars_backend -> backend
        base = Path(__file__).resolve().parent.parent

    config_dir = base / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_profile_path() -> Path:
    """Devuelve la ruta completa al archivo de perfil de control."""
    return get_config_dir() / "control_profile.json"


def get_default_profile() -> dict:
    """Devuelve el perfil por defecto."""
    return {"active_mode": DEFAULT_MODE}


def load_profile() -> dict:
    """
    Carga el perfil de control desde el archivo JSON.
    Si el archivo no existe o hay un error, devuelve el perfil por defecto.
    """
    path = get_profile_path()
    if not path.exists():
        return get_default_profile()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        mode = data.get("active_mode", DEFAULT_MODE)
        if mode not in VALID_MODES:
            mode = DEFAULT_MODE
        return {"active_mode": mode}
    except Exception:
        # Ante cualquier problema, devolvemos el default
        return get_default_profile()


def validate_mode(mode: str) -> str:
    """
    Valida que el modo sea uno de los permitidos.
    Lanza ValueError si el modo no es válido.
    """
    if mode not in VALID_MODES:
        raise ValueError(
            f"Modo inválido: {mode}. Debe ser uno de {sorted(VALID_MODES)}"
        )
    return mode


def save_profile(profile: dict) -> dict:
    """
    Guarda el perfil de control en el archivo JSON.
    Valida el modo antes de guardar.
    """
    mode = validate_mode(profile.get("active_mode", DEFAULT_MODE))
    data = {"active_mode": mode}

    path = get_profile_path()
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


__all__ = ["VALID_MODES", "DEFAULT_MODE", "load_profile", "save_profile"]

