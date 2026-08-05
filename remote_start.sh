#!/bin/bash
# remote_start.sh – start Antigravity Docker container and optional reverse tunnel
set -e

# Pull latest image (replace with actual image name if needed)
# docker pull myrepo/antigravity-ai-service:latest

# Stop any existing container named antigravity-ai-service
if docker ps -a --format '{{.Names}}' | grep -q '^antigravity-ai-service$'; then
  docker rm -f antigravity-ai-service
fi

# Start container exposing port 5005
docker run -d \
  --name antigravity-ai-service \
  -p 5005:5005 \
  myrepo/antigravity-ai-service:latest

# Optional reverse SSH tunnel back to laptop (replace <LAPTOP_IP> with actual IP)
# ssh -N -R 5005:localhost:5005 root@<LAPTOP_IP> &

echo "Remote Antigravity service started on port 5005"
