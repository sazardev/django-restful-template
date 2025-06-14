# 🚀 Django RESTful API Template

[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14+-ff1709?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

> **Plantilla profesional de Django** enfocada en enseñar y ejemplificar una **RESTful API avanzada** usando Django y Django REST Framework (DRF), con **arquitectura de código limpio**, inyección de dependencias, mejores estándares y documentación completa.

## ⚡ Quick Start - Un Solo Comando

### 🐳 Docker "Todo en Uno" (Recomendado)

```bash
# 1. Clona el repositorio
git clone <repository-url>
cd django-restful-template

# 2. Inicia con datos de prueba (recomendado para testing)
./start.sh --with-test-data

# O inicia con base de datos limpia
./start.sh --clean

# En Windows
start.bat --with-test-data
```

**¡Eso es todo!** 🎉 En pocos minutos tendrás:

- 🌐 **API completa**: http://localhost
- 📊 **Monitoreo Celery**: http://localhost:5555 (admin/flower123)
- 🐘 **PostgreSQL**: localhost:5432
- 🔴 **Redis**: localhost:6379
- 📚 **Swagger Docs**: http://localhost/api/docs/

### 🏗️ Servicios Incluidos

| Servicio       | Puerto | Descripción                   |
| -------------- | ------ | ----------------------------- |
| **Nginx**      | 80/443 | Reverse proxy + Static files  |
| **Django**     | 8000   | API REST principal            |
| **WebSocket**  | 8001   | Notificaciones en tiempo real |
| **PostgreSQL** | 5432   | Base de datos principal       |
| **Redis**      | 6379   | Cache + Message broker        |
| **Celery**     | -      | Tareas asíncronas             |
| **Flower**     | 5555   | Monitoreo de Celery           |

## 🎯 Características Principales

### ✅ **Arquitectura Limpia Implementada**

- **Domain Layer**: Entidades de negocio y reglas de dominio
- **Application Layer**: Casos de uso y servicios de aplicación
- **Infrastructure Layer**: Implementaciones de bases de datos y servicios externos
- **Presentation Layer**: APIs REST, serializers y views
- **Shared Layer**: Código compartido y utilidades

### 🔔 **Sistema de Notificaciones en Tiempo Real**

- **WebSocket** con Django Channels
- **Celery** para tareas asíncronas
- **Redis** como message broker
- Notificaciones push y por email
- Dashboard de administración

### 🔐 **Sistema de Autenticación Avanzado**

- Modelo de usuario personalizado con UUID
- Autenticación JWT con refresh tokens
- Múltiples roles de usuario (Admin, Carrier, Logistics, Customer)
- 2FA (preparado para implementar)
- Password reset y verificación de email
- Gestión de sesiones y seguridad

### 🚛 **Sistema Logístico Completo**

- **Vehículos**: CRUD completo con especificaciones técnicas
- **Subastas**: Sistema de pujas en tiempo real
- **Mantenimiento**: Historial y programación
- **Tracking**: Ubicaciones GPS y rutas
- **Documentos**: Gestión de archivos y certificados

### 🌐 **API RESTful Profesional**

- Endpoints completamente documentados
- Paginación y filtros avanzados
- Rate limiting y throttling
- Versionado de API
- Validación robusta de datos
- Error handling consistente

### 📚 **Documentación Automática**

- **Swagger UI** interactivo (`/api/docs/`)
- **ReDoc** elegante (`/api/redoc/`)
- **OpenAPI 3.0** Schema (`/api/schema/`)
- Ejemplos de código y testing

### 🏥 **Monitoring y Health Checks**

- Multiple endpoints de salud
- Logging estructurado
- Error tracking con UUIDs
- Métricas de performance

## 🚀 Opciones de Instalación

### Opción 1: Docker (Recomendado) 🐳

El método más fácil es usar Docker. Todo está preconfigurado:

```bash
# Clonar repositorio
git clone <repository-url>
cd django-restful-template

# Iniciar con datos de prueba
./start.sh --with-test-data     # Linux/Mac
start.bat --with-test-data      # Windows

# O iniciar con BD limpia
./start.sh --clean
```

### Opción 2: Desarrollo Local 💻

Si prefieres desarrollo local sin Docker:

```bash
# 1. Clonar y configurar entorno
git clone <repository-url>
cd django-restful-template
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu configuración

# 3. Configurar servicios externos
# Instalar PostgreSQL y Redis localmente
# O usar Docker solo para estos servicios:
docker run -d --name postgres -p 5432:5432 -e POSTGRES_DB=logistics_db postgres:15
docker run -d --name redis -p 6379:6379 redis:7-alpine

# 4. Inicializar BD
python manage.py wait_for_db
python manage.py migrate
python manage.py setup_initial_data  # Datos de prueba

# 5. Ejecutar servicios
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A config worker -l info

# Terminal 3: Celery Beat
celery -A config beat -l info

# Terminal 4: WebSocket (opcional)
daphne -p 8001 config.asgi:application
```

## 🔧 Comandos de Gestión

### Scripts de Inicio Rápido

```bash
# Datos de prueba vs limpio
./start.sh --with-test-data    # Con usuarios, vehículos, subastas de ejemplo
./start.sh --clean             # Solo estructura de BD

# Opciones adicionales
./start.sh --build             # Rebuild containers
./start.sh --stop              # Parar todos los servicios
./start.sh --logs              # Ver logs en tiempo real
```

### Comandos Docker

```bash
# Ver estado de servicios
docker-compose ps

# Ver logs específicos
docker-compose logs web
docker-compose logs celery
docker-compose logs flower

# Ejecutar comandos Django
docker-compose exec web python manage.py shell
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py test

# Acceder a contenedor
docker-compose exec web bash
```

### Desarrollo y Testing

```bash
# Ejecutar tests
docker-compose exec web python manage.py test

# Linter y formato
docker-compose exec web flake8
docker-compose exec web black .

# Crear nueva app
docker-compose exec web python manage.py startapp nueva_app
```

# Modo desarrollo

python manage.py runserver

# Verificar funcionamiento

python demo_api.py

````

### 5. **Explorar la API**

- 🏠 **Admin Panel**: http://127.0.0.1:8000/admin/
- 📖 **Swagger UI**: http://127.0.0.1:8000/api/docs/
- 📘 **ReDoc**: http://127.0.0.1:8000/api/redoc/
- 🔍 **Health Check**: http://127.0.0.1:8000/health/
- 🌐 **API Root**: http://127.0.0.1:8000/api/v1/

## 🐳 Docker Setup

```bash
# Ejecutar con Docker Compose
docker-compose up --build

# En background
docker-compose up -d

# Ver logs
docker-compose logs -f
````

## 👤 Usuarios de Prueba

El comando `setup_initial_data` crea usuarios de ejemplo:

| Email                     | Rol       | Password         |
| ------------------------- | --------- | ---------------- |
| admin@example.com         | Superuser | (auto-generated) |
| transportista@example.com | Carrier   | transport123     |
| operador@example.com      | Logistics | operator123      |
| cliente@example.com       | Customer  | client123        |

## 📁 Estructura del Proyecto

```
django-restful-template/
├── 📱 apps/                    # Aplicaciones Django
│   ├── authentication/        # Sistema de autenticación
│   ├── users/                 # Gestión de usuarios
│   ├── vehicles/              # CRUD de vehículos
│   ├── auctions/              # Sistema de subastas
│   └── notifications/         # Notificaciones
├── ⚙️ config/                  # Configuración
│   ├── settings/              # Settings por ambiente
│   ├── urls.py               # URL routing principal
│   └── celery.py             # Configuración Celery
├── 🔧 shared/                  # Código compartido
│   ├── domain/               # Excepciones de dominio
│   └── infrastructure/       # Infraestructura común
├── 📚 docs/                    # Documentación
├── 🐳 docker-compose.yml       # Docker Compose
├── 📋 requirements.txt         # Dependencias Python
└── 🚀 demo_api.py             # Script de demostración
```

## 🔧 Comandos Útiles

```bash
# 🔍 Verificar el proyecto
python manage.py check

# 📊 Ver todas las URLs
python manage.py show_urls

# 🧪 Ejecutar tests
python manage.py test

# 📝 Crear migraciones
python manage.py makemigrations

# 🔄 Aplicar migraciones
python manage.py migrate

# 📁 Colectar archivos estáticos
python manage.py collectstatic

# 💬 Shell interactivo
python manage.py shell
```

## 🌟 Casos de Uso

Este template es ideal para:

- 🚛 **Sistemas Logísticos**: Gestión de flotas y transporte
- 🏪 **Marketplaces**: Plataformas de compra/venta
- 🔄 **Sistemas de Subastas**: Pujas en tiempo real
- 📱 **APIs Backend**: Para aplicaciones móviles/web
- 🏢 **ERPs**: Sistemas de gestión empresarial
- 🎓 **Proyectos Educativos**: Aprender Django + DRF

## 🛠️ Tecnologías

### Backend

- **Django 4.2+**: Framework web principal
- **Django REST Framework**: API REST
- **Simple JWT**: Autenticación JWT
- **drf-spectacular**: Documentación OpenAPI

### Base de Datos

- **SQLite**: Desarrollo (incluido)
- **PostgreSQL**: Producción (recomendado)
- **MySQL**: Alternativa soportada

### DevOps

- **Docker & Docker Compose**: Containerización
- **WhiteNoise**: Servir archivos estáticos
- **python-decouple**: Variables de entorno

### Desarrollo

- **django-debug-toolbar**: Debug en desarrollo
- **django-extensions**: Comandos útiles
- **django-cors-headers**: CORS para frontend

## 📈 Roadmap

### ✅ Completado (v1.0)

- [x] Arquitectura limpia implementada
- [x] Sistema de usuarios y autenticación
- [x] CRUD de vehículos completo
- [x] Sistema de subastas básico
- [x] API REST documentada
- [x] Panel administrativo
- [x] Health checks y monitoring
- [x] Docker setup

### 🔄 En Progreso (v1.1)

- [ ] WebSocket con Django Channels
- [ ] Notificaciones en tiempo real
- [ ] Tests de cobertura completa
- [ ] CI/CD pipeline

### 🎯 Futuro (v2.0)

- [ ] Cache con Redis
- [ ] Celery para tareas asíncronas
- [ ] Elasticsearch para búsqueda
- [ ] GraphQL endpoint
- [ ] Métricas con Prometheus

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

## 🆘 Soporte

- 📧 **Email**: support@example.com
- 🐛 **Issues**: [GitHub Issues](https://github.com/tu-usuario/django-restful-template/issues)
- 📖 **Docs**: [Documentation](./docs/)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/tu-usuario/django-restful-template/discussions)

---

<div align="center">

**¡Template listo para producción!** 🎉

[![GitHub stars](https://img.shields.io/github/stars/tu-usuario/django-restful-template?style=social)](https://github.com/tu-usuario/django-restful-template)
[![GitHub forks](https://img.shields.io/github/forks/tu-usuario/django-restful-template?style=social)](https://github.com/tu-usuario/django-restful-template/fork)

</div>
