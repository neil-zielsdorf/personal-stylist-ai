#!/bin/bash

set -e

echo "Personal Stylist AI - Unraid Installation"
echo "=========================================="

# Configuration
REPO_URL="https://github.com/neil-zielsdorf/personal-stylist-ai.git"
INSTALL_DIR="/mnt/user/appdata/personal-stylist"
VERSION=${1:-latest}

# Functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo "[ERROR] $1" >&2
    exit 1
}

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    error "Docker is not installed or not in PATH"
fi

if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed or not in PATH"
fi

# Create installation directory
log "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Clone or update repository
if [ -d ".git" ]; then
    log "Updating existing installation..."
    git fetch origin
    git checkout main
    git pull origin main
else
    log "Cloning repository..."
    git clone "$REPO_URL" .
fi

# Checkout specific version if requested
if [ "$VERSION" != "latest" ]; then
    log "Checking out version: $VERSION"
    git checkout "$VERSION"
fi

# Create data directories
log "Creating data directories..."
mkdir -p data/{database,users}
mkdir -p uploads/{clothing,body_analysis,temp}
mkdir -p models/cache

# Set permissions
log "Setting permissions..."
chmod -R 755 data uploads models
chown -R nobody:users data uploads models 2>/dev/null || true

# Create environment file
log "Creating environment configuration..."
cat > .env << EOF
# Personal Stylist AI Configuration
VERSION=$VERSION
COMPOSE_PROJECT_NAME=personal-stylist
COMPOSE_FILE=docker/docker-compose.yml

# Streamlit Configuration
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_PORT=8501

# Application Settings
PYTHONUNBUFFERED=1
DEBUG=false
EOF

# Deploy with Docker Compose
log "Deploying with Docker Compose..."
docker-compose -f docker/docker-compose.yml pull
docker-compose -f docker/docker-compose.yml up -d

# Wait for application to start
log "Waiting for application to start..."
sleep 10

# Check if application is running
if docker-compose -f docker/docker-compose.yml ps | grep -q "Up"; then
    log "✓ Personal Stylist AI installed successfully!"
    echo ""
    echo "Access your application at: http://$(hostname -I | awk '{print $1}'):8501"
    echo ""
    echo "First-time setup:"
    echo "1. Open the web interface"
    echo "2. Create your first user profile"
    echo "3. Upload some clothing photos"
    echo "4. Get your first outfit recommendation!"
    echo ""
    echo "For support, visit: https://github.com/neil-zielsdorf/personal-stylist-ai/issues"
else
    error "Installation failed. Check logs with: docker-compose -f docker/docker-compose.yml logs"
fi