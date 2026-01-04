#!/bin/bash
# VanDash Launch Wrapper
# This script starts the backend and serves the frontend.

# Define Colors
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Launching VanDash...${NC}"

# Navigate to project root (directory of this script)
cd "$(dirname "$0")"

# 1. Check for build artifacts
if [ ! -d "frontend/dist" ]; then
    echo "⚠️  Frontend build not found. Running build first..."
    cd frontend && npm run build && cd ..
fi

# 2. Determine IP Address (Priority: wlan0, then eth0, then localhost)
IP_ADDR=$(hostname -I | awk '{print $1}')
if [ -z "$IP_ADDR" ]; then
    IP_ADDR="127.0.0.1"
fi

# 3. Start Backend
# We use port 8000 by default for the manual CLI launcher.
# Port 80 is usually reserved for the background systemd service.
echo -e "${GREEN}📡 Dashboard will be available at: http://$IP_ADDR:8000${NC}"
echo "Press Ctrl+C to stop."

uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
