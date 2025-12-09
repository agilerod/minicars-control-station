"""
Throttle mapping logic from car_control_logi.py.

This module implements the exact throttle mapping algorithm used in car_control_logi.py,
including deadzone, exponential curves, and ramp rate limiting for smooth acceleration.
"""
from dataclasses import dataclass
from typing import Dict


@dataclass
class DrivingMode:
    """Driving mode configuration matching car_control_logi.py exactly."""
    id: str
    label: str
    max_throttle: float  # valor máximo [0..1] que se enviará al vehículo
    expo: float  # curva exponencial >1 = más suave al inicio
    deadzone: float  # umbral bajo el cual se considera 0
    ramp_rate: float  # cambio máximo por frame (0..1)


# Exact modes from car_control_logi.py
DRIVING_MODES: Dict[str, DrivingMode] = {
    "kid": DrivingMode(
        id="kid",
        label="Modo Niños",
        max_throttle=0.35,
        expo=2.2,
        deadzone=0.12,
        ramp_rate=0.05,
    ),
    "normal": DrivingMode(
        id="normal",
        label="Modo Normal",
        max_throttle=0.7,
        expo=1.8,
        deadzone=0.08,
        ramp_rate=0.08,
    ),
    "sport": DrivingMode(
        id="sport",
        label="Modo Sport",
        max_throttle=1.0,
        expo=1.3,
        deadzone=0.05,
        ramp_rate=0.15,
    ),
}

# Global state for ramp smoothing (per instance)
_current_throttle_state: Dict[str, float] = {}


def get_mode(mode_id: str) -> DrivingMode:
    """Get driving mode, defaulting to 'normal' if invalid."""
    mode = DRIVING_MODES.get(mode_id)
    if mode is None:
        mode = DRIVING_MODES["normal"]
    return mode


def _apply_deadzone(raw: float, deadzone: float) -> float:
    """Aplica deadzone: valores menores al umbral se consideran 0."""
    if abs(raw) < deadzone:
        return 0.0
    return raw


def _apply_expo(raw: float, expo: float) -> float:
    """Aplica curva exponencial: expo > 1 hace la curva más suave al inicio."""
    if raw <= 0.0:
        return 0.0
    return raw ** expo


def _apply_ramp(current: float, target: float, ramp_rate: float) -> float:
    """Aplica rampa suave para evitar cambios bruscos."""
    delta = target - current
    if abs(delta) <= ramp_rate:
        return target
    return current + ramp_rate * (1.0 if delta > 0 else -1.0)


def map_pedal_to_throttle(raw_value: float, mode: DrivingMode, state_key: str = "default") -> float:
    """
    Transforma el valor crudo del pedal en un throttle suave [0..1]
    aplicando: deadzone, curva expo, límite de modo y rampa.
    
    Exact implementation from car_control_logi.py.
    
    El raw_value viene del eje del joystick (típicamente -1 a +1, donde
    +1 = reposo y -1 = pisado al máximo).
    
    Args:
        raw_value: Raw axis value from joystick (-1.0 to +1.0)
        mode: Driving mode configuration
        state_key: Key for state storage (to allow multiple instances)
        
    Returns:
        Processed throttle value [0.0 to 1.0]
    """
    global _current_throttle_state
    
    # Initialize state if needed
    if state_key not in _current_throttle_state:
        _current_throttle_state[state_key] = 0.0
    
    # Convertir de rango joystick [-1..+1] a [0..1]
    # +1 (reposo) → 0.0, -1 (pisado) → 1.0
    raw = (1.0 - raw_value) / 2.0
    raw = max(0.0, min(1.0, raw))
    
    # Deadzone
    raw = _apply_deadzone(raw, mode.deadzone)
    
    # Normalizar después de deadzone (reescalar al rango completo)
    if raw > 0.0:
        raw = (raw - mode.deadzone) / (1.0 - mode.deadzone)
        raw = max(0.0, min(1.0, raw))
    
    # Curva exponencial
    curved = _apply_expo(raw, mode.expo)
    
    # Límite por modo
    target = curved * mode.max_throttle
    
    # Rampa suave (evita acelerones bruscos)
    current = _current_throttle_state[state_key]
    throttled = _apply_ramp(current, target, mode.ramp_rate)
    _current_throttle_state[state_key] = throttled
    
    # Clamp final por seguridad
    return max(0.0, min(1.0, throttled))


def percent_from_axis(axis_val: float, deadzone_pct: int = 5) -> int:
    """
    Fórmula original: (1 - val) * 100
    • Si reposo = +1  ⇒  0 %
    • Si pisado = -1  ⇒  200 %  (luego saturaremos a 100 %)
    Le aplicamos dead-zone y límite 0-100.
    """
    pct = int((1 - axis_val) * 100)
    if pct < deadzone_pct:
        return 0
    return 100 if pct > 100 else pct

