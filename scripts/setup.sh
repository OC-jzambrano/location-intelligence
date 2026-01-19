#!/bin/bash
# =============================================================================
# FastAPI REST API Starter - Setup Script
# =============================================================================
# This script sets up the development environment for the FastAPI starter kit.
# Run from the project root: ./scripts/setup.sh
# =============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Check if running from project root
if [ ! -f "pyproject.toml" ]; then
    error "Please run this script from the project root directory"
fi

echo ""
echo "=============================================="
echo "  FastAPI REST API Starter - Setup"
echo "=============================================="
echo ""

# -----------------------------------------------------------------------------
# Step 1: Check prerequisites
# -----------------------------------------------------------------------------
info "Checking prerequisites..."

# Check Python version
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
        error "Python 3.11+ is required. Found: Python $PYTHON_VERSION"
    fi
    success "Python $PYTHON_VERSION found"
else
    error "Python 3 is not installed"
fi

# Check Docker (optional)
if command -v docker &> /dev/null; then
    success "Docker found"
    DOCKER_AVAILABLE=true
else
    warn "Docker not found - you'll need to run PostgreSQL and Redis manually"
    DOCKER_AVAILABLE=false
fi

# Check docker-compose
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1; then
    success "docker-compose found"
else
    if [ "$DOCKER_AVAILABLE" = true ]; then
        warn "docker-compose not found"
    fi
fi

# -----------------------------------------------------------------------------
# Step 2: Create virtual environment
# -----------------------------------------------------------------------------
info "Setting up Python virtual environment..."

if [ -d ".venv" ]; then
    warn "Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        success "Virtual environment recreated"
    fi
else
    python3 -m venv .venv
    success "Virtual environment created"
fi

# Activate virtual environment
source .venv/bin/activate

# -----------------------------------------------------------------------------
# Step 3: Install dependencies
# -----------------------------------------------------------------------------
info "Installing dependencies..."

pip install --upgrade pip > /dev/null
pip install -e ".[dev]"

success "Dependencies installed"

# -----------------------------------------------------------------------------
# Step 4: Setup environment file
# -----------------------------------------------------------------------------
info "Setting up environment file..."

if [ -f ".env" ]; then
    warn ".env file already exists"
else
    cp .env.example .env
    
    # Generate secure JWT secret
    if command -v openssl &> /dev/null; then
        JWT_SECRET=$(openssl rand -hex 32)
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/your-super-secret-key-change-in-production/$JWT_SECRET/" .env
        else
            # Linux
            sed -i "s/your-super-secret-key-change-in-production/$JWT_SECRET/" .env
        fi
        success "Generated secure JWT secret"
    else
        warn "openssl not found - please update JWT_SECRET_KEY in .env manually"
    fi
    
    success ".env file created"
fi

# -----------------------------------------------------------------------------
# Step 5: Start services with Docker (if available)
# -----------------------------------------------------------------------------
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo ""
    read -p "Do you want to start PostgreSQL and Redis with Docker? (Y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        info "Starting Docker services..."
        
        # Start only db and redis services
        if docker compose version &> /dev/null 2>&1; then
            docker compose up -d db redis
        else
            docker-compose up -d db redis
        fi
        
        # Wait for services to be ready
        info "Waiting for services to be ready..."
        sleep 5
        
        success "Docker services started"
    fi
fi

# -----------------------------------------------------------------------------
# Step 6: Run tests
# -----------------------------------------------------------------------------
echo ""
read -p "Do you want to run the test suite? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    info "Running tests..."
    pytest tests/ -v || warn "Some tests failed - this may be expected if services aren't running"
fi

# -----------------------------------------------------------------------------
# Complete
# -----------------------------------------------------------------------------
echo ""
echo "=============================================="
echo "  Setup Complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo ""
echo "  1. Activate the virtual environment:"
echo "     source .venv/bin/activate"
echo ""
echo "  2. Start the development server:"
echo "     uvicorn src.main:app --reload"
echo ""
echo "  3. Or use Docker Compose for everything:"
echo "     docker-compose up"
echo ""
echo "  4. Access the API documentation:"
echo "     http://localhost:8000/docs"
echo ""
echo "Happy coding!"
echo ""
