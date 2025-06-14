# 🚀 Django RESTful API Template - PROJECT COMPLETE

## 📋 Resumen del Proyecto

Este proyecto es una **plantilla profesional de Django** enfocada en enseñar y ejemplificar una **RESTful API avanzada** usando Django y Django REST Framework (DRF), con **arquitectura de código limpio**, inyección de dependencias, mejores estándares, reducción de código, comentarios de uso y opciones.

## ✅ Características Implementadas

### 🏗️ **Arquitectura Limpia (Clean Architecture)**

- **Domain Layer**: Entidades, Value Objects, Domain Exceptions
- **Application Layer**: Services, DTOs, Use Cases
- **Infrastructure Layer**: Django Models, Repositories, External Services
- **Presentation Layer**: REST API Views, Serializers, URL Routing
- **Shared Layer**: Common Exceptions, Permissions, Pagination, Events

### 🔐 **Sistema de Autenticación Avanzado**

- Modelo de usuario personalizado con UUID
- Autenticación JWT (Simple JWT)
- Múltiples tipos de usuario (Admin, Carrier, Logistics Operator, Customer)
- Gestión de perfiles extendidos
- Sistema de grupos y membresías personalizados
- 2FA (Two-Factor Authentication) preparado
- Password reset y email verification

### 🚛 **Sistema de Vehículos CRUD Completo**

- Gestión completa de vehículos (Create, Read, Update, Delete)
- Especificaciones técnicas detalladas
- Registro de mantenimiento
- Tracking GPS con ubicaciones
- Gestión de documentos adjuntos
- Búsqueda avanzada y filtros
- Estadísticas y reportes

### 🏛️ **Sistema de Subastas**

- Creación y gestión de subastas de vehículos
- Sistema de pujas en tiempo real
- Pujas automáticas con límite máximo
- Seguimiento de subastas (watchers)
- Estados de subasta (draft, active, completed, etc.)
- Notificaciones y eventos

### 🌐 **API RESTful Profesional**

- Endpoints completos para todas las entidades
- Serializers con validación avanzada
- Paginación personalizada
- Filtros y búsqueda
- Rate limiting y throttling
- Versionado de API

### 📚 **Documentación Automática**

- **Swagger UI** (`/api/docs/`)
- **ReDoc** (`/api/redoc/`)
- **OpenAPI Schema** (`/api/schema/`)
- Documentación de código completa
- Ejemplos de uso

### 🔧 **Panel Administrativo Personalizado**

- Admin interface mejorado para todas las entidades
- Filtros y búsqueda avanzada
- Acciones masivas
- Estadísticas y dashboards
- Exportación de datos

### 🏥 **Health Checks y Monitoring**

- Multiple endpoints de health check
- Monitoreo de base de datos
- Monitoreo de servicios externos
- Logs estructurados
- Error tracking con IDs únicos

### 🛡️ **Seguridad y Permisos**

- Permissions personalizados por tipo de usuario
- Middleware de auditoría
- Rate limiting
- CORS configurado
- Security headers
- Validación de datos robusta

### 🔄 **Signals y Eventos**

- Sistema de eventos personalizado
- Signals para auditoría
- Notificaciones automáticas
- Event sourcing preparado

### 🧪 **Estructura de Testing**

- Tests unitarios
- Tests de integración
- Tests de API endpoints
- Coverage configuration

### 🐳 **DevOps Ready**

- **Dockerfile** optimizado
- **docker-compose.yml** para desarrollo
- Multiple environments (development, testing, production)
- Environment variables management
- Logging configuration

## 📁 Estructura del Proyecto

