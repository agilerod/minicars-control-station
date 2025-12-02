#!/usr/bin/env python3
"""
MiniCars TCP-to-UART Bridge for Jetson Nano.

Receives joystick commands via TCP from the laptop and forwards them
to the Arduino via UART. Includes watchdog for failsafe operation.
"""
import logging
import os
import signal
import socket
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional

try:
    import serial
except ImportError:
    print("ERROR: pyserial not installed. Run: pip3 install pyserial")
    sys.exit(1)

# Configuration from environment variables
BRIDGE_HOST = os.getenv("MINICARS_BRIDGE_HOST", "0.0.0.0")
BRIDGE_PORT = int(os.getenv("MINICARS_BRIDGE_PORT", "5005"))
UART_DEVICE = os.getenv("MINICARS_UART_DEVICE", "/dev/ttyTHS1")
UART_BAUD = int(os.getenv("MINICARS_UART_BAUD", "115200"))
WATCHDOG_MS = int(os.getenv("MINICARS_WATCHDOG_MS", "150"))
LOG_LEVEL = os.getenv("MINICARS_LOG_LEVEL", "INFO")
SERVO_CENTER = int(os.getenv("MINICARS_SERVO_CENTER", "90"))

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format='[minicars-joystick-bridge] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class JoystickMessage:
    """Parsed joystick message from TCP."""
    servo: float  # -1.0 to 1.0
    throttle: float  # 0.0 to 1.0
    brake: float  # 0.0 to 1.0
    handbrake: float  # 0.0 to 1.0
    turbo: float  # 0.0 to 1.0
    mode: str  # "kid", "normal", "pro"
    
    def to_uart_format(self) -> str:
        """
        Convert to UART format for Arduino.
        
        Returns:
            String: "servo_angle,accel_pct,brake_pct,hbrake_flag,turbo_flag\n"
        """
        # Convert normalized values to Arduino format
        servo_angle = int((self.servo + 1.0) * 90.0)  # -1..1 → 0..180
        servo_angle = max(0, min(180, servo_angle))  # Clamp
        
        accel_pct = int(self.throttle * 100.0)  # 0..1 → 0..100
        brake_pct = int(self.brake * 100.0)
        hbrake_flag = 1 if self.handbrake > 0.5 else 0
        turbo_flag = 1 if self.turbo > 0.5 else 0
        
        return f"{servo_angle},{accel_pct},{brake_pct},{hbrake_flag},{turbo_flag}\n"


