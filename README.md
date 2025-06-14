# 🚛 Django RESTful Logistics Template

Una plantilla profesional de Django REST API enfocada en un sistema logístico completo, implementando las mejores prácticas de desarrollo, arquitectura limpia e inyección de dependencias.

## 🌟 Características Principales

### 🏗️ Arquitectura

- **Clean Architecture**: Separación clara de capas (Domain, Application, Infrastructure)
- **Dependency Injection**: Inyección de dependencias con interfaces
- **Repository Pattern**: Abstracción de acceso a datos
- **Service Layer**: Lógica de negocio encapsulada
- **CQRS Pattern**: Separación de comandos y consultas

### 🔐 Seguridad

- **JWT Authentication**: Autenticación con tokens JWT
- **Role-based Access Control**: Control de acceso basado en roles
- **Group Permissions**: Permisos granulares por grupos
- **API Throttling**: Limitación de requests
- **CORS Configuration**: Configuración de CORS segura

### 📊 Sistema Logístico

- **Gestión de Vehículos**: CRUD completo de vehículos
- **Sistema de Subastas**: Subastas en tiempo real
- **Tracking en Tiempo Real**: WebSockets para seguimiento
- **Notificaciones**: Sistema de notificaciones push
- **Historial de Procesos**: Auditoría completa de acciones

### 🛠️ Tecnologías

- **Django 4.2**: Framework web robusto
- **Django REST Framework**: API REST potente
- **PostgreSQL**: Base de datos relacional
- **Redis**: Cache y message broker
- **Celery**: Tareas asíncronas
- **Channels**: WebSockets para tiempo real
- **JWT**: Autenticación segura

### 📚 Documentación

- **OpenAPI/Swagger**: Documentación automática de API
- **Docstrings**: Documentación completa del código
- **Type Hints**: Tipado estático para mejor desarrollo

## 🚀 Instalación Rápida

### Prerrequisitos

- Python 3.9+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (para frontend opcional)

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd django-restful-template
```

### 2. Crear y activar entorno virtual

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 5. Configurar base de datos

```bash
# Crear base de datos PostgreSQL
createdb logistics_db

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Cargar datos de prueba
python manage.py loaddata fixtures/initial_data.json
```

### 6. Ejecutar servidor de desarrollo

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A config worker -l info

# Terminal 3: Celery Beat
celery -A config beat -l info
```

## 📁 Estructura del Proyecto

```
django-restful-template/
├── 📁 config/                    # Configuración principal
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py              # Configuración base
│   │   ├── development.py       # Configuración desarrollo
│   │   ├── production.py        # Configuración producción
│   │   └── testing.py           # Configuración testing
│   ├── urls.py                  # URLs principales
│   ├── wsgi.py                  # WSGI config
│   ├── asgi.py                  # ASGI config (WebSockets)
│   └── celery.py               # Configuración Celery
│
├── 📁 apps/                      # Aplicaciones del proyecto
│   ├── 📁 authentication/       # Sistema de autenticación
│   │   ├── domain/              # Lógica de dominio
│   │   ├── application/         # Casos de uso
│   │   ├── infrastructure/      # Implementaciones
│   │   └── presentation/        # Controllers/Views
│   │
│   ├── 📁 users/                # Gestión de usuarios
│   ├── 📁 vehicles/             # Gestión de vehículos
│   ├── 📁 auctions/             # Sistema de subastas
│   ├── 📁 notifications/        # Sistema de notificaciones
│   ├── 📁 logistics/            # Lógica logística
│   └── 📁 audit/                # Auditoría y logs
│
├── 📁 shared/                    # Código compartido
│   ├── 📁 domain/               # Interfaces y abstracciones
│   ├── 📁 infrastructure/       # Implementaciones comunes
│   └── 📁 utils/                # Utilidades
│
├── 📁 tests/                     # Tests organizados
├── 📁 docs/                      # Documentación
├── 📁 fixtures/                  # Datos de prueba
├── 📁 media/                     # Archivos multimedia
├── 📁 static/                    # Archivos estáticos
└── 📁 logs/                      # Archivos de log
```

## 🔑 Usuarios y Roles por Defecto

### Roles del Sistema

- **Super Admin**: Acceso completo al sistema
- **Logistics Manager**: Gestión de operaciones logísticas
- **Fleet Manager**: Gestión de flota de vehículos
- **Auction Manager**: Gestión de subastas
- **Driver**: Conductor de vehículos
- **Client**: Cliente del sistema logístico

### Usuarios de Prueba

```
Super Admin:
- Username: admin
- Password: admin123

Logistics Manager:
- Username: logistics_manager
- Password: logistics123

Fleet Manager:
- Username: fleet_manager
- Password: fleet123

Driver:
- Username: driver1
- Password: driver123

Client:
- Username: client1
- Password: client123
```

