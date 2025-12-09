#!/bin/bash
# MiniCars Jetson Services Deployment Script
#
# This script deploys systemd services for MiniCars on the Jetson Nano.
# It syncs service files and restarts services as needed.
#
# Usage:
#   ./deploy_services.sh

set -e  # Abort on errors

# Configuration
REPO_DIR="${HOME}/minicars-control-station"
JETSON_USER="jetson-rod"
SYSTEMD_DIR="/etc/systemd/system"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "MiniCars Jetson Services Deployment"
echo "=========================================="

# Step 1: Change to repo directory
echo ""
echo "Step 1: Locating repository..."
if [ ! -d "$REPO_DIR" ]; then
    echo -e "${RED}ERROR: Repository not found at $REPO_DIR${NC}"
    echo "Please clone the repository first:"
    echo "  git clone <repo-url> $REPO_DIR"
    exit 1
fi

cd "$REPO_DIR"
echo -e "${GREEN}✓${NC} Repository found at $REPO_DIR"

# Step 2: Optional git pull (commented by default)
echo ""
echo "Step 2: Updating code (optional)..."
echo "NOTE: To update code from GitHub, uncomment the git pull line below"
# Uncomment the next line to enable automatic git pull:
# if git pull origin main; then
#     echo -e "${GREEN}✓${NC} Code updated from GitHub"
# else
#     echo -e "${YELLOW}⚠${NC} Git pull failed (continuing anyway)"
# fi

# Step 3: Verify service files exist
echo ""
echo "Step 3: Verifying service files..."
SERVICES=(
    "jetson/minicars-streamer.service"
    "jetson/minicars-joystick.service"
)

for service_file in "${SERVICES[@]}"; do
    if [ ! -f "$service_file" ]; then
        echo -e "${RED}ERROR: Service file not found: $service_file${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓${NC} Found $service_file"
done

# Step 4: Copy service files to systemd
echo ""
echo "Step 4: Installing systemd services..."
for service_file in "${SERVICES[@]}"; do
    service_name=$(basename "$service_file")
    echo "  Installing $service_name..."
    
    sudo cp "$service_file" "$SYSTEMD_DIR/$service_name"
    echo -e "  ${GREEN}✓${NC} Copied to $SYSTEMD_DIR/$service_name"
done

# Step 5: Reload systemd daemon
echo ""
echo "Step 5: Reloading systemd daemon..."
sudo systemctl daemon-reload
echo -e "${GREEN}✓${NC} Systemd daemon reloaded"

# Step 6: Enable and restart streamer service
echo ""
echo "Step 6: Configuring minicars-streamer.service..."
sudo systemctl enable minicars-streamer.service
echo -e "${GREEN}✓${NC} Service enabled"

echo "  Restarting service..."
sudo systemctl restart minicars-streamer.service
echo -e "${GREEN}✓${NC} Service restarted"

# Step 7: Enable and restart joystick service (if needed)
echo ""
echo "Step 7: Configuring minicars-joystick.service..."
if systemctl is-enabled minicars-joystick.service >/dev/null 2>&1; then
    echo "  Service already enabled, restarting..."
    sudo systemctl restart minicars-joystick.service
    echo -e "${GREEN}✓${NC} Service restarted"
else
    echo "  Enabling service..."
    sudo systemctl enable minicars-joystick.service
    echo -e "${GREEN}✓${NC} Service enabled"
    
    echo "  Starting service..."
    sudo systemctl start minicars-joystick.service
    echo -e "${GREEN}✓${NC} Service started"
fi

# Step 8: Verify services are running
echo ""
echo "Step 8: Verifying services..."
echo ""
echo "=== minicars-streamer.service ==="
if systemctl is-active minicars-streamer.service >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Service is active"
else
    echo -e "${RED}✗${NC} Service is not active"
    echo "Check logs with: journalctl -u minicars-streamer.service -n 50"
fi

echo ""
echo "=== minicars-joystick.service ==="
if systemctl is-active minicars-joystick.service >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Service is active"
else
    echo -e "${RED}✗${NC} Service is not active"
    echo "Check logs with: journalctl -u minicars-joystick.service -n 50"
fi

# Step 9: Legacy services notice (if any exist)
echo ""
echo "=========================================="
echo "Deployment Complete"
echo "=========================================="
echo ""
echo "Useful commands:"
echo "  View streamer logs:  journalctl -u minicars-streamer.service -f"
echo "  View joystick logs:  journalctl -u minicars-joystick.service -f"
echo "  Check status:        systemctl status minicars-streamer.service"
echo ""
echo "Configuration:"
echo "  Stream config:       $REPO_DIR/jetson/config/stream_config.json"
echo "  Edit and restart:    sudo systemctl restart minicars-streamer.service"
echo ""

# Note about legacy services (if any were found)
if systemctl list-unit-files | grep -q "minicars.*stream.*service"; then
    echo -e "${YELLOW}NOTE:${NC} If you have legacy streaming services, you may want to disable them:"
    echo "  sudo systemctl disable --now <legacy-service-name>"
    echo ""
fi

echo "Done!"

