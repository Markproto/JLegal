#!/bin/bash
# JLegal Server Setup Script for Ubuntu 22.04/24.04
# Run as root on a fresh Digital Ocean droplet
# Usage: curl -fsSL <raw-url> | bash

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}JLegal Document Processor - Server Setup${NC}"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Please run as root${NC}"
    exit 1
fi

# Update system
echo -e "${GREEN}Updating system packages...${NC}"
apt update && apt upgrade -y

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
apt install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    git \
    ufw

# Install Docker
echo -e "${GREEN}Installing Docker...${NC}"
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Install Docker Compose
echo -e "${GREEN}Installing Docker Compose...${NC}"
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Configure firewall
echo -e "${GREEN}Configuring firewall...${NC}"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 8000/tcp
ufw allow 5555/tcp
ufw --force enable

# Create app directory
APP_DIR="/opt/jlegal"
echo -e "${GREEN}Setting up application directory at $APP_DIR${NC}"
mkdir -p $APP_DIR

# Print next steps
echo ""
echo -e "${GREEN}=========================================="
echo "Server Setup Complete!"
echo -e "==========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Clone the repository:"
echo "   cd $APP_DIR"
echo "   git clone <your-repo-url> ."
echo ""
echo "2. Create and configure .env:"
echo "   cp .env.example .env"
echo "   nano .env"
echo ""
echo "3. Deploy:"
echo "   ./scripts/deploy.sh"
echo ""
echo "Server IP: $(curl -s ifconfig.me)"
