#!/bin/bash
#
# MiniCars Jetson Deployment Script
#
# Este script actualiza el código en la Jetson Nano desde GitHub,
# actualiza permisos, sincroniza el servicio systemd y reinicia los servicios necesarios.
#
# Uso:
#   ./deploy_to_jetson.sh
#
# Requisitos:
#   - Repositorio clonado en /home/jetson-rod/minicars-control-station
#   - Acceso a Internet para git pull
#   - Permisos sudo para reiniciar servicios

set -e  # Salir si cualquier comando falla

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Banner
echo "=========================================="
echo "=== MiniCars Jetson Deployment ==="
echo "=========================================="
echo ""

# Verificar que el repositorio existe
REPO_PATH="/home/jetson-rod/minicars-control-station"
if [ ! -d "$REPO_PATH" ]; then
    echo -e "${RED}Error: El repositorio no existe en $REPO_PATH${NC}"
    echo "Por favor, clona el repositorio primero:"
    echo "  git clone git@github.com:tu-usuario/minicars-control-station.git $REPO_PATH"
    exit 1
fi

echo -e "${GREEN}✓${NC} Repositorio encontrado en $REPO_PATH"
echo ""

# Entrar al repositorio
cd "$REPO_PATH" || {
    echo -e "${RED}Error: No se pudo cambiar al directorio $REPO_PATH${NC}"
    exit 1
}

echo "Directorio actual: $(pwd)"
echo ""

# Hacer git pull (con manejo de errores sin internet)
echo "Actualizando código desde GitHub..."
echo "-----------------------------------"
if git pull origin main; then
    echo -e "${GREEN}✓${NC} Código actualizado correctamente"
else
    EXIT_CODE=$?
    echo -e "${YELLOW}⚠${NC} No se pudo hacer git pull (código: $EXIT_CODE)"
    echo ""
    echo "Posibles causas:"
    echo "  - Sin conexión a Internet (continuando con código local...)"
    echo "  - Problemas con SSH keys para GitHub"
    echo "  - El repositorio remoto no está configurado"
    echo ""
    echo "Para verificar SSH con GitHub:"
    echo "  ssh -T git@github.com"
    echo ""
    echo "Para verificar el remoto:"
    echo "  git remote -v"
    echo ""
    echo -e "${YELLOW}CONTINUANDO CON CÓDIGO LOCAL EXISTENTE${NC}"
    echo "(Si no hay internet, asegúrate de que el código local esté actualizado)"
    echo ""
fi

# Actualizar permisos del script
echo "Actualizando permisos..."
echo "-----------------------------------"
if [ -f "jetson/start_streamer.py" ]; then
    chmod +x jetson/start_streamer.py
    echo -e "${GREEN}✓${NC} Permisos actualizados para jetson/start_streamer.py"
else
    echo -e "${YELLOW}⚠${NC} No se encontró jetson/start_streamer.py"
fi
echo ""

# Sincronizar servicio systemd
echo "Sincronizando servicio systemd..."
echo "-----------------------------------"
if [ -f "jetson/minicars-streamer.service" ]; then
    sudo cp jetson/minicars-streamer.service /etc/systemd/system/minicars-streamer.service
    sudo systemctl daemon-reload
    echo -e "${GREEN}✓${NC} Servicio systemd sincronizado"
else
    echo -e "${YELLOW}⚠${NC} No se encontró jetson/minicars-streamer.service"
fi
echo ""

# Reiniciar nvargus-daemon
echo "Reiniciando nvargus-daemon..."
echo "-----------------------------------"
if sudo systemctl restart nvargus-daemon; then
    echo -e "${GREEN}✓${NC} nvargus-daemon reiniciado"
    echo "Esperando 2 segundos para estabilización..."
    sleep 2
else
    echo -e "${YELLOW}⚠${NC} No se pudo reiniciar nvargus-daemon (puede no estar instalado)"
fi
echo ""

# Reiniciar el servicio GStreamer
echo "Reiniciando servicio minicars-streamer..."
echo "-----------------------------------"
if sudo systemctl restart minicars-streamer; then
    echo -e "${GREEN}✓${NC} Servicio minicars-streamer reiniciado"
else
    echo -e "${YELLOW}⚠${NC} No se pudo reiniciar minicars-streamer"
    echo "Verifica que el servicio esté habilitado:"
    echo "  sudo systemctl enable minicars-streamer.service"
fi
echo ""

# Sincronizar servicio joystick (TCP-UART bridge)
echo "Sincronizando servicio minicars-joystick..."
echo "-----------------------------------"
if [ -f "jetson/minicars-joystick.service" ]; then
    sudo cp jetson/minicars-joystick.service /etc/systemd/system/minicars-joystick.service
    sudo systemctl daemon-reload
    sudo systemctl enable minicars-joystick.service
    echo -e "${GREEN}✓${NC} Servicio minicars-joystick sincronizado"
else
    echo -e "${YELLOW}⚠${NC} No se encontró jetson/minicars-joystick.service"
fi
echo ""

# Actualizar permisos del bridge
echo "Actualizando permisos del TCP-UART bridge..."
echo "-----------------------------------"
if [ -f "jetson/tcp_uart_bridge.py" ]; then
    chmod +x jetson/tcp_uart_bridge.py
    echo -e "${GREEN}✓${NC} Permisos actualizados para jetson/tcp_uart_bridge.py"
else
    echo -e "${YELLOW}⚠${NC} No se encontró jetson/tcp_uart_bridge.py"
fi
echo ""

# Reiniciar el servicio joystick
echo "Reiniciando servicio minicars-joystick..."
echo "-----------------------------------"
if sudo systemctl restart minicars-joystick; then
    echo -e "${GREEN}✓${NC} Servicio minicars-joystick reiniciado"
else
    echo -e "${YELLOW}⚠${NC} No se pudo reiniciar minicars-joystick"
    echo "Verifica que el servicio esté habilitado:"
    echo "  sudo systemctl enable minicars-joystick.service"
fi
echo ""

# Mostrar estado final de ambos servicios
echo "=========================================="
echo "Estado de los servicios:"
echo "=========================================="
echo ""
echo "--- Servicio Streamer (GStreamer) ---"
sudo systemctl status minicars-streamer --no-pager -l | head -n 15 || true
echo ""
echo "--- Servicio Joystick (TCP-UART Bridge) ---"
sudo systemctl status minicars-joystick --no-pager -l | head -n 15 || true
echo ""

# Mostrar comandos para ver logs
echo "=========================================="
echo "Para ver logs en tiempo real:"
echo "-----------------------------------"
echo -e "${GREEN}# Streamer:${NC}"
echo "  journalctl -u minicars-streamer -f"
echo ""
echo -e "${GREEN}# Joystick:${NC}"
echo "  journalctl -u minicars-joystick -f"
echo ""
echo -e "${GREEN}# Ambos:${NC}"
echo "  journalctl -u minicars-streamer -u minicars-joystick -f"
echo ""

echo "=========================================="
echo -e "${GREEN}Deployment completado${NC}"
echo "=========================================="

