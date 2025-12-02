"""
Joystick Sender - Sends joystick commands to Jetson via TCP.

This module reads joystick input using pygame and sends control commands
to the Jetson Nano over TCP, applying driving profile curves and limits.
"""
import logging
import socket
import sys
import threading
import time
from typing import Optional

try:
    import pygame
except ImportError:
    print("ERROR: pygame not installed. Run: pip install pygame", file=sys.stderr)
    print("The joystick control system requires pygame to read joystick input.", file=sys.stderr)
    pygame = None  # type: ignore

from .profiles import get_driving_profile, DrivingMode
from .protocol import JoystickMessage, format_message
from ..control_profiles import load_profile

logger = logging.getLogger("minicars.joystick.sender")


class JoystickSender:
    """
    Manages joystick input and sends control commands to Jetson.
    
    Attributes:
        target_host: Hostname or IP of Jetson
        target_port: TCP port on Jetson
        send_hz: Frequency of sending commands (default 20Hz)
    """
    
    def __init__(
        self,
        target_host: str = "SKLNx.local",
        target_port: int = 5005,
        send_hz: int = 20,
    ):
        self.target_host = target_host
        self.target_port = target_port
        self.send_hz = send_hz
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._socket: Optional[socket.socket] = None
        
        # State for delta limiting
        self._last_throttle = 0.0
        self._last_servo = 0.0
        
    def start(self) -> None:
        """Start the joystick sender thread."""
        # Check if pygame is available
        if pygame is None:
            raise RuntimeError(
                "pygame is not installed. Install it with: pip install pygame"
            )
        
        if self._running:
            logger.warning("Joystick sender already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f"[joystick-sender] Started (target: {self.target_host}:{self.target_port})")
    
    def stop(self) -> None:
        """Stop the joystick sender thread."""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        
        # Send failsafe message before closing
        self._send_failsafe()
        
        if self._socket:
            try:
                self._socket.close()
            except:
                pass
        
        logger.info("[joystick-sender] Stopped")
    
    def _connect(self) -> bool:
        """
        Establish TCP connection to Jetson.
        
        Returns:
            True if connected successfully
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.target_host, self.target_port))
            logger.info(f"[joystick-sender] Connected to {self.target_host}:{self.target_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.target_host}:{self.target_port}: {e}")
            return False
    
    def _send_failsafe(self) -> None:
        """Send failsafe message (centered servo, no throttle, full brake)."""
        if not self._socket:
            return
        
        failsafe_msg = JoystickMessage(
            servo=0.0,
            throttle=0.0,
            brake=1.0,
            handbrake=0.0,
            turbo=0.0,
            mode="normal",
        )
        
        try:
            self._socket.sendall(format_message(failsafe_msg).encode("ascii"))
            logger.info("[joystick-sender] Sent failsafe message")
        except:
            pass
    
    def _run(self) -> None:
        """Main loop: read joystick and send commands."""
        # Initialize pygame and joystick
        pygame.init()
        pygame.joystick.init()
        
        if pygame.joystick.get_count() == 0:
            logger.error("No joystick detected")
            self._running = False
            return
        
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
        logger.info(f"Joystick: {joystick.get_name()}")
        
        # Connect to Jetson
        if not self._connect():
            self._running = False
            return
        
        # Main loop
        dt = 1.0 / self.send_hz
        next_send_time = time.perf_counter()
        
        turbo_mode = False
        prev_turbo_button = False
        
        while self._running:
            try:
                pygame.event.pump()
                
                # Read joystick axes (adjust indices as needed for your controller)
                servo_raw = joystick.get_axis(0)  # Steering
                throttle_raw = joystick.get_axis(2)  # Accelerator (often -1=pressed, 1=released)
                brake_raw = joystick.get_axis(3)  # Brake
                
                # Normalize pedals: -1=pressed → 1.0, +1=released → 0.0
                throttle_normalized = (-throttle_raw + 1.0) / 2.0
                brake_normalized = (-brake_raw + 1.0) / 2.0
                
                # Handbrake button (adjust index as needed)
                handbrake = 1.0 if joystick.get_button(5) else 0.0
                
                # Turbo toggle (adjust index as needed)
                turbo_button = joystick.get_button(6)
                if turbo_button and not prev_turbo_button:
                    turbo_mode = not turbo_mode
                    logger.info(f"Turbo mode: {'ON' if turbo_mode else 'OFF'}")
                prev_turbo_button = turbo_button
                
                # Get active driving profile
                profile_data = load_profile()
                active_mode = profile_data.get("active_mode", "normal")
                profile = get_driving_profile(active_mode)
                
                # Apply profile curves and limits
                throttle_curved = profile.apply_throttle_curve(throttle_normalized)
                throttle_limited = profile.limit_throttle_delta(self._last_throttle, throttle_curved, dt)
                
                servo_limited_range = profile.apply_servo_limit(servo_raw)
                servo_limited_delta = profile.limit_servo_delta(self._last_servo, servo_limited_range, dt)
                
                # Update state
                self._last_throttle = throttle_limited
                self._last_servo = servo_limited_delta
                
                # Create message
                msg = JoystickMessage(
                    servo=servo_limited_delta,
                    throttle=throttle_limited,
                    brake=brake_normalized,
                    handbrake=handbrake,
                    turbo=1.0 if turbo_mode else 0.0,
                    mode=active_mode,
                )
                
                # Send
                self._socket.sendall(format_message(msg).encode("ascii"))
                
                # Maintain frequency
                now = time.perf_counter()
                sleep_time = next_send_time - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                next_send_time += dt
                
            except OSError as e:
                logger.error(f"Connection lost: {e}. Reconnecting...")
                try:
                    self._socket.close()
                except:
                    pass
                time.sleep(2.0)
                if not self._connect():
                    break
            except Exception as e:
                logger.error(f"Error in sender loop: {e}", exc_info=True)
                break
        
        pygame.quit()

