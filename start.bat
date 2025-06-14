@echo off
REM ============================================================================
REM DJANGO RESTFUL LOGISTICS TEMPLATE - QUICK START SCRIPT (Windows)
REM ============================================================================
REM Script para inicializar rápidamente el entorno Docker en Windows

setlocal enabledelayedexpansion

REM Configuration
set "COMPOSE_FILE=docker-compose.yml"
set "ENV_FILE=.env"
set "ENV_EXAMPLE=.env.example"

echo ============================================================================
echo  DJANGO RESTFUL LOGISTICS TEMPLATE - QUICK START
echo ============================================================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not in PATH
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker Compose is not installed or not in PATH
    exit /b 1
)

echo Dependencies check passed

REM Setup environment file
if not exist "%ENV_FILE%" (
    if exist "%ENV_EXAMPLE%" (
        copy "%ENV_EXAMPLE%" "%ENV_FILE%" >nul
        echo Created .env file from .env.example
    ) else (
        echo ERROR: .env.example not found
        exit /b 1
    )
) else (
    echo WARNING: .env file already exists
)

REM Create necessary directories
if not exist "logs\nginx" mkdir "logs\nginx"
if not exist "logs\postgres" mkdir "logs\postgres"
if not exist "data\postgres" mkdir "data\postgres"
if not exist "data\redis" mkdir "data\redis"
if not exist "backups" mkdir "backups"
if not exist "nginx\ssl" mkdir "nginx\ssl"

echo Directories created

REM Parse command line arguments
set "LOAD_TEST_DATA=false"
set "BUILD_FLAG="

:parse_args
if "%~1"=="" goto start_services
if "%~1"=="--with-test-data" (
    set "LOAD_TEST_DATA=true"
    shift
    goto parse_args
)
if "%~1"=="--clean" (
    set "LOAD_TEST_DATA=false"
    shift
    goto parse_args
)
if "%~1"=="--build" (
    set "BUILD_FLAG=--build"
    shift
    goto parse_args
)
if "%~1"=="--stop" (
    echo Stopping services...
    docker-compose -f "%COMPOSE_FILE%" down
    echo Services stopped
    exit /b 0
)
if "%~1"=="--logs" (
    docker-compose -f "%COMPOSE_FILE%" logs -f
    exit /b 0
)
if "%~1"=="--help" (
    echo Usage: %0 [OPTIONS]
    echo.
    echo Options:
    echo   --with-test-data    Start with test data (LOAD_TEST_DATA=true)
    echo   --clean             Start with clean database (LOAD_TEST_DATA=false)
    echo   --build             Force rebuild of Docker images
    echo   --stop              Stop all services
    echo   --logs              Show logs
    echo   --help              Show this help message
    echo.
    echo Examples:
    echo   %0 --with-test-data    # Start with test data
    echo   %0 --clean             # Start with clean database
    echo   %0 --build --clean     # Rebuild and start clean
    exit /b 0
)
shift
goto parse_args

:start_services
echo Starting services...
echo Test data: %LOAD_TEST_DATA%

REM Set environment variable
set "LOAD_TEST_DATA=%LOAD_TEST_DATA%"

REM Start services
if defined BUILD_FLAG (
    echo Building and starting services...
    docker-compose -f "%COMPOSE_FILE%" up -d %BUILD_FLAG%
) else (
    echo Starting services...
    docker-compose -f "%COMPOSE_FILE%" up -d
)

echo Services started!

REM Wait for services to be ready
echo Waiting for services to be ready...
timeout /t 5 /nobreak >nul

REM Show service status
docker-compose -f "%COMPOSE_FILE%" ps

echo.
echo Service URLs:
echo   Main Application: http://localhost
echo   Flower (Celery):  http://localhost:5555
echo   PostgreSQL:       localhost:5432
echo   Redis:            localhost:6379
echo.
echo Default Flower credentials: admin / flower123

exit /b 0
