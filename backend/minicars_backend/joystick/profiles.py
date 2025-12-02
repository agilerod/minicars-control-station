"""
Driving Mode Profiles for MiniCars.

Defines the behavior characteristics for each driving mode (kid, normal, pro).
"""
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class DrivingMode(str, Enum):
    """Available driving modes."""
    KID = "kid"
    NORMAL = "normal"
    SPORT = "sport"  # Aligned with control_profiles.py and UI


@dataclass
class DrivingProfile:
    """
    Driving profile configuration for a specific mode.
    
    Attributes:
        mode: The driving mode
        throttle_curve_exp: Exponent for throttle curve (1.0 = linear, >1.0 = progressive)
        max_throttle: Maximum throttle output (0.0 to 1.0)
        servo_limit: Maximum servo deflection (0.0 to 1.0, where 1.0 = full range)
        max_throttle_delta: Maximum throttle change per frame (0.0 to 1.0)
        max_servo_delta: Maximum servo change per frame (0.0 to 1.0)
        description: Human-readable description
    """
    mode: DrivingMode
    throttle_curve_exp: float
    max_throttle: float
    servo_limit: float
    max_throttle_delta: float
    max_servo_delta: float
    description: str
    
    def apply_throttle_curve(self, throttle_raw: float) -> float:
        """
        Apply the throttle curve and limits for this profile.
        
        Args:
            throttle_raw: Raw throttle input (0.0 to 1.0)
            
        Returns:
            Processed throttle value (0.0 to 1.0)
        """
        # Clamp input
        throttle = max(0.0, min(1.0, throttle_raw))
        
        # Apply curve
        throttle = throttle ** self.throttle_curve_exp
        
        # Apply max limit
        throttle = min(throttle, self.max_throttle)
        
        return throttle
    
    def limit_throttle_delta(self, current: float, target: float, dt: float = 0.05) -> float:
        """
        Limit the rate of throttle change.
        
        Args:
            current: Current throttle value
            target: Target throttle value
            dt: Time delta (default 0.05s for 20Hz)
            
        Returns:
            New throttle value with limited delta
        """
        max_change = self.max_throttle_delta * (dt / 0.05)  # Scale by actual dt
        delta = target - current
        
        if abs(delta) <= max_change:
            return target
        
        return current + (max_change if delta > 0 else -max_change)
    
    def apply_servo_limit(self, servo_raw: float) -> float:
        """
        Apply servo limits for this profile.
        
        Args:
            servo_raw: Raw servo input (-1.0 to 1.0)
            
        Returns:
            Limited servo value (-1.0 to 1.0)
        """
        # Clamp and apply limit
        servo = max(-1.0, min(1.0, servo_raw))
        servo = servo * self.servo_limit
        return servo
    
    def limit_servo_delta(self, current: float, target: float, dt: float = 0.05) -> float:
        """
        Limit the rate of servo change.
        
        Args:
            current: Current servo value
            target: Target servo value
            dt: Time delta (default 0.05s for 20Hz)
            
        Returns:
            New servo value with limited delta
        """
        max_change = self.max_servo_delta * (dt / 0.05)  # Scale by actual dt
        delta = target - current
        
        if abs(delta) <= max_change:
            return target
        
        return current + (max_change if delta > 0 else -max_change)


# Define the three driving profiles
DRIVING_PROFILES = {
    DrivingMode.KID: DrivingProfile(
        mode=DrivingMode.KID,
        throttle_curve_exp=2.0,  # Cuadrática suave
        max_throttle=0.40,  # 40% máximo
        servo_limit=0.60,  # ±60% de rango
        max_throttle_delta=0.05,  # 5% por frame
        max_servo_delta=0.10,  # 10% por frame
        description="Aceleración limitada, giros suavizados, ideal para niños",
    ),
    DrivingMode.NORMAL: DrivingProfile(
        mode=DrivingMode.NORMAL,
        throttle_curve_exp=1.2,  # Casi lineal
        max_throttle=0.75,  # 75% máximo
        servo_limit=0.85,  # ±85% de rango
        max_throttle_delta=0.15,  # 15% por frame
        max_servo_delta=0.25,  # 25% por frame
        description="Conducción equilibrada",
    ),
    DrivingMode.SPORT: DrivingProfile(
        mode=DrivingMode.SPORT,
        throttle_curve_exp=1.0,  # Lineal
        max_throttle=1.0,  # 100%
        servo_limit=1.0,  # 100%
        max_throttle_delta=0.5,  # Sin límite práctico
        max_servo_delta=0.5,  # Sin límite práctico
        description="Respuesta rápida y completa",
    ),
}


def get_driving_profile(mode: str | DrivingMode) -> DrivingProfile:
    """
    Get the driving profile for a given mode.
    
    Args:
        mode: The driving mode (string or DrivingMode enum)
        
    Returns:
        The corresponding DrivingProfile
        
    Raises:
        ValueError: If the mode is not recognized
    """
    if isinstance(mode, str):
        try:
            mode = DrivingMode(mode.lower())
        except ValueError:
            raise ValueError(f"Unknown driving mode: {mode}. Valid modes: {[m.value for m in DrivingMode]}")
    
    profile = DRIVING_PROFILES.get(mode)
    if profile is None:
        raise ValueError(f"No profile found for mode: {mode}")
    
    return profile

