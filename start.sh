#!/bin/bash

# ============================================================================
# DJANGO RESTFUL LOGISTICS TEMPLATE - QUICK START SCRIPT
# ============================================================================
# Script para inicializar rápidamente el entorno Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "============================================================================"
    echo " DJANGO RESTFUL LOGISTICS TEMPLATE - QUICK START"
    echo "============================================================================"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    print_success "Dependencies check passed"
}

setup_environment() {
    print_info "Setting up environment..."
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            print_success "Created .env file from .env.example"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_warning ".env file already exists"
    fi
}

create_directories() {
    print_info "Creating necessary directories..."
    
    mkdir -p logs/nginx
    mkdir -p logs/postgres
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p backups
    mkdir -p nginx/ssl
    
    print_success "Directories created"
}

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --with-test-data    Start with test data (LOAD_TEST_DATA=true)"
    echo "  --clean             Start with clean database (LOAD_TEST_DATA=false)"
    echo "  --build             Force rebuild of Docker images"
    echo "  --stop              Stop all services"
    echo "  --logs              Show logs"
    echo "  --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --with-test-data    # Start with test data"
    echo "  $0 --clean             # Start with clean database"
    echo "  $0 --build --clean     # Rebuild and start clean"
}

start_services() {
    local load_test_data="false"
    local build_flag=""
    
    # Parse options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --with-test-data)
                load_test_data="true"
                shift
                ;;
            --clean)
                load_test_data="false"
                shift
                ;;
            --build)
                build_flag="--build"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    print_info "Starting services..."
    print_info "Test data: $load_test_data"
    
    # Set environment variable
    export LOAD_TEST_DATA=$load_test_data
    
    # Start services
    if [ -n "$build_flag" ]; then
        print_info "Building and starting services..."
        docker-compose -f "$COMPOSE_FILE" up -d $build_flag
    else
        print_info "Starting services..."
        docker-compose -f "$COMPOSE_FILE" up -d
    fi
    
    print_success "Services started!"
    
    # Wait a moment for services to be ready
    print_info "Waiting for services to be ready..."
    sleep 5
    
    # Show service status
    docker-compose -f "$COMPOSE_FILE" ps
    
    print_info "Service URLs:"
    echo "  🌐 Main Application: http://localhost"
    echo "  📊 Flower (Celery): http://localhost:5555"
    echo "  🐘 PostgreSQL:      localhost:5432"
    echo "  🔴 Redis:           localhost:6379"
    echo ""
    print_info "Default Flower credentials: admin / flower123"
}

stop_services() {
    print_info "Stopping services..."
    docker-compose -f "$COMPOSE_FILE" down
    print_success "Services stopped"
}

show_logs() {
    docker-compose -f "$COMPOSE_FILE" logs -f
}

# Main script
print_header

case "${1:-}" in
    --help)
        show_usage
        exit 0
        ;;
    --stop)
        stop_services
        exit 0
        ;;
    --logs)
        show_logs
        exit 0
        ;;
    *)
        check_dependencies
        setup_environment
        create_directories
        start_services "$@"
        ;;
esac
