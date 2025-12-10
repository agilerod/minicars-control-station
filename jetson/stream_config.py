#!/usr/bin/env python3
"""
MiniCars Stream Configuration Loader.

Loads and validates streaming configuration from stream_config.json.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Optional

# Verify Python version (need at least 3.6)
if sys.version_info < (3, 6):
    print(f"[STREAM-CONFIG] ERROR: Python 3.6+ required, found {sys.version_info.major}.{sys.version_info.minor}")
    sys.exit(1)

logger = logging.getLogger(__name__)

# Python 3.7+ has dataclasses, but Jetson may have Python 3.6
# Use a fallback for compatibility
try:
    from dataclasses import dataclass
    _HAS_DATACLASS = True
except ImportError:
    _HAS_DATACLASS = False
    # Fallback: simple class without dataclass decorator
    def dataclass(cls):
        """No-op decorator for Python < 3.7."""
        return cls


class ResolutionConfig:
    """Video resolution configuration."""
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
    
    def __repr__(self):
        return f"ResolutionConfig(width={self.width}, height={self.height})"


@dataclass if _HAS_DATACLASS else lambda x: x
class StreamConfig:
    """
    Streaming configuration for Jetson camera.
    
    Attributes:
        control_station_host: IP or hostname of control station (laptop)
        video_port: UDP port for video stream
        backend_port: TCP port for backend connectivity check (default: 8000)
        camera_device: Camera device name (typically "nvarguscamerasrc")
        ssid: WiFi SSID to require (None or empty string = no SSID check)
        resolution: Video resolution (width, height)
        framerate: Video framerate (fps)
        bitrate: Video bitrate (bits per second)
        flip_method: Video flip method (0=none, 2=180°, etc.)
    """
    control_station_host: str
    video_port: int
    backend_port: int  # TCP port for connectivity check (default 8000)
    camera_device: str
    ssid: Optional[str]
    resolution: ResolutionConfig
    framerate: int
    bitrate: int
    flip_method: int


class StreamConfigError(Exception):
    """Exception raised when stream configuration is invalid."""
    pass


def get_config_path() -> Path:
    """
    Get path to stream_config.json.
    
    Returns:
        Path to config file in jetson/config/stream_config.json
    """
    # This file is in jetson/, so config is at jetson/config/
    jetson_dir = Path(__file__).parent
    return jetson_dir / "config" / "stream_config.json"


def load_config() -> StreamConfig:
    """
    Load and validate stream configuration from JSON file.
    
    Returns:
        StreamConfig object with validated configuration
        
    Raises:
        StreamConfigError: If configuration file is missing or invalid
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        raise StreamConfigError(
            f"[STREAM-CONFIG] Configuration file not found: {config_path}"
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise StreamConfigError(
            f"[STREAM-CONFIG] Invalid JSON in config file: {e}"
        ) from e
    except Exception as e:
        raise StreamConfigError(
            f"[STREAM-CONFIG] Failed to read config file: {e}"
        ) from e
    
    # Validate required fields
    if not data.get("control_station_host"):
        raise StreamConfigError(
            "[STREAM-CONFIG] Missing or empty 'control_station_host'"
        )
    
    video_port = data.get("video_port")
    if not isinstance(video_port, int) or video_port < 1 or video_port > 65535:
        raise StreamConfigError(
            f"[STREAM-CONFIG] Invalid 'video_port': {video_port} (must be 1-65535)"
        )
    
    # Backend port for connectivity check (optional, default 8000)
    backend_port = data.get("backend_port", 8000)
    if not isinstance(backend_port, int) or backend_port < 1 or backend_port > 65535:
        raise StreamConfigError(
            f"[STREAM-CONFIG] Invalid 'backend_port': {backend_port} (must be 1-65535)"
        )
    
    if not data.get("camera_device"):
        raise StreamConfigError(
            "[STREAM-CONFIG] Missing or empty 'camera_device'"
        )
    
    # Parse resolution
    res_data = data.get("resolution", {})
    if not isinstance(res_data, dict):
        raise StreamConfigError(
            "[STREAM-CONFIG] Invalid 'resolution' (must be object with width/height)"
        )
    
    width = res_data.get("width")
    height = res_data.get("height")
    if not isinstance(width, int) or width < 1:
        raise StreamConfigError(
            f"[STREAM-CONFIG] Invalid 'resolution.width': {width}"
        )
    if not isinstance(height, int) or height < 1:
        raise StreamConfigError(
            f"[STREAM-CONFIG] Invalid 'resolution.height': {height}"
        )
    
    # Create ResolutionConfig (works with or without dataclass)
    if _HAS_DATACLASS:
        resolution = ResolutionConfig(width=width, height=height)
    else:
        resolution = ResolutionConfig(width=width, height=height)
    
    # Parse framerate
    framerate = data.get("framerate", 30)
    if not isinstance(framerate, int) or framerate < 1 or framerate > 120:
        raise StreamConfigError(
            f"[STREAM-CONFIG] Invalid 'framerate': {framerate} (must be 1-120)"
        )
    
    # Parse bitrate
    bitrate = data.get("bitrate", 8000000)
    if not isinstance(bitrate, int) or bitrate < 1000000:
        raise StreamConfigError(
            f"[STREAM-CONFIG] Invalid 'bitrate': {bitrate} (must be >= 1000000)"
        )
    
    # Parse flip_method
    flip_method = data.get("flip_method", 2)
    if not isinstance(flip_method, int) or flip_method < 0 or flip_method > 7:
        raise StreamConfigError(
            f"[STREAM-CONFIG] Invalid 'flip_method': {flip_method} (must be 0-7)"
        )
    
    # SSID is optional (can be None or empty string)
    ssid = data.get("ssid")
    if ssid == "":
        ssid = None
    
    logger.info(f"[STREAM-CONFIG] Loaded config from {config_path}")
    logger.info(f"[STREAM-CONFIG] Host: {data['control_station_host']}, Video Port: {video_port}, Backend Port: {backend_port}")
    
    # Create StreamConfig (works with or without dataclass)
    if _HAS_DATACLASS:
        return StreamConfig(
            control_station_host=data["control_station_host"],
            video_port=video_port,
            backend_port=backend_port,
            camera_device=data["camera_device"],
            ssid=ssid,
            resolution=resolution,
            framerate=framerate,
            bitrate=bitrate,
            flip_method=flip_method,
        )
    else:
        # Manual initialization for Python < 3.7
        config = StreamConfig.__new__(StreamConfig)
        config.control_station_host = data["control_station_host"]
        config.video_port = video_port
        config.backend_port = backend_port
        config.camera_device = data["camera_device"]
        config.ssid = ssid
        config.resolution = resolution
        config.framerate = framerate
        config.bitrate = bitrate
        config.flip_method = flip_method
        return config


def validate_config() -> None:
    """
    Validate configuration file (useful for testing).
    
    Raises:
        StreamConfigError: If configuration is invalid
    """
    try:
        config = load_config()
        print(f"[STREAM-CONFIG] ✓ Configuration valid")
        print(f"[STREAM-CONFIG]   Host: {config.control_station_host}")
        print(f"[STREAM-CONFIG]   Video Port: {config.video_port}")
        print(f"[STREAM-CONFIG]   Backend Port: {config.backend_port}")
        print(f"[STREAM-CONFIG]   SSID: {config.ssid or '(no check)'}")
        print(f"[STREAM-CONFIG]   Resolution: {config.resolution.width}x{config.resolution.height}")
        print(f"[STREAM-CONFIG]   Framerate: {config.framerate} fps")
        print(f"[STREAM-CONFIG]   Bitrate: {config.bitrate} bps")
    except StreamConfigError as e:
        print(f"[STREAM-CONFIG] ✗ Configuration error: {e}")
        raise


if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    validate_config()

