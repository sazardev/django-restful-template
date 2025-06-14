# Deployment Guide

Esta guía detalla cómo desplegar la aplicación Django RESTful Template en diferentes entornos.

## Requisitos del Sistema

### Desarrollo Local

- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Node.js 16+ (para frontend opcional)

### Producción

- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Nginx
- Gunicorn/uWSGI
- Supervisor (opcional)
- Docker (opcional)

## Configuración Local

### 1. Clonar y Configurar Entorno

```bash
# Clonar repositorio
git clone <repository-url>
cd django-restful-template

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Base de Datos

```bash
# PostgreSQL
createdb logistics_db
psql logistics_db

# Dentro de psql
CREATE USER logistics_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE logistics_db TO logistics_user;
ALTER USER logistics_user CREATEDB;
```

### 3. Variables de Entorno

Crear archivo `.env`:

```bash
# Configuración básica
DEBUG=True
SECRET_KEY=django-insecure-development-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
DATABASE_URL=postgresql://logistics_user:secure_password@localhost:5432/logistics_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Email (desarrollo)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS (desarrollo)
CORS_ALLOW_ALL_ORIGINS=True
```

### 4. Ejecutar Migraciones y Configurar Datos

```bash
# Ejecutar migraciones
python manage.py migrate

# Configurar datos iniciales
python manage.py setup_initial_data --with-demo-data

# (Opcional) Crear superusuario manual
python manage.py createsuperuser
```

### 5. Ejecutar Servicios

```bash
# Terminal 1: Django server
python manage.py runserver

# Terminal 2: Celery worker
celery -A config worker -l info

# Terminal 3: Celery beat (tareas programadas)
celery -A config beat -l info

# Terminal 4: Redis server
redis-server
```

## Deployment en Producción

### Opción 1: Deployment Tradicional (VPS/Server)

#### 1. Configurar Servidor

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3-pip python3-venv postgresql postgresql-contrib redis-server nginx supervisor

# CentOS/RHEL
sudo yum install python3-pip postgresql-server postgresql-contrib redis nginx supervisor
```

#### 2. Configurar PostgreSQL

```bash
sudo -u postgres psql

CREATE DATABASE logistics_prod;
CREATE USER logistics_prod WITH PASSWORD 'super_secure_password';
GRANT ALL PRIVILEGES ON DATABASE logistics_prod TO logistics_prod;
ALTER USER logistics_prod CREATEDB;
```

#### 3. Configurar Aplicación

```bash
# Crear usuario para la aplicación
sudo adduser logistics
sudo usermod -aG sudo logistics

# Cambiar a usuario de aplicación
sudo su - logistics

# Clonar y configurar
git clone <repository-url> /home/logistics/app
cd /home/logistics/app

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Variables de Entorno de Producción

Crear `/home/logistics/app/.env`:

```bash
# Producción
DEBUG=False
SECRET_KEY=your-super-secure-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Base de datos
DATABASE_URL=postgresql://logistics_prod:super_secure_password@localhost:5432/logistics_prod

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yourdomain.com
EMAIL_HOST_PASSWORD=your-app-password

# Seguridad
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Archivos estáticos (opcional: usar S3)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1
```

#### 5. Configurar Gunicorn

Crear `/home/logistics/app/gunicorn.conf.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "gevent"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
```

#### 6. Configurar Supervisor

Crear `/etc/supervisor/conf.d/logistics.conf`:

```ini
[program:logistics_django]
command=/home/logistics/app/venv/bin/gunicorn config.wsgi:application -c /home/logistics/app/gunicorn.conf.py
directory=/home/logistics/app
user=logistics
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/logistics_django.log

[program:logistics_celery]
command=/home/logistics/app/venv/bin/celery -A config worker -l info
directory=/home/logistics/app
user=logistics
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/logistics_celery.log

[program:logistics_celery_beat]
command=/home/logistics/app/venv/bin/celery -A config beat -l info
directory=/home/logistics/app
user=logistics
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/logistics_beat.log
```

#### 7. Configurar Nginx

Crear `/etc/nginx/sites-available/logistics`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    client_max_body_size 100M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/logistics/app/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/logistics/app/media/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 8. Deployment Final

```bash
# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/logistics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Ejecutar migraciones
cd /home/logistics/app
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py setup_initial_data

# Iniciar servicios
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### Opción 2: Deployment con Docker

#### 1. Dockerfile

