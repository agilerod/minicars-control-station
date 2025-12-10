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
from .protocol import JoystickMessage
from .throttle_mapper import get_mode, map_pedal_to_throttle, percent_from_axis
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
        
        # State for throttle mapper (uses ramp rate internally)
        self._throttle_state_key = f"sender_{id(self)}"
        
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
            # Set timeout for connection attempt
            self._socket.settimeout(5.0)
            self._socket.connect((self.target_host, self.target_port))
            # Remove timeout after connection (for blocking sends)
            self._socket.settimeout(None)
            logger.info(f"[joystick-sender] Connected to {self.target_host}:{self.target_port}")
            return True
        except socket.timeout:
            logger.error(f"[joystick-sender] Connection timeout to {self.target_host}:{self.target_port}")
            return False
        except socket.gaierror as e:
            logger.error(f"[joystick-sender] DNS resolution failed for {self.target_host}: {e}")
            logger.error(f"[joystick-sender] Hint: Check if Jetson IP/hostname is correct. Try using IP address instead of hostname.")
            return False
        except ConnectionRefusedError:
            logger.error(f"[joystick-sender] Connection refused by {self.target_host}:{self.target_port}")
            logger.error(f"[joystick-sender] Hint: Ensure Jetson receiver is running and listening on port {self.target_port}")
            return False
        except Exception as e:
            logger.error(f"[joystick-sender] Failed to connect to {self.target_host}:{self.target_port}: {e}")
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
            # Use TCP format (6-field) that bridge expects
            self._socket.sendall(failsafe_msg.to_tcp_format().encode("ascii"))
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
            logger.error("[joystick-sender] Failed to establish initial connection. Thread exiting.")
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
                
                # Read joystick axes - EXACT match with car_control_logi.py
                # car_control_logi.py uses: AXIS_STEER=0, AXIS_ACCEL=1, AXIS_BRAKE=2, AXIS_HBRAKE=3
                steer_raw = joystick.get_axis(0)  # Steering (axis 0)
                accel_raw = joystick.get_axis(1)  # Accelerator (axis 1)
                brake_raw = joystick.get_axis(2)  # Brake (axis 2)
                hbrake_raw = joystick.get_axis(3)  # Handbrake (axis 3)
                
                # Turbo toggle - EXACT match with car_control_logi.py (BUTTON_TURBO=10)
                turbo_pressed = joystick.get_button(10)
                if turbo_pressed and not prev_turbo_button:
                    turbo_mode = not turbo_mode
                    logger.info(f"Turbo mode: {'ON' if turbo_mode else 'OFF'}")
                prev_turbo_button = turbo_pressed
                
                # Get active driving mode
                profile_data = load_profile()
                active_mode = profile_data.get("active_mode", "normal")
                mode = get_mode(active_mode)
                
                # Servo conversion - EXACT match with car_control_logi.py
                # servo_angle = int((steer_raw + 1) * 90)  # 0-180
                # But we send normalized -1.0 to 1.0, so keep raw for now, then normalize
                servo_normalized = steer_raw  # Already -1.0 to 1.0
                
                # Throttle mapping - EXACT logic from car_control_logi.py
                throttle = map_pedal_to_throttle(accel_raw, mode, self._throttle_state_key)
                
                # Apply turbo gain if enabled - EXACT match with car_control_logi.py
                TURBO_GAIN = 1.30  # 30% más
                if turbo_mode:
                    throttle = min(1.0, throttle * TURBO_GAIN)
                
                # Brake conversion - EXACT match with car_control_logi.py
                # Uses percent_from_axis which applies (1 - axis_val) * 100
                # But we need normalized 0.0 to 1.0
                brake_pct = percent_from_axis(brake_raw)
                brake_normalized = brake_pct / 100.0
                
                # Handbrake - EXACT match with car_control_logi.py
                hbrake_pct = percent_from_axis(hbrake_raw)
                handbrake = 1.0 if hbrake_pct > 0 else 0.0
                
                # Create message with normalized values
                msg = JoystickMessage(
                    servo=servo_normalized,
                    throttle=throttle,
                    brake=brake_normalized,
                    handbrake=handbrake,
                    turbo=1.0 if turbo_mode else 0.0,
                    mode=active_mode,
                )
                
                # Send using TCP format (6-field) that bridge expects
                # Format: "servo,throttle,brake,handbrake,turbo,mode\n"
                tcp_msg = msg.to_tcp_format()
                self._socket.sendall(tcp_msg.encode("ascii"))
                
                # Log values periodically for debugging (every 50 messages ~2.5 seconds at 20Hz)
                if hasattr(self, '_debug_counter'):
                    self._debug_counter += 1
                else:
                    self._debug_counter = 0
                
                if self._debug_counter % 50 == 0:
                    logger.debug(
                        f"[joystick-sender] Values: "
                        f"servo={servo_normalized:.3f}, "
                        f"throttle={throttle:.3f}, "
                        f"brake={brake_normalized:.3f}, "
                        f"mode={active_mode}, "
                        f"raw_accel={accel_raw:.3f}, "
                        f"raw_brake={brake_raw:.3f}"
                    )
                
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

