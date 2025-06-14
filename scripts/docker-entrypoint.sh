#!/bin/bash
# ============================================================================
# DJANGO RESTFUL LOGISTICS TEMPLATE - DOCKER ENTRYPOINT SCRIPT
# ============================================================================
# Script de inicialización para contenedores Docker

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Función para esperar que un servicio esté disponible
wait_for_service() {
    local host=$1
    local port=$2
    local service_name=$3
    local timeout=${4:-60}
    
    log "Waiting for $service_name to be ready at $host:$port..."
    
    for i in $(seq 1 $timeout); do
        if nc -z "$host" "$port" 2>/dev/null; then
            success "$service_name is ready!"
            return 0
        fi
        sleep 1
    done
    
    error "$service_name is not ready after $timeout seconds"
    return 1
}

# Función para verificar variables de entorno requeridas
check_env_vars() {
    local required_vars=(
        "DATABASE_NAME"
        "DATABASE_USER"
        "DATABASE_PASSWORD"
        "DATABASE_HOST"
        "SECRET_KEY"
        "REDIS_URL"
    )
    
    log "Checking required environment variables..."
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    success "All required environment variables are set"
}

# Función para ejecutar migraciones de base de datos
run_migrations() {
    log "Running database migrations..."
    
    if python manage.py migrate --noinput; then
        success "Database migrations completed successfully"
    else
        error "Database migrations failed"
        exit 1
    fi
}

# Función para recopilar archivos estáticos
collect_static() {
    log "Collecting static files..."
    
    if python manage.py collectstatic --noinput; then
        success "Static files collected successfully"
    else
        warning "Failed to collect static files"
    fi
}

# Función para crear superusuario si no existe
create_superuser() {
    if [ "$DJANGO_SUPERUSER_EMAIL" ] && [ "$DJANGO_SUPERUSER_PASSWORD" ]; then
        log "Creating superuser if it doesn't exist..."
        
        python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD',
        first_name='${DJANGO_SUPERUSER_FIRST_NAME:-Admin}',
        last_name='${DJANGO_SUPERUSER_LAST_NAME:-User}'
    )
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF
        success "Superuser check completed"
    fi
}

# Función para cargar datos de prueba
load_test_data() {
    if [ "$LOAD_TEST_DATA" = "true" ]; then
        log "Loading test data..."
        
        if python manage.py setup_initial_data; then
            success "Test data loaded successfully"
        else
            warning "Failed to load test data"
        fi
    else
        log "Skipping test data loading (LOAD_TEST_DATA=$LOAD_TEST_DATA)"
    fi
}

# Función para verificar la salud del sistema
health_check() {
    log "Performing health check..."
    
    # Verificar conexión a la base de datos
    if python manage.py check --database default; then
        success "Database connection OK"
    else
        error "Database connection failed"
        exit 1
    fi
    
    # Verificar conexión a Redis
    if python -c "
import redis
import os
from urllib.parse import urlparse
url = urlparse(os.environ.get('REDIS_URL', 'redis://redis:6379/0'))
r = redis.Redis(host=url.hostname, port=url.port, db=url.path[1:] if url.path else 0)
r.ping()
print('Redis connection OK')
"; then
        success "Redis connection OK"
    else
        error "Redis connection failed"
        exit 1
    fi
}

# Función principal
main() {
    log "Starting Django Logistics Template initialization..."
    
    # Verificar variables de entorno
    check_env_vars
    
    # Esperar a que los servicios estén disponibles
    if [ "$DATABASE_HOST" != "localhost" ] && [ "$DATABASE_HOST" != "127.0.0.1" ]; then
        wait_for_service "$DATABASE_HOST" "${DATABASE_PORT:-5432}" "PostgreSQL"
    fi
    
    if [ "$REDIS_URL" ]; then
        redis_host=$(echo "$REDIS_URL" | cut -d'/' -f3 | cut -d':' -f1)
        redis_port=$(echo "$REDIS_URL" | cut -d'/' -f3 | cut -d':' -f2)
        if [ "$redis_host" != "localhost" ] && [ "$redis_host" != "127.0.0.1" ]; then
            wait_for_service "$redis_host" "${redis_port:-6379}" "Redis"
        fi
    fi
    
    # Verificar salud del sistema
    health_check
    
    # Ejecutar migraciones
    run_migrations
    
    # Recopilar archivos estáticos (solo para web server)
    if [[ "$*" == *"gunicorn"* ]] || [[ "$*" == *"runserver"* ]]; then
        collect_static
    fi
    
    # Crear superusuario
    create_superuser
    
    # Cargar datos de prueba
    load_test_data
    
    success "Initialization completed successfully!"
    log "Starting application with command: $*"
    
    # Ejecutar el comando pasado como argumentos
    exec "$@"
}

# Manejo de señales para graceful shutdown
trap 'log "Received shutdown signal, stopping..."; exit 0' SIGTERM SIGINT

# Ejecutar función principal
main "$@"