```dockerfile
FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . /app/

# Crear usuario no-root
RUN addgroup --system django \
    && adduser --system --ingroup django django

# Cambiar permisos
RUN chown -R django:django /app
USER django

# Exponer puerto
EXPOSE 8000

# Comando por defecto
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]
```

#### 2. docker-compose.yml

```yaml
version: "3.8"

services:
  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - static_volume:/app/staticfiles
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      POSTGRES_DB: logistics_db
      POSTGRES_USER: logistics_user
      POSTGRES_PASSWORD: secure_password

  redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data

  celery:
    build: .
    command: celery -A config worker -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A config beat -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
      - media_volume:/app/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static_volume:
  media_volume:
```

#### 3. Ejecutar con Docker

```bash
# Construir y ejecutar
docker-compose up -d --build

# Ejecutar migraciones
docker-compose exec web python manage.py migrate

# Configurar datos iniciales
docker-compose exec web python manage.py setup_initial_data

# Ver logs
docker-compose logs -f
```

### Opción 3: Deployment en la Nube

#### AWS (usando Elastic Beanstalk)

1. **Instalar EB CLI**

```bash
pip install awsebcli
```

2. **Configurar aplicación**

```bash
eb init
eb create production
eb deploy
```

3. **Configurar variables de entorno en AWS Console**

#### Digital Ocean (usando App Platform)

1. **Crear app.yaml**

```yaml
name: logistics-api
services:
  - name: web
    source_dir: /
    github:
      repo: your-username/django-restful-template
      branch: main
    run_command: gunicorn --worker-tmp-dir /dev/shm config.wsgi
    environment_slug: python
    instance_count: 1
    instance_size_slug: basic-xxs
    envs:
      - key: DEBUG
        value: "False"
      - key: DATABASE_URL
        value: ${db.DATABASE_URL}
databases:
  - engine: PG
    name: db
    num_nodes: 1
    size: db-s-dev-database
    version: "13"
```

#### Heroku

```bash
# Instalar Heroku CLI
# Crear Procfile
echo "web: gunicorn config.wsgi" > Procfile
echo "worker: celery -A config worker -l info" >> Procfile

# Desplegar
heroku create your-app-name
heroku config:set DEBUG=False
heroku config:set SECRET_KEY=your-secret-key
heroku addons:create heroku-postgresql:hobby-dev
heroku addons:create heroku-redis:hobby-dev

git push heroku main
heroku run python manage.py migrate
heroku run python manage.py setup_initial_data
```

## Monitoreo y Mantenimiento

### 1. Logging

Configurar en `settings/production.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/django/logistics.log',
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

### 2. Monitoring

```bash
# Instalar Sentry
pip install sentry-sdk[django]

# Configurar en settings
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

### 3. Backup

```bash
#!/bin/bash
# Script de backup diario
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup de base de datos
pg_dump logistics_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Backup de archivos media
tar -czf $BACKUP_DIR/media_backup_$DATE.tar.gz /home/logistics/app/media/

# Limpiar backups antiguos (30 días)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 4. Health Checks

```python
# views.py
from django.http import JsonResponse
from django.db import connections
from django.core.cache import cache

def health_check(request):
    """Health check endpoint."""
    try:
        # Check database
        db_conn = connections['default']
        db_conn.cursor()

        # Check cache
        cache.set('health_check', 'ok', 30)
        cache_status = cache.get('health_check')

        return JsonResponse({
            'status': 'healthy',
            'database': 'ok',
            'cache': 'ok' if cache_status == 'ok' else 'error'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
```

## Troubleshooting

### Problemas Comunes

1. **Error de migración**

```bash
python manage.py migrate --fake-initial
```

2. **Archivos estáticos no se cargan**

```bash
python manage.py collectstatic --clear --noinput
```

3. **Celery no procesa tareas**

```bash
# Verificar conexión Redis
redis-cli ping

# Purgar tareas
celery -A config purge
```

4. **Error de permisos**

```bash
sudo chown -R logistics:logistics /home/logistics/app
sudo chmod -R 755 /home/logistics/app
```

### Comandos de Diagnóstico

```bash
# Ver logs de aplicación
sudo tail -f /var/log/supervisor/logistics_django.log

# Ver logs de Nginx
sudo tail -f /var/log/nginx/error.log

# Estado de servicios
sudo systemctl status nginx
sudo supervisorctl status

# Uso de recursos
htop
df -h
free -h
```
