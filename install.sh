#!/bin/bash
set -e

# VanDash Provisioning Script for Raspberry Pi 5
# Responsibilities: OS validation, System Update, Dependency Management, Build Prep.

echo "🚀 Starting VanDash Appliance Provisioning..."

# 1. OS Verification
if [ -f /etc/os-release ]; then
    OS=$(grep "^ID=" /etc/os-release | cut -d= -f2 | tr -d '"')
    CODENAME=$(grep "^VERSION_CODENAME=" /etc/os-release | cut -d= -f2 | tr -d '"')
    
    echo "📊 Detected OS: $OS (Codename: $CODENAME)"
    
    if [[ "$OS" != "raspbian" && "$OS" != "debian" ]]; then
        echo "⚠️  Warning: This script is optimized for Raspberry Pi OS / Debian."
        read -p "Proceed anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "❌ Error: Could not determine OS version. Are you on a Linux system?"
    exit 1
fi

# 2. System Update
echo "🔄 Updating package lists..."
sudo apt update

# 3. OS Package Installation
echo "📦 Installing system dependencies from system-packages.txt..."
if [ -f "system-packages.txt" ]; then
    # Filter comments and empty lines
    DEPS=$(grep -v '^#' system-packages.txt | grep -v '^$' | xargs)
    sudo apt install -y $DEPS
else
    echo "❌ Error: system-packages.txt not found in the current directory."
    exit 1
fi

# 4. uv (Python Project Manager) Installation
if ! command -v uv &> /dev/null; then
    echo "🐍 Installing uv for Python dependency management..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Ensure uv is in path for the rest of the script
    export PATH="$HOME/.local/bin:$PATH"
    source $HOME/.cargo/env 2>/dev/null || true
else
    echo "✅ uv is already installed."
fi

# 5. Application Preparation (Backend)
echo "🔗 Syncing Python environment (uv)..."
# We run from project root where pyproject.toml is located
uv sync

# 6. Application Preparation (Frontend)
if [ -d "frontend" ]; then
    echo "🌐 Preparing Frontend..."
    cd frontend
    echo "📥 Installing frontend dependencies..."
    npm install
    echo "🏗️  Building production assets..."
    npm run build
    cd ..
else
    echo "⚠️  Warning: 'frontend' directory not found. Skipping UI build."
fi

# 7. Hardware Permissions
echo "🔑 Granting user '$USER' hardware access (video, dialout, i2c)..."
sudo usermod -a -G video $USER || true
sudo usermod -a -G dialout $USER || true
sudo usermod -a -G i2c $USER || true

# 8. Success Message
echo ""
echo "✨ VanDash Provisioning Complete!"
echo "======================================================="
echo "ENVIRONMENT SUMMARY:"
echo " - Hardware Groups: user added to video, dialout, i2c"
echo " - Python: Managed by uv (see pyproject.toml)"
echo " - Frontend: Assets built in frontend/dist"
echo ""
echo "NEXT STEPS:"
echo " 1. Logout and login again to refresh group memberships."
echo " 2. Start the backend: uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"
echo " 3. Or use the systemd service in 'scripts/' if configured."
echo "======================================================="
