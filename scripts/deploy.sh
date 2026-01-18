#!/bin/bash
# JLegal Deployment Script for Digital Ocean
# Usage: ./scripts/deploy.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}JLegal Document Processor - Deployment Script${NC}"
echo "================================================"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}Installing Docker Compose...${NC}"
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from example...${NC}"
    cp .env.example .env

    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/change-this-in-production-to-a-random-string/$SECRET_KEY/" .env

    echo -e "${GREEN}Created .env file with random SECRET_KEY${NC}"
    echo -e "${YELLOW}Review and edit .env if needed before continuing${NC}"
fi

# Create storage directory
mkdir -p storage
chmod 755 storage

# Pull/build images
echo -e "${GREEN}Building Docker images...${NC}"
docker-compose build

# Start services
echo -e "${GREEN}Starting services...${NC}"
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check health
echo -e "${GREEN}Checking service health...${NC}"
curl -s http://localhost:8000/health | python3 -m json.tool || echo "Health check endpoint not ready yet"

echo ""
echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Services running:"
docker-compose ps
echo ""
echo "API available at: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000"
echo "API docs at: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):8000/docs"
echo "Flower (task monitor) at: http://$(curl -s ifconfig.me 2>/dev/null || echo 'localhost'):5555"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f          # View logs"
echo "  docker-compose ps               # Check status"
echo "  docker-compose up -d --scale worker=4  # Scale workers"
echo "  docker-compose down             # Stop all services"
