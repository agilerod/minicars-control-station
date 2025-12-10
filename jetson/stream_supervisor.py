#!/usr/bin/env python3
"""
MiniCars Stream Supervisor.

Monitors connectivity to control station and manages GStreamer pipeline
for camera streaming. Only starts pipeline when control station is reachable
and (optionally) when connected to the correct WiFi SSID.
"""
import logging
import os
import socket
import subprocess
import sys
import time
from typing import Optional

from stream_config import StreamConfig, StreamConfigError, load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[stream-supervisor] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global state
_pipeline_proc: Optional[subprocess.Popen] = None
_last_restart_attempt = 0.0
_restart_delay = 10.0  # Wait 10s after pipeline failure before retry


def check_host_reachable(host: str, port: int, timeout: float = 1.0) -> bool:
    """
    Check if host:port is reachable via TCP connection attempt.
    
    Args:
        host: Hostname or IP address
        port: TCP port
        timeout: Connection timeout in seconds
        
    Returns:
        True if connection succeeds, False otherwise
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except socket.gaierror:
        # DNS resolution failed
        logger.debug(f"DNS resolution failed for {host}")
        return False
    except Exception as e:
        logger.debug(f"Connection check failed: {e}")
        return False


def check_ssid_match(required_ssid: Optional[str]) -> bool:
    """
    Check if current WiFi SSID matches required SSID.
    
    Args:
        required_ssid: Required SSID (None or empty = no check)
        
    Returns:
        True if SSID matches or no check required, False otherwise
    """
    if not required_ssid:
        return True  # No SSID check required
    
    try:
        # Try to get current SSID using iwgetid
        result = subprocess.run(
            ["iwgetid", "-r"],
            capture_output=True,
            text=True,
            timeout=2.0
        )
        
        if result.returncode != 0:
            logger.debug("iwgetid failed (may not be on WiFi)")
            return False
        
        current_ssid = result.stdout.strip()
        if current_ssid == required_ssid:
            logger.debug(f"SSID match: {current_ssid}")
            return True
        else:
            logger.debug(f"SSID mismatch: current={current_ssid}, required={required_ssid}")
            return False
    except FileNotFoundError:
        logger.debug("iwgetid not found (may not be installed)")
        return False
    except subprocess.TimeoutExpired:
        logger.debug("iwgetid timeout")
        return False
    except Exception as e:
        logger.debug(f"SSID check failed: {e}")
        return False


def restart_nvargus_daemon() -> bool:
    """
    Restart nvargus-daemon to avoid capture session errors.
    
    Note: This requires sudo without password (configured via sudoers).
    If sudo fails, we continue anyway as the pipeline might work without restart.
    
    Returns:
        True if restart succeeded, False otherwise
    """
    try:
        logger.info("Restarting nvargus-daemon...")
        # Try to restart without password prompt (requires sudoers config)
        # If it fails, we'll continue anyway
        result = subprocess.run(
            ["sudo", "-n", "systemctl", "restart", "nvargus-daemon"],
            capture_output=True,
            text=True,
            timeout=10.0
        )
        
        if result.returncode == 0:
            logger.info("nvargus-daemon restarted successfully")
            return True
        else:
            # If sudo requires password, log warning but continue
            if "password" in result.stderr.lower() or "no tty" in result.stderr.lower():
                logger.warning("nvargus-daemon restart skipped (sudo requires password). Pipeline may still work.")
                logger.warning("To enable auto-restart, configure sudoers: jetson-rod ALL=(ALL) NOPASSWD: /bin/systemctl restart nvargus-daemon")
            else:
                logger.warning(f"nvargus-daemon restart failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.warning("nvargus-daemon restart timeout")
        return False
    except Exception as e:
        logger.warning(f"nvargus-daemon restart error: {e}")
        return False


def build_gstreamer_pipeline(config: StreamConfig) -> list:
    """
    Build GStreamer pipeline command from configuration.
    
    Args:
        config: Stream configuration
        
    Returns:
        List of command arguments for GStreamer
    """
    gst_cmd = [
        "gst-launch-1.0", "-e",
        config.camera_device,
        "!", f'video/x-raw(memory:NVMM),width={config.resolution.width},height={config.resolution.height},framerate={config.framerate}/1',
        "!", "nvvidconv", f"flip-method={config.flip_method}",
        "!", 'video/x-raw(memory:NVMM),format=NV12',
        "!", "nvv4l2h264enc",
        "insert-sps-pps=true",
        "maxperf-enable=1",
        "control-rate=2",
        f"bitrate={config.bitrate}",
        "iframeinterval=10",
        "!", "h264parse",
        "!", "rtph264pay", "config-interval=1", "pt=96",
        "!", "udpsink",
        f"host={config.control_station_host}",
        f"port={config.video_port}",
        "sync=false",
        "async=false",
    ]
    
    return gst_cmd


def start_pipeline(config: StreamConfig) -> bool:
    """
    Start GStreamer pipeline.
    
    Args:
        config: Stream configuration
        
    Returns:
        True if pipeline started successfully, False otherwise
    """
    global _pipeline_proc
    
    # Check for duplicate pipelines (safety check)
    existing_processes = subprocess.run(
        ["pgrep", "-f", "gst-launch-1.0.*nvarguscamerasrc"],
        capture_output=True,
        text=True
    )
    if existing_processes.returncode == 0:
        pids = existing_processes.stdout.strip().split('\n')
        pids = [p for p in pids if p and p != str(os.getpid())]  # Exclude current process
        if pids:
            logger.warning(f"Found {len(pids)} existing pipeline process(es): {pids}")
            logger.warning("Another pipeline may already be running. Attempting to continue anyway.")
    
    if _pipeline_proc is not None:
        # Pipeline already running, check if it's still alive
        poll_result = _pipeline_proc.poll()
        if poll_result is None:
            logger.debug("Pipeline already running")
            return True
        else:
            logger.warning(f"Previous pipeline died (exit code: {poll_result})")
            _pipeline_proc = None
    
    # Try to restart nvargus-daemon before starting pipeline (optional, may fail if sudo requires password)
    # If it fails, we continue anyway - the pipeline might work without restart
    nvargus_restarted = restart_nvargus_daemon()
    
    # Only wait if we successfully restarted nvargus-daemon
    if nvargus_restarted:
        logger.debug("Waiting for nvargus-daemon to stabilize...")
        time.sleep(2)
    else:
        logger.debug("Skipping nvargus-daemon stabilization wait (restart was skipped)")
    
    # Build and launch pipeline
    gst_cmd = build_gstreamer_pipeline(config)
    
    try:
        logger.info(f"Starting GStreamer pipeline to {config.control_station_host}:{config.video_port}...")
        logger.debug(f"Command: {' '.join(gst_cmd)}")
        
        _pipeline_proc = subprocess.Popen(
            gst_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give it a moment to start and check for immediate failures
        time.sleep(1.5)  # Wait a bit longer to catch initialization errors
        
        # Check if it's still running
        poll_result = _pipeline_proc.poll()
        if poll_result is not None:
            # Process died immediately - read stderr for diagnostics
            stderr_output = ""
            stdout_output = ""
            try:
                # Use communicate() with timeout to get all output
                try:
                    stdout_bytes, stderr_bytes = _pipeline_proc.communicate(timeout=2.0)
                    if stderr_bytes:
                        stderr_output = stderr_bytes.decode('utf-8', errors='replace').strip()
                    if stdout_bytes:
                        stdout_output = stdout_bytes.decode('utf-8', errors='replace').strip()
                except subprocess.TimeoutExpired:
                    # Process is still running? That's unexpected if poll() returned non-None
                    # Try to kill it and read what we can
                    _pipeline_proc.kill()
                    try:
                        stdout_bytes, stderr_bytes = _pipeline_proc.communicate(timeout=1.0)
                        if stderr_bytes:
                            stderr_output = stderr_bytes.decode('utf-8', errors='replace').strip()
                        if stdout_bytes:
                            stdout_output = stdout_bytes.decode('utf-8', errors='replace').strip()
                    except:
                        pass
            except Exception as e:
                stderr_output = f"Could not read stderr: {e}"
            
            logger.error(f"Pipeline failed to start (exit code: {poll_result})")
            if stderr_output:
                # Log stderr (most important for GStreamer errors)
                logger.error(f"GStreamer stderr:\n{stderr_output}")
            if stdout_output:
                # Log stdout (may contain useful info)
                logger.error(f"GStreamer stdout:\n{stdout_output}")
            if not stderr_output and not stdout_output:
                logger.error("No output captured. Pipeline may have failed during initialization.")
                logger.error("Common causes:")
                logger.error("  - Camera device busy (another process using it)")
                logger.error("  - nvargus-daemon not running or needs restart")
                logger.error("  - Permission problems")
                logger.error("  - Invalid GStreamer pipeline syntax")
            _pipeline_proc = None
            return False
        
        logger.info("GStreamer pipeline started successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}", exc_info=True)
        _pipeline_proc = None
        return False


def stop_pipeline() -> None:
    """
    Stop GStreamer pipeline gracefully.
    Also stops any duplicate pipelines that may be running.
    """
    global _pipeline_proc
    
    logger.info("Stopping GStreamer pipeline...")
    
    # Stop managed pipeline
    if _pipeline_proc is not None:
        try:
            # Try graceful termination
            _pipeline_proc.terminate()
            
            try:
                _pipeline_proc.wait(timeout=3.0)
                logger.info("Pipeline stopped gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop
                logger.warning("Pipeline did not stop gracefully, forcing kill...")
                _pipeline_proc.kill()
                _pipeline_proc.wait()
                logger.info("Pipeline killed")
        except Exception as e:
            logger.error(f"Error stopping managed pipeline: {e}")
        finally:
            _pipeline_proc = None
    
    # Safety: Also check for and stop any orphaned pipelines
    try:
        existing_processes = subprocess.run(
            ["pgrep", "-f", "gst-launch-1.0.*nvarguscamerasrc"],
            capture_output=True,
            text=True
        )
        if existing_processes.returncode == 0:
            pids = existing_processes.stdout.strip().split('\n')
            pids = [p for p in pids if p and p != str(os.getpid())]
            if pids:
                logger.warning(f"Found {len(pids)} orphaned pipeline process(es): {pids}. Stopping them...")
                for pid in pids:
                    try:
                        os.kill(int(pid), 15)  # SIGTERM
                        logger.info(f"Sent SIGTERM to orphaned pipeline PID {pid}")
                    except (ValueError, ProcessLookupError, PermissionError) as e:
                        logger.warning(f"Could not stop PID {pid}: {e}")
    except Exception as e:
        logger.warning(f"Error checking for orphaned pipelines: {e}")


def main_loop(config: StreamConfig) -> None:
    """
    Main supervisor loop.
    
    Monitors connectivity and manages pipeline lifecycle.
    
    Args:
        config: Stream configuration
    """
    global _last_restart_attempt
    
    logger.info("=" * 60)
    logger.info("MiniCars Stream Supervisor Starting")
    logger.info("=" * 60)
    logger.info(f"Control station: {config.control_station_host}")
    logger.info(f"  Video stream (UDP): port {config.video_port}")
    logger.info(f"  Backend check (TCP): port {config.backend_port}")
    logger.info(f"SSID check: {config.ssid or '(disabled)'}")
    logger.info(f"Resolution: {config.resolution.width}x{config.resolution.height}@{config.framerate}fps")
    logger.info(f"Bitrate: {config.bitrate} bps")
    logger.info("=" * 60)
    
    # Safety check: Verify no other supervisor instance is running
    current_pid = os.getpid()
    supervisor_processes = subprocess.run(
        ["pgrep", "-f", "stream_supervisor.py"],
        capture_output=True,
        text=True
    )
    if supervisor_processes.returncode == 0:
        pids = [p for p in supervisor_processes.stdout.strip().split('\n') if p and p != str(current_pid)]
        if pids:
            logger.warning(f"WARNING: Found {len(pids)} other stream_supervisor process(es) with PIDs: {pids}")
            logger.warning("Multiple supervisors may cause conflicts. Consider stopping duplicates.")
    else:
        logger.debug("No duplicate supervisor processes detected")
    
    iteration = 0
    consecutive_failures = 0
    max_consecutive_failures = 5
    
    while True:
        iteration += 1
        current_time = time.time()
        
        try:
            # Check backend reachability (TCP port 8000 for backend API)
            # This is more reliable than checking UDP video port
            host_reachable = check_host_reachable(config.control_station_host, config.backend_port)
            
            # Check SSID if required
            ssid_ok = check_ssid_match(config.ssid)
            
            should_run = host_reachable and ssid_ok
            
            # Pipeline state
            pipeline_running = _pipeline_proc is not None and _pipeline_proc.poll() is None
            
            if should_run:
                if not pipeline_running:
                    # Host is reachable but pipeline is not running
                    # Check if we should attempt restart (respect cooldown)
                    time_since_last_attempt = current_time - _last_restart_attempt
                    if time_since_last_attempt >= _restart_delay:
                        logger.info(f"Backend reachable at {config.control_station_host}:{config.backend_port}, starting pipeline...")
                        if start_pipeline(config):
                            consecutive_failures = 0
                            _last_restart_attempt = current_time
                        else:
                            consecutive_failures += 1
                            _last_restart_attempt = current_time
                            logger.warning(f"Pipeline start failed (consecutive failures: {consecutive_failures})")
                            if consecutive_failures >= max_consecutive_failures:
                                logger.error(f"Too many consecutive failures ({consecutive_failures}), waiting longer...")
                                time.sleep(30)  # Longer wait after many failures
                                consecutive_failures = 0
                    else:
                        wait_time = _restart_delay - time_since_last_attempt
                        logger.debug(f"Waiting {wait_time:.1f}s before retry...")
                else:
                    # Pipeline running and backend reachable - all good
                    if iteration % 20 == 0:  # Log every ~60 seconds (20 * 3s)
                        logger.info(f"Pipeline running, backend reachable at {config.control_station_host}:{config.backend_port}")
            else:
                if pipeline_running:
                    # Host not reachable but pipeline is running - stop it
                    reason = []
                    if not host_reachable:
                        reason.append(f"backend unreachable at {config.control_station_host}:{config.backend_port}")
                    if not ssid_ok:
                        reason.append(f"SSID mismatch (required: {config.ssid})")
                    logger.info(f"Backend/SSID not OK ({', '.join(reason)}), stopping pipeline")
                    stop_pipeline()
                    consecutive_failures = 0
                else:
                    # Backend not reachable and no pipeline - just wait
                    if iteration % 10 == 0:  # Log every ~30 seconds
                        reason = []
                        if not host_reachable:
                            reason.append(f"backend unreachable at {config.control_station_host}:{config.backend_port}")
                        if not ssid_ok:
                            reason.append(f"SSID mismatch")
                        logger.info(f"Waiting for backend connectivity... ({', '.join(reason)})")
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            time.sleep(5)  # Wait a bit before continuing
        
        # Sleep between iterations
        time.sleep(3)
    
    # Cleanup on exit
    logger.info("Shutting down supervisor...")
    stop_pipeline()
    logger.info("Supervisor stopped")


def main() -> None:
    """Main entry point."""
    try:
        # Load configuration
        try:
            config = load_config()
        except StreamConfigError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        
        # Run main loop
        main_loop(config)
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