## 🌐 API Endpoints

### 📋 Documentación de API

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### 🔐 Autenticación

```
POST /api/auth/login/          # Login
POST /api/auth/logout/         # Logout
POST /api/auth/register/       # Registro
POST /api/auth/refresh/        # Refresh token
POST /api/auth/password/reset/ # Reset password
```

### 👥 Usuarios

```
GET    /api/users/           # Listar usuarios
POST   /api/users/           # Crear usuario
GET    /api/users/{id}/      # Obtener usuario
PUT    /api/users/{id}/      # Actualizar usuario
DELETE /api/users/{id}/      # Eliminar usuario
GET    /api/users/me/        # Perfil actual
```

### 🚛 Vehículos

```
GET    /api/vehicles/         # Listar vehículos
POST   /api/vehicles/         # Crear vehículo
GET    /api/vehicles/{id}/    # Obtener vehículo
PUT    /api/vehicles/{id}/    # Actualizar vehículo
DELETE /api/vehicles/{id}/    # Eliminar vehículo
GET    /api/vehicles/{id}/tracking/ # Tracking en tiempo real
```

### 🏆 Subastas

```
GET    /api/auctions/         # Listar subastas
POST   /api/auctions/         # Crear subasta
GET    /api/auctions/{id}/    # Obtener subasta
POST   /api/auctions/{id}/bid/ # Realizar puja
GET    /api/auctions/{id}/bids/ # Listar pujas
```

### 🔔 Notificaciones

```
GET    /api/notifications/    # Listar notificaciones
POST   /api/notifications/mark-read/{id}/ # Marcar como leída
DELETE /api/notifications/{id}/ # Eliminar notificación
```

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest

# Tests con cobertura
pytest --cov=apps

# Tests específicos
pytest apps/vehicles/tests/

# Tests de integración
pytest tests/integration/
```

### Estructura de Tests

```
tests/
├── unit/           # Tests unitarios
├── integration/    # Tests de integración
├── e2e/           # Tests end-to-end
└── fixtures/      # Datos de prueba
```

## 🔧 Desarrollo

### Comandos Útiles

```bash
# Formatear código
black .
isort .

# Linting
flake8

# Generar migraciones
python manage.py makemigrations

# Ejecutar migraciones
python manage.py migrate

# Crear app
python manage.py startapp nombre_app

# Shell de Django
python manage.py shell

# Recolectar archivos estáticos
python manage.py collectstatic
```

### Pre-commit Hooks

```bash
# Instalar pre-commit
pre-commit install

# Ejecutar en todos los archivos
pre-commit run --all-files
```

## 🚀 Despliegue

### Docker (Recomendado)

```bash
# Construir imagen
docker build -t logistics-api .

# Ejecutar con docker-compose
docker-compose up -d
```

### Producción Manual

```bash
# Instalar dependencias de producción
pip install -r requirements/production.txt

# Configurar variables de entorno
export DJANGO_SETTINGS_MODULE=config.settings.production

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Ejecutar con Gunicorn
gunicorn config.wsgi:application
```

## 📊 Monitoreo

### Logs

Los logs se guardan en `logs/django.log` y están configurados con diferentes niveles:

- **DEBUG**: Información detallada de debugging
- **INFO**: Información general
- **WARNING**: Advertencias
- **ERROR**: Errores
- **CRITICAL**: Errores críticos

### Métricas

- **Performance**: Tiempo de respuesta de APIs
- **Usage**: Uso de endpoints
- **Errors**: Tracking de errores
- **Security**: Intentos de acceso no autorizado

## 🤝 Contribución

1. Fork del proyecto
2. Crear rama feature (`git checkout -b feature/nueva-caracteristica`)
3. Commit cambios (`git commit -am 'Agregar nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crear Pull Request

### Estándares de Código

- **PEP 8**: Seguir estándares de Python
- **Type Hints**: Usar tipado estático
- **Docstrings**: Documentar funciones y clases
- **Tests**: Mantener cobertura >90%

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 🆘 Soporte

- **Issues**: Reportar bugs en GitHub Issues
- **Documentación**: Ver carpeta `docs/`
- **Email**: soporte@logistics-template.com

---

## 🎯 Próximas Características

- [ ] Integración con servicios de mapas
- [ ] Sistema de reportes avanzados
- [ ] Mobile API endpoints
- [ ] Integración con proveedores logísticos
- [ ] Dashboard en tiempo real
- [ ] Análisis predictivo con ML

---

**¡Hecho con ❤️ para la comunidad Django!**
