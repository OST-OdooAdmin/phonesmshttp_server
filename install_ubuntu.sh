#!/usr/bin/env bash
# ==============================================================================
# Google Antigravity AI Engine - Ubuntu Server 1-Click Installer
# Compatible with Ubuntu 20.04 / 22.04 / 24.04 LTS
# ==============================================================================

set -e

echo "🚀 Installing Google Antigravity Universal Engine on Ubuntu Server..."

# 1. Update APT & Install Prerequisites
sudo apt-get update -y
sudo apt-get install -y git curl python3 python3-pip docker.io

# 2. Start & Enable Docker
sudo systemctl enable --now docker

# 3. Clone Repository
INSTALL_DIR="/opt/antigravity_server"
sudo rm -rf "$INSTALL_DIR"
sudo git clone https://github.com/OST-OdooAdmin/phonesmshttp_server.git "$INSTALL_DIR"

# 4. Install CLI Tool
sudo cp "$INSTALL_DIR/antigravity_cli.py" /usr/local/bin/antigravity
sudo chmod +x /usr/local/bin/antigravity

# 5. Build & Launch Docker Microservice Container
cd "$INSTALL_DIR/antigravity_service"
sudo docker build -t antigravity-ai-service .
sudo docker rm -f antigravity-ai-service || true
sudo docker run -d \
  --name antigravity-ai-service \
  -p 5005:5005 \
  --restart always \
  antigravity-ai-service

echo ""
echo "======================================================================="
echo "✅ Google Antigravity AI Engine successfully installed on Ubuntu Server!"
echo "• Microservice URL: http://localhost:5005/"
echo "• CLI Command:      antigravity"
echo "======================================================================="
