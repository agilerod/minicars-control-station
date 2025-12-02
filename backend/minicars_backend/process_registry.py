from __future__ import annotations

import subprocess
from typing import Dict, Optional

ProcessesDict = Dict[str, subprocess.Popen]

processes: ProcessesDict = {}


def register_process(name: str, proc: subprocess.Popen) -> None:
    """
    Registra un proceso activo bajo un nombre conocido.
    Si ya existía un proceso para ese nombre, se sobrescribe.
    """
    processes[name] = proc


def get_process(name: str) -> Optional[subprocess.Popen]:
    """
    Obtiene sin modificar el proceso registrado para el nombre dado.
    """
    return processes.get(name)


def is_process_running(name: str) -> bool:
    """
    Determina si el proceso registrado sigue activo. Si detecta que ya
    terminó, limpia la entrada del registro y devuelve False.
    """
    proc = processes.get(name)
    if proc is None:
        return False

    if proc.poll() is None:
        return True

    # El proceso ya terminó; limpiar el registro.
    processes.pop(name, None)
    return False


def stop_process(name: str) -> dict:
    """
    Intenta detener el proceso registrado con el nombre dado.
    Maneja escenarios donde el proceso ya no existe o ya terminó.
    """
    proc = processes.get(name)
    if proc is None:
        return {
            "status": "error",
            "message": f"No hay proceso registrado para {name}.",
        }

    try:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=2)
        processes.pop(name, None)
        return {
            "status": "ok",
            "message": f"{name} detenido.",
        }
    except Exception as exc:  # pragma: no cover - difícil de reproducir
        processes.pop(name, None)
        return {
            "status": "error",
            "message": f"Error al detener {name}: {exc}",
        }


def list_status() -> dict:
    """
    Devuelve el estado de cada proceso conocido (running/stopped).
    """
    status = {}
    for name in ("stream", "car_control"):
        status[name] = "running" if is_process_running(name) else "stopped"
    return status