```
django-restful-template/
├── 📁 apps/
│   ├── 📁 authentication/         # Sistema de autenticación
│   ├── 📁 users/                  # Gestión de usuarios
│   ├── 📁 vehicles/               # CRUD de vehículos
│   ├── 📁 auctions/               # Sistema de subastas
│   └── 📁 notifications/          # Notificaciones
├── 📁 config/                     # Configuración Django
│   ├── 📁 settings/               # Settings por ambiente
│   ├── asgi.py                    # ASGI config
│   ├── celery.py                  # Celery config
│   ├── urls.py                    # URL routing
│   └── wsgi.py                    # WSGI config
├── 📁 shared/                     # Código compartido
│   ├── 📁 domain/                 # Domain exceptions
│   └── 📁 infrastructure/         # Infrastructure shared
├── 📁 docs/                       # Documentación
├── 📁 static/                     # Static files
├── 📁 logs/                       # Log files
├── .env                           # Environment variables
├── .env.example                   # Environment template
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker configuration
├── docker-compose.yml             # Docker compose
├── manage.py                      # Django management
└── demo_api.py                    # API demonstration
```

## 🌐 URLs Importantes

- **Admin Panel**: http://127.0.0.1:8000/admin/
- **API Root**: http://127.0.0.1:8000/api/v1/
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/
- **Health Check**: http://127.0.0.1:8000/health/

## 👤 Usuarios de Prueba

- **admin@example.com** (superuser)
- **transportista@example.com** (carrier)
- **operador@example.com** (logistics_operator)
- **cliente@example.com** (customer)

## 🚀 Cómo Ejecutar

### Desarrollo Local

```bash
# 1. Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env

# 4. Ejecutar migraciones
python manage.py migrate

# 5. Crear datos iniciales
python manage.py setup_initial_data

# 6. Ejecutar servidor
python manage.py runserver

# 7. Ejecutar demostración
python demo_api.py
```

### Con Docker

```bash
# Ejecutar con docker-compose
docker-compose up --build
```

## 📖 Comandos Útiles

```bash
# Crear superusuario
python manage.py createsuperuser

# Ver todas las URLs
python manage.py show_urls

# Verificar proyecto
python manage.py check

# Ejecutar tests
python manage.py test

# Crear nueva migración
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Colectar static files
python manage.py collectstatic

# Shell interactivo
python manage.py shell
```

## 🎯 Próximos Pasos (Opcional)

- [ ] Implementar WebSocket con Django Channels
- [ ] Agregar Celery para tareas asíncronas
- [ ] Implementar cache con Redis
- [ ] Agregar más tests de cobertura
- [ ] Implementar CI/CD pipeline
- [ ] Agregar Elasticsearch para búsqueda
- [ ] Implementar GraphQL endpoint
- [ ] Agregar métricas con Prometheus

## 📚 Tecnologías Utilizadas

- **Django 4.2+**
- **Django REST Framework**
- **Simple JWT**
- **drf-spectacular** (OpenAPI/Swagger)
- **django-extensions**
- **django-debug-toolbar**
- **django-cors-headers**
- **Pillow** (image processing)
- **python-decouple** (environment variables)
- **whitenoise** (static files)

## 🤝 Contribución

Este proyecto sirve como template y ejemplo educativo. Siéntete libre de:

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver `LICENSE` para más detalles.

## 📞 Soporte

Para soporte y preguntas:

- 📧 Email: support@example.com
- 🐛 Issues: GitHub Issues
- 📖 Documentation: `/docs/`

---

**¡Template listo para producción!** 🎉

Este template proporciona una base sólida para cualquier proyecto Django con arquitectura limpia y mejores prácticas implementadas.

## ✨ Sistema de Notificaciones Completado

### Funcionalidades Implementadas

- **Sistema completo de notificaciones** con Clean Architecture
- **WebSocket support** para notificaciones en tiempo real (requiere Redis)
- **Múltiples tipos de notificación**: info, warning, error, success, urgent
- **Prioridades configurables**: low, normal, high, urgent, critical
- **Estados de notificación**: pending, sent, delivered, read, failed, expired
- **Canales de entrega**: websocket, email, sms, push, slack, webhook
- **Plantillas de notificación** reutilizables
- **Sistema de broadcast** para envío masivo
- **Integración con signals** de Django para eventos automáticos
- **Panel administrativo** completo con estadísticas
- **API REST completa** con filtros y paginación
- **Comando de prueba** para verificar funcionamiento

