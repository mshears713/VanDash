#!/bin/bash

# VanDash Deployment Script
# This script runs on the laptop to build and push artifacts to the Pi.

PI_IP="192.168.4.1"
PI_USER="pi"
REMOTE_DIR="/home/pi/VanDash"

echo "🚀 Starting VanDash Deployment..."

# 1. Build Frontend
echo "📦 Building Frontend..."
cd frontend
npm install && npm run build
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed. Aborting."
    exit 1
fi
cd ..

# 2. Sync to Pi
echo "📡 Syncing to Pi at $PI_IP..."
# Exclude dev-only files
rsync -avz --delete \
    --exclude '.git' \
    --exclude 'node_modules' \
    --exclude '__pycache__' \
    --exclude '.venv' \
    --exclude 'config/maintenance.yaml' \
    --exclude 'frontend/src' \
    --exclude 'frontend/node_modules' \
    ./ ${PI_USER}@${PI_IP}:${REMOTE_DIR}

if [ $? -ne 0 ]; then
    echo "❌ Sync failed. Are you connected to VanDash-Hub?"
    exit 1
fi

# 3. Restart Backend
echo "🔄 Restarting VanDash Backend..."
ssh ${PI_USER}@${PI_IP} "sudo systemctl restart vandash-backend"

if [ $? -ne 0 ]; then
    echo "❌ Failed to restart service. Manual check required."
    exit 1
fi

echo "✅ VanDash Deployment Successful!"