def parse_message(line: str) -> Optional[JoystickMessage]:
    """
    Parse joystick message from TCP.
    
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


class TCPUARTBridge:
    """
    TCP-to-UART bridge for MiniCars joystick control.
    
    Receives commands via TCP and forwards to Arduino via UART,
    with watchdog failsafe.
    """
    
    def __init__(self):
        self.running = False
        self.uart: Optional[serial.Serial] = None
        self.tcp_socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
        
        # Watchdog state
        self.last_msg_time = 0.0
        self.watchdog_thread: Optional[threading.Thread] = None
        self.failsafe_active = False
        self.last_failsafe_log = 0.0
        
        # State for delta limiting
        self.last_servo = 0.0  # Normalized
        self.last_throttle = 0.0
        
    def open_uart(self) -> bool:
        """Open UART connection to Arduino."""
        try:
            self.uart = serial.Serial(
                UART_DEVICE,
                UART_BAUD,
                timeout=0.1,
                write_timeout=0.1,
            )
            logger.info(f"UART opened: {UART_DEVICE} @ {UART_BAUD} baud")
            return True
        except Exception as e:
            logger.error(f"Failed to open UART {UART_DEVICE}: {e}")
            return False
    
    def send_failsafe_to_uart(self) -> None:
        """Send failsafe command to Arduino (centered servo, no throttle, full brake)."""
        if not self.uart or not self.uart.is_open:
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
            uart_cmd = failsafe_msg.to_uart_format()
            self.uart.write(uart_cmd.encode('ascii'))
            self.uart.flush()
            
            # Rate-limited logging
            now = time.time()
            if now - self.last_failsafe_log > 1.0:
                logger.warning("Failsafe activated - sending safe command to Arduino")
                self.last_failsafe_log = now
        except Exception as e:
            logger.error(f"Failed to send failsafe to UART: {e}")
    
    def watchdog_loop(self) -> None:
        """Watchdog thread: monitors message timeout and applies failsafe."""
        logger.info(f"Watchdog started (timeout: {WATCHDOG_MS}ms)")
        
        while self.running:
            time.sleep(0.02)  # Check every 20ms
            
            if self.last_msg_time == 0:
                # No messages received yet
                continue
            
            elapsed_ms = (time.time() - self.last_msg_time) * 1000.0
            
            if elapsed_ms > WATCHDOG_MS:
                if not self.failsafe_active:
                    self.failsafe_active = True
                    logger.warning(f"No message for {elapsed_ms:.0f}ms - activating failsafe")
                
                self.send_failsafe_to_uart()
            else:
                if self.failsafe_active:
                    self.failsafe_active = False
                    logger.info("Messages resumed - failsafe deactivated")
    
    def apply_smoothing(self, msg: JoystickMessage) -> JoystickMessage:
        """
        Apply basic delta limiting to smooth control changes.
        
        Args:
            msg: Input message
            
        Returns:
            Smoothed message
        """
        # Max change per message (generous, main smoothing is in sender)
        max_servo_delta = 0.3  # 30% of range per message
        max_throttle_delta = 0.2  # 20% per message
        
        # Limit servo delta
        servo_delta = msg.servo - self.last_servo
        if abs(servo_delta) > max_servo_delta:
            new_servo = self.last_servo + (max_servo_delta if servo_delta > 0 else -max_servo_delta)
        else:
            new_servo = msg.servo
        
        # Limit throttle delta
        throttle_delta = msg.throttle - self.last_throttle
        if abs(throttle_delta) > max_throttle_delta:
            new_throttle = self.last_throttle + (max_throttle_delta if throttle_delta > 0 else -max_throttle_delta)
        else:
            new_throttle = msg.throttle
        
        # Update state
        self.last_servo = new_servo
        self.last_throttle = new_throttle
        
        # Return smoothed message
        return JoystickMessage(
            servo=new_servo,
            throttle=new_throttle,
            brake=msg.brake,  # Brake doesn't need smoothing
            handbrake=msg.handbrake,
            turbo=msg.turbo,
            mode=msg.mode,
        )
    
    def handle_client(self, client_sock: socket.socket, client_addr: tuple) -> None:
        """
        Handle a connected TCP client.
        
        Args:
            client_sock: Client socket
            client_addr: Client address tuple
        """
        logger.info(f"Client connected from {client_addr[0]}:{client_addr[1]}")
        
        # Reset state
        self.last_msg_time = 0.0
        self.last_servo = 0.0
        self.last_throttle = 0.0
        self.failsafe_active = False
        
        buffer = ""
        invalid_count = 0
        
        try:
            while self.running:
                # Receive data
                data = client_sock.recv(1024)
                if not data:
                    logger.info("Client disconnected")
                    break
                
                buffer += data.decode('ascii', errors='ignore')
                
                # Process complete lines
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    
                    # Parse message
                    msg = parse_message(line)
                    if msg is None:
                        invalid_count += 1
                        if invalid_count % 100 == 1:  # Rate-limit logging
                            logger.warning(f"Invalid message: {line[:50]}")
                        continue
                    
                    # Reset invalid counter on valid message
                    invalid_count = 0
                    
                    # Update watchdog timestamp
                    self.last_msg_time = time.time()
                    
                    # Apply smoothing
                    smoothed_msg = self.apply_smoothing(msg)
                    
                    # Convert to UART format and send
                    uart_cmd = smoothed_msg.to_uart_format()
                    
                    if self.uart and self.uart.is_open:
                        try:
                            self.uart.write(uart_cmd.encode('ascii'))
                            self.uart.flush()
                            logger.debug(f"Sent to UART: {uart_cmd.strip()}")
                        except Exception as e:
                            logger.error(f"Failed to write to UART: {e}")
                            break
                    
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            # Send failsafe before closing
            self.send_failsafe_to_uart()
            client_sock.close()
            logger.info("Client connection closed")
    
    def run(self) -> None:
        """Main loop: accept TCP connections and forward to UART."""
        # Open UART
        if not self.open_uart():
            logger.error("Failed to open UART - exiting")
            return
        
        # Create TCP server socket
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind((BRIDGE_HOST, BRIDGE_PORT))
            self.tcp_socket.listen(1)
            logger.info(f"TCP server listening on {BRIDGE_HOST}:{BRIDGE_PORT}")
        except Exception as e:
            logger.error(f"Failed to create TCP server: {e}")
            return
        
        # Start watchdog thread
        self.running = True
        self.watchdog_thread = threading.Thread(target=self.watchdog_loop, daemon=True)
        self.watchdog_thread.start()
        
        # Accept connections loop
        while self.running:
            try:
                logger.info("Waiting for client connection...")
                self.tcp_socket.settimeout(1.0)  # Allow checking self.running
                
                try:
                    client_sock, client_addr = self.tcp_socket.accept()
                except socket.timeout:
                    continue
                
                self.client_socket = client_sock
                self.handle_client(client_sock, client_addr)
                self.client_socket = None
                
            except Exception as e:
                if self.running:
                    logger.error(f"Error in accept loop: {e}")
                    time.sleep(1.0)
    
    def shutdown(self) -> None:
        """Graceful shutdown."""
        logger.info("Shutting down bridge...")
        self.running = False
        
        # Send final failsafe
        self.send_failsafe_to_uart()
        
        # Close sockets
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except:
                pass
        
        # Close UART
        if self.uart and self.uart.is_open:
            try:
                self.uart.close()
            except:
                pass
        
        # Wait for watchdog thread
        if self.watchdog_thread:
            self.watchdog_thread.join(timeout=1.0)
        
        logger.info("Bridge shut down")


# Global bridge instance for signal handling
bridge: Optional[TCPUARTBridge] = None


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"Received signal {signum}")
    if bridge:
        bridge.shutdown()
    sys.exit(0)


def main():
    """Main entry point."""
    global bridge
    
    logger.info("===========================================")
    logger.info("MiniCars TCP-UART Bridge Starting")
    logger.info("===========================================")
    logger.info(f"TCP: {BRIDGE_HOST}:{BRIDGE_PORT}")
    logger.info(f"UART: {UART_DEVICE} @ {UART_BAUD} baud")
    logger.info(f"Watchdog: {WATCHDOG_MS}ms timeout")
    logger.info(f"Log Level: {LOG_LEVEL}")
    logger.info("===========================================")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run bridge
    bridge = TCPUARTBridge()
    
    try:
        bridge.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        if bridge:
            bridge.shutdown()


if __name__ == "__main__":
    main()

