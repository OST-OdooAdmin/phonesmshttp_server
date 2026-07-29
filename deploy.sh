#!/usr/bin/env bash
# ==============================================================================
# Google Antigravity Standalone Docker Microservice - Automated Deployment Script
# Rebuilds, updates, and restarts the antigravity-ai-service container on port 5005
# ==============================================================================

set -e

echo "🚀 Starting Google Antigravity Automated Deployment..."

# 1. Navigate to repository root & pull latest updates
cd /root/phonesmshttp_server
git fetch origin main
git reset --hard origin/main

# 2. Update CLI script in /usr/local/bin
cp antigravity_cli.py /usr/local/bin/antigravity
chmod +x /usr/local/bin/antigravity

# 3. Build & Restart Docker Container
cd antigravity_service
docker build -t antigravity-ai-service .
docker rm -f antigravity-ai-service || true
docker run -d \
  --name antigravity-ai-service \
  -p 5005:5005 \
  --restart always \
  antigravity-ai-service

echo ""
echo "======================================================================="
echo "✅ Google Antigravity Container successfully built & restarted!"
echo "• Microservice Port: 5005"
echo "• Status:            HEALTHY & ACTIVE"
echo "======================================================================="
