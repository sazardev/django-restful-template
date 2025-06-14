# API Usage Examples

Esta documentación proporciona ejemplos prácticos de uso de la API RESTful del sistema logístico.

## Autenticación

### Obtener Token JWT

```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "transportista@example.com",
    "password": "transport123"
  }'
```

Respuesta:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "transportista@example.com",
    "first_name": "Carlos",
    "last_name": "Transportista",
    "user_type": "carrier"
  }
}
```

### Usar Token en Peticiones

```bash
curl -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  http://localhost:8000/api/v1/vehicles/
```

## Gestión de Vehículos

### Crear un Vehículo

```bash
curl -X POST http://localhost:8000/api/v1/vehicles/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "license_plate": "ABC123",
    "brand": "Mercedes",
    "model": "Actros",
    "year": 2022,
    "color": "Blanco",
    "vehicle_type": "truck",
    "specifications": {
      "max_weight_kg": "40000.00",
      "max_volume_m3": "100.00",
      "fuel_type": "diesel",
      "fuel_capacity_liters": "400.00",
      "engine_power_hp": 450
    },
    "owner_id": "123e4567-e89b-12d3-a456-426614174000"
  }'
```

### Listar Vehículos con Filtros

```bash
# Vehículos disponibles
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/vehicles/?status=available"

# Vehículos por tipo
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/vehicles/?vehicle_type=truck"

# Vehículos con capacidad mínima
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/vehicles/?min_weight_capacity=20000"
```

### Actualizar Ubicación de Vehículo

```bash
curl -X POST http://localhost:8000/api/v1/vehicles/{vehicle_id}/update-location/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "latitude": "19.4326",
    "longitude": "-99.1332",
    "accuracy_meters": "5.0",
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

### Asignar Conductor

```bash
curl -X POST http://localhost:8000/api/v1/vehicles/{vehicle_id}/assign-driver/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": "456e7890-e89b-12d3-a456-426614174001"
  }'
```

## Gestión de Subastas

### Crear una Subasta

```bash
curl -X POST http://localhost:8000/api/v1/auctions/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Transporte CDMX - Guadalajara",
    "description": "Envío de productos electrónicos",
    "auction_type": "reverse",
    "starting_price": "50000.00",
    "shipment_details": {
      "origin_address": "Ciudad de México, CDMX",
      "destination_address": "Guadalajara, Jalisco",
      "pickup_date": "2024-02-01T08:00:00Z",
      "delivery_date": "2024-02-02T18:00:00Z",
      "weight_kg": "15000.00",
      "volume_m3": "50.00",
      "cargo_description": "Productos electrónicos"
    },
    "requirements": {
      "min_vehicle_capacity_kg": "20000.00",
      "required_vehicle_types": ["truck"],
      "insurance_coverage_required": true
    },
    "start_time": "2024-01-20T09:00:00Z",
    "end_time": "2024-01-25T17:00:00Z"
  }'
```

### Hacer una Oferta

```bash
curl -X POST http://localhost:8000/api/v1/auctions/{auction_id}/bids/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": "45000.00",
    "notes": "Incluye seguro completo y seguimiento GPS"
  }'
```

### Listar Subastas Activas

```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/auctions/?status=active"
```

## Notificaciones en Tiempo Real

### Conectar a WebSocket

```javascript
// Cliente JavaScript
const socket = new WebSocket(
  'ws://localhost:8000/ws/notifications/',
  ['authorization', 'Bearer ' + token]
);

socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Notificación recibida:', data);
};

socket.onopen = function(event) {
  console.log('Conectado a notificaciones');
};
```

### Enviar Notificación

```bash
curl -X POST http://localhost:8000/api/v1/notifications/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Nueva oferta recibida",
    "message": "Has recibido una nueva oferta de $45,000 en tu subasta",
    "notification_type": "info",
    "priority": 3,
    "recipient_id": "123e4567-e89b-12d3-a456-426614174000",
    "channels": ["web", "email"]
  }'
```

