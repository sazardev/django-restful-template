# 🚀 Django RESTful API Template

[![Django](https://img.shields.io/badge/Django-4.2+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14+-ff1709?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

> **Plantilla profesional de Django** enfocada en enseñar y ejemplificar una **RESTful API avanzada** usando Django y Django REST Framework (DRF), con **arquitectura de código limpio**, inyección de dependencias, mejores estándares y documentación completa.

## 🎯 Características Principales

### ✅ **Arquitectura Limpia Implementada**

- **Domain Layer**: Entidades de negocio y reglas de dominio
- **Application Layer**: Casos de uso y servicios de aplicación
- **Infrastructure Layer**: Implementaciones de bases de datos y servicios externos
- **Presentation Layer**: APIs REST, serializers y views
- **Shared Layer**: Código compartido y utilidades

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

## 🚀 Quick Start

### 1. **Clonar y Configurar**

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/django-restful-template.git
cd django-restful-template

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt
```

### 2. **Configurar Variables de Entorno**

```bash
# Copiar template de variables
cp .env.example .env

# Editar .env con tus configuraciones
# SECRET_KEY, DATABASE_URL, etc.
```

### 3. **Inicializar Base de Datos**

```bash
# Ejecutar migraciones
python manage.py migrate

# Crear datos iniciales y usuarios de prueba
python manage.py setup_initial_data

# Crear superusuario (opcional)
python manage.py createsuperuser
```

### 4. **Ejecutar el Servidor**

```bash
# Modo desarrollo
python manage.py runserver

# Verificar funcionamiento
python demo_api.py
```

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
```

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