### Estructura de Notificaciones

```
apps/notifications/
├── domain/entities.py              # Entidades de dominio
├── application/
│   ├── services.py                 # Servicios de aplicación
│   ├── dtos.py                     # DTOs para transferencia
│   └── entities.py                 # Entidad simple para implementación
├── infrastructure/
│   ├── models.py                   # Modelos de base de datos
│   ├── repository.py               # Repositorio de datos
│   ├── consumers.py                # Consumidores WebSocket
│   ├── signals.py                  # Señales de infraestructura
│   └── websocket/routing.py        # Rutas WebSocket
├── presentation/
│   ├── views.py                    # Vistas API REST
│   ├── serializers.py              # Serializadores
│   └── __init__.py
├── management/commands/
│   └── test_notifications.py       # Comando de prueba
├── admin.py                        # Configuración admin
├── signals.py                      # Señales de dominio
├── urls.py                         # URLs de la app
└── models.py                       # Exposición de modelos
```

### Endpoints de Notificaciones

```bash
# API REST de notificaciones
GET    /api/v1/notifications/                    # Listar notificaciones
POST   /api/v1/notifications/                    # Crear notificación (admin)
GET    /api/v1/notifications/{id}/               # Obtener notificación
PUT    /api/v1/notifications/{id}/               # Actualizar notificación
DELETE /api/v1/notifications/{id}/               # Eliminar notificación

# Acciones específicas
POST   /api/v1/notifications/mark-all-as-read/   # Marcar todas como leídas
POST   /api/v1/notifications/{id}/mark-as-read/  # Marcar una como leída
GET    /api/v1/notifications/unread-count/       # Contador de no leídas
GET    /api/v1/notifications/stats/              # Estadísticas
GET    /api/v1/notifications/summary/            # Resumen compacto
POST   /api/v1/notifications/cleanup-expired/    # Limpiar expiradas (admin)

# Broadcast
POST   /api/v1/broadcast/all/                    # Broadcast a todos
POST   /api/v1/broadcast/group/                  # Broadcast a grupo

# WebSocket
ws://localhost:8000/ws/notifications/           # WebSocket principal
ws://localhost:8000/ws/notifications/broadcast/ # WebSocket broadcast (admin)
```

### Comandos de Gestión

```bash
# Probar sistema de notificaciones
python manage.py test_notifications

# Probar con usuario específico
python manage.py test_notifications --user-email admin@example.com

# Probar con broadcast
python manage.py test_notifications --broadcast

# Crear notificaciones de prueba
python manage.py test_notifications --count 5
```

### Tipos de Notificaciones Soportadas

1. **Notificaciones de Sistema**

   - Mantenimiento programado
   - Actualizaciones del sistema
   - Mensajes administrativos

2. **Notificaciones de Subastas**

   - Nueva subasta creada
   - Nueva puja recibida
   - Puja superada
   - Subasta ganada/perdida
   - Subasta finalizada

3. **Notificaciones de Vehículos**

   - Vehículo registrado
   - Vehículo actualizado
   - Documentos venciendo

4. **Notificaciones de Usuario**
   - Bienvenida al sistema
   - Verificación de email
   - Cambios de perfil

### Integración con WebSocket

El sistema incluye soporte completo para WebSocket usando Django Channels:

- **Conexión automática** por usuario autenticado
- **Grupos dinámicos** por usuario (`user_{user_id}`)
- **Mensajes en tiempo real** para nuevas notificaciones
- **Actualización de contadores** automática
- **Manejo de errores** y reconexión
- **Comandos interactivos** (marcar como leída, obtener lista)

### Señales Automáticas

- **Usuario creado** → Notificación de bienvenida
- **Subasta creada** → Notificación a usuarios interesados
- **Nueva puja** → Notificación al pujador anterior
- **Vehículo creado** → Notificación al propietario