## Análisis y Reportes

### Métricas de Flota

```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/vehicles/analytics/fleet/"
```

Respuesta:
```json
{
  "total_vehicles": 25,
  "active_vehicles": 20,
  "in_maintenance": 3,
  "available_vehicles": 15,
  "average_age_years": 4.2,
  "total_capacity_weight_kg": "1000000.00",
  "total_capacity_volume_m3": "2500.00",
  "utilization_rate": 80.0,
  "maintenance_cost_trend": {
    "2024-01": 15000.00,
    "2024-02": 12000.00
  }
}
```

### Estadísticas de Utilización

```bash
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/vehicles/analytics/utilization/?start_date=2024-01-01&end_date=2024-01-31"
```

## Casos de Uso Comunes

### 1. Flujo Completo de Subasta

```bash
# 1. Cliente crea subasta
AUCTION_ID=$(curl -X POST http://localhost:8000/api/v1/auctions/ \
  -H "Authorization: Bearer CLIENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}' | jq -r '.id')

# 2. Transportista hace oferta
curl -X POST http://localhost:8000/api/v1/auctions/$AUCTION_ID/bids/ \
  -H "Authorization: Bearer CARRIER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": "45000.00"}'

# 3. Cliente acepta oferta
curl -X POST http://localhost:8000/api/v1/auctions/$AUCTION_ID/end/ \
  -H "Authorization: Bearer CLIENT_TOKEN"
```

### 2. Seguimiento de Vehículo en Ruta

```bash
# Obtener ruta histórica
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/vehicles/{vehicle_id}/route/?start_date=2024-01-15T00:00:00Z&end_date=2024-01-15T23:59:59Z"

# Obtener ubicación actual
curl -H "Authorization: Bearer TOKEN" \
  "http://localhost:8000/api/v1/vehicles/{vehicle_id}/current-location/"
```

### 3. Mantenimiento Programado

```bash
# Programar mantenimiento
curl -X POST http://localhost:8000/api/v1/vehicles/{vehicle_id}/schedule-maintenance/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "maintenance_type": "preventive",
    "description": "Mantenimiento preventivo trimestral",
    "scheduled_date": "2024-02-15T09:00:00Z"
  }'

# Completar mantenimiento
curl -X POST http://localhost:8000/api/v1/vehicles/{vehicle_id}/complete-maintenance/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "maintenance_type": "preventive",
    "description": "Mantenimiento preventivo completado",
    "cost": "5000.00",
    "performed_by": "Taller Mecánico ABC",
    "mileage_km": "150000.00"
  }'
```

## Códigos de Error Comunes

| Código | Descripción | Solución |
|--------|-------------|----------|
| 401 | No autenticado | Incluir token JWT válido |
| 403 | Sin permisos | Verificar permisos del usuario |
| 404 | Recurso no encontrado | Verificar ID del recurso |
| 400 | Datos inválidos | Revisar formato de datos |
| 429 | Demasiadas peticiones | Implementar rate limiting |

## Variables de Entorno

```bash
# Configuración básica
export DEBUG=True
export SECRET_KEY=your-secret-key
export DATABASE_URL=postgresql://user:pass@localhost/dbname

# Redis para cache y Celery
export REDIS_URL=redis://localhost:6379/0

# Email
export EMAIL_HOST=smtp.gmail.com
export EMAIL_PORT=587
export EMAIL_HOST_USER=your-email@gmail.com
export EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (opcional)
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

## Comandos Útiles

```bash
# Configurar datos iniciales
python manage.py setup_initial_data --with-demo-data

# Ejecutar migraciones
python manage.py migrate

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver

# Ejecutar worker de Celery
celery -A config worker -l info

# Ejecutar Celery Beat (tareas programadas)
celery -A config beat -l info

# Ejecutar tests
python manage.py test

# Generar esquema OpenAPI
python manage.py spectacular --file schema.yml
```
