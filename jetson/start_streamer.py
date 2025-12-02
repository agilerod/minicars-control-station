#!/usr/bin/env python3
"""
MiniCars Jetson GStreamer Sender

This script restarts nvargus-daemon and launches a GStreamer pipeline
to stream video from the Jetson Nano camera to a remote host via UDP.

The script is designed to be run as a systemd service.
"""
import logging
import socket
import subprocess
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[minicars-jetson] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def resolve_hostname(hostname: str) -> None:
    """
    Attempt to resolve a hostname and log the result.
    
    This is useful for mDNS hostnames that may take time to be available.
    If resolution fails, logs a warning but continues execution.
    """
    try:
        ip = socket.gethostbyname(hostname)
        logger.info(f"Resolved {hostname} to {ip}")
    except socket.gaierror:
        logger.warning(f"Could not resolve {hostname}, continuing anyway (mDNS may take time)")


def restart_nvargus_daemon() -> None:
    """
    Restart the nvargus-daemon service to avoid "Failed to create CaptureSession" errors.
    
    Raises:
        SystemExit: If the restart command fails.
    """
    logger.info("Restarting nvargus-daemon...")
    try:
        subprocess.run(
            ["sudo", "systemctl", "restart", "nvargus-daemon"],
            check=True
        )
        logger.info("nvargus-daemon restarted successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to restart nvargus-daemon: {e}")
        sys.exit(1)


def run_gstreamer_pipeline() -> None:
    """
    Run the GStreamer pipeline to stream video from the Jetson camera.
    
    The pipeline:
    - Captures video from nvarguscamerasrc
    - Converts and encodes to H.264
    - Sends via UDP to the configured host
    
    Raises:
        SystemExit: If the GStreamer pipeline fails.
    """
    # Pipeline optimizada para 720p30:
    # - bitrate ~8 Mbps (buena calidad en WiFi)
    # - control-rate=2 (VBR controlado)
    # - iframeinterval=10 (keyframes razonables para FPV)
    # - maxperf-enable=1 (optimización de performance)
    # - host=SKLNx.local, port=5000
    gst_cmd = [
        "gst-launch-1.0", "-e",
        "nvarguscamerasrc",
        "!", 'video/x-raw(memory:NVMM),width=1280,height=720,framerate=30/1',
        "!", "nvvidconv", "flip-method=2",
        "!", 'video/x-raw(memory:NVMM),format=NV12',
        "!", "nvv4l2h264enc",
        "insert-sps-pps=true",
        "maxperf-enable=1",
        "control-rate=2",
        "bitrate=8000000",
        "iframeinterval=10",
        "!", "h264parse",
        "!", "rtph264pay", "config-interval=1", "pt=96",
        "!", "udpsink",
        "host=SKLNx.local",
        "port=5000",
        "sync=false",
        "async=false",
    ]
    
    logger.info("Starting GStreamer pipeline...")
    try:
        subprocess.run(gst_cmd, check=True)
        logger.info("GStreamer pipeline finished.")
    except subprocess.CalledProcessError as e:
        logger.error(f"GStreamer pipeline failed with exit code {e.returncode}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("GStreamer pipeline interrupted by user.")
        sys.exit(0)


def main() -> None:
    """Main entry point for the script."""
    try:
        # Optional: Try to resolve the target hostname
        resolve_hostname("SKLNx.local")
        
        # Restart nvargus-daemon to avoid capture session errors
        restart_nvargus_daemon()
        
        # Wait a bit for nvargus-daemon to stabilize
        logger.info("Waiting 2 seconds for nvargus-daemon to stabilize...")
        time.sleep(2)
        
        # Run the GStreamer pipeline (runs in foreground)
        run_gstreamer_pipeline()
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

