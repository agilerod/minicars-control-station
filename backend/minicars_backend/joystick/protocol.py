"""
MiniCars Joystick Control Protocol.

Defines the message format for communication between laptop and Jetson.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class JoystickMessage:
    """
    Joystick control message.
    
    All values are normalized floats for consistency.
    """
    servo: float  # -1.0 to 1.0 (left to right)
    throttle: float  # 0.0 to 1.0
    brake: float  # 0.0 to 1.0
    handbrake: float  # 0.0 to 1.0 (typically 0 or 1)
    turbo: float  # 0.0 to 1.0 (typically 0 or 1)
    mode: str  # "kid", "normal", or "pro"
    
    def to_uart_format(self) -> str:
        """
        Convert to UART format for Arduino.
        
        Returns:
            String in format: "servo_angle,accel_pct,brake_pct,hbrake_flag,turbo_flag\n"
        """
        # Convert normalized values to Arduino format
        servo_angle = int((self.servo + 1.0) * 90.0)  # -1..1 → 0..180
        servo_angle = max(0, min(180, servo_angle))  # Clamp
        
        accel_pct = int(self.throttle * 100.0)  # 0..1 → 0..100
        brake_pct = int(self.brake * 100.0)
        hbrake_flag = 1 if self.handbrake > 0.5 else 0
        turbo_flag = 1 if self.turbo > 0.5 else 0
        
        return f"{servo_angle},{accel_pct},{brake_pct},{hbrake_flag},{turbo_flag}\n"


def format_message(msg: JoystickMessage) -> str:
    """
    Format a joystick message for TCP transmission.
    
    Args:
        msg: The joystick message
        
    Returns:
        Formatted string: "servo,throttle,brake,handbrake,turbo,mode\n"
    """
    return f"{msg.servo:.3f},{msg.throttle:.3f},{msg.brake:.3f},{msg.handbrake:.3f},{msg.turbo:.3f},{msg.mode}\n"


def parse_message(line: str) -> Optional[JoystickMessage]:
    """
    Parse a joystick message from TCP.
    
    Args:
        line: Raw line from TCP socket
        
    Returns:
        Parsed JoystickMessage or None if invalid
    """
    try:
        parts = line.strip().split(',')
        if len(parts) != 6:
            return None
        
        servo = float(parts[0])
        throttle = float(parts[1])
        brake = float(parts[2])
        handbrake = float(parts[3])
        turbo = float(parts[4])
        mode = parts[5]
        
        # Validate ranges
        if not (-1.0 <= servo <= 1.0):
            return None
        if not (0.0 <= throttle <= 1.0):
            return None
        if not (0.0 <= brake <= 1.0):
            return None
        if not (0.0 <= handbrake <= 1.0):
            return None
        if not (0.0 <= turbo <= 1.0):
            return None
        if mode not in ["kid", "normal", "sport"]:
            return None
        
        return JoystickMessage(
            servo=servo,
            throttle=throttle,
            brake=brake,
            handbrake=handbrake,
            turbo=turbo,
            mode=mode,
        )
    except (ValueError, IndexError):
        return None

