#!/usr/bin/env bash
set -euo pipefail

# deploy_vm.sh — prepare an Ubuntu VM and deploy the b3-quote-api
# Usage: copy this file to the VM and run: sudo bash deploy_vm.sh
# Assumes the repo will be cloned to /home/ubuntu/b3-quote-api

echo ">>> Updating apt and installing system packages"
sudo apt update
sudo apt install -y git curl ca-certificates software-properties-common

# Install Python 3.12 (deadsnakes for older Ubuntu)
if ! command -v python3.12 >/dev/null 2>&1; then
  echo ">>> Installing Python 3.12"
  sudo add-apt-repository -y ppa:deadsnakes/ppa
  sudo apt update
  sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip
fi

# Create project dir if missing and clone (or pull)
PROJECT_DIR="/home/ubuntu/b3-quote-api"
if [ ! -d "$PROJECT_DIR" ]; then
  echo ">>> Cloning repository into $PROJECT_DIR"
  sudo -u ubuntu git clone https://github.com/Alessandro-Borges/b3-quote-api.git $PROJECT_DIR
else
  echo ">>> Repository already present, pulling latest"
  (cd $PROJECT_DIR && sudo -u ubuntu git pull)
fi

# Create venv and install requirements
echo ">>> Creating virtual environment and installing Python deps"
cd $PROJECT_DIR
python3.12 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

# Optional: add corporate CA if provided at /tmp/company-ca.pem
if [ -f "/tmp/company-ca.pem" ]; then
  echo ">>> Installing corporate CA into system trust store"
  sudo cp /tmp/company-ca.pem /usr/local/share/ca-certificates/company-ca.crt
  sudo update-ca-certificates
fi

# Install systemd unit
echo ">>> Installing systemd service"
sudo cp api.service /etc/systemd/system/api.service
sudo systemctl daemon-reload
sudo systemctl enable --now api

# Open firewall (ufw) for port 8000 if ufw is used
if command -v ufw >/dev/null 2>&1; then
  echo ">>> Configuring ufw: allow 22 and 8000"
  sudo ufw allow 22/tcp
  sudo ufw allow 8000/tcp
  sudo ufw enable || true
fi

# Quick smoke tests
echo ">>> Smoke tests (local VM):"
sleep 2
curl -sS http://localhost:8000/health || true
curl -sS http://localhost:8000/api/v1/quote/PETR4 || true

echo "\n>>> Deploy finished. Check service with: sudo systemctl status api and journalctl -u api -f"
