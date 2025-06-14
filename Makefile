# ============================================================================
# DJANGO RESTFUL LOGISTICS TEMPLATE - MAKEFILE
# ============================================================================
# Comandos comunes para desarrollo y despliegue

.PHONY: help build up down logs test clean restart shell migrate collectstatic

# Variables
COMPOSE_FILE=docker-compose.yml
DOCKER_COMPOSE=docker-compose -f $(COMPOSE_FILE)

# Default target
help: ## Show this help message
	@echo "Django RESTful Logistics Template - Available commands:"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
build: ## Build all Docker images
	$(DOCKER_COMPOSE) build

up: ## Start all services
	$(DOCKER_COMPOSE) up -d

up-test: ## Start with test data
	LOAD_TEST_DATA=true $(DOCKER_COMPOSE) up -d

up-clean: ## Start with clean database
	LOAD_TEST_DATA=false $(DOCKER_COMPOSE) up -d

up-build: ## Build and start all services
	$(DOCKER_COMPOSE) up -d --build

down: ## Stop all services
	$(DOCKER_COMPOSE) down

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart

logs: ## Show logs for all services
	$(DOCKER_COMPOSE) logs -f

logs-web: ## Show logs for web service
	$(DOCKER_COMPOSE) logs -f web

logs-celery: ## Show logs for celery service
	$(DOCKER_COMPOSE) logs -f celery

logs-nginx: ## Show logs for nginx service
	$(DOCKER_COMPOSE) logs -f nginx

# Django commands
shell: ## Access Django shell
	$(DOCKER_COMPOSE) exec web python manage.py shell

migrate: ## Run database migrations
	$(DOCKER_COMPOSE) exec web python manage.py migrate

makemigrations: ## Create new migrations
	$(DOCKER_COMPOSE) exec web python manage.py makemigrations

collectstatic: ## Collect static files
	$(DOCKER_COMPOSE) exec web python manage.py collectstatic --noinput

createsuperuser: ## Create Django superuser
	$(DOCKER_COMPOSE) exec web python manage.py createsuperuser

# Testing and quality
test: ## Run all tests
	$(DOCKER_COMPOSE) exec web python manage.py test

test-coverage: ## Run tests with coverage
	$(DOCKER_COMPOSE) exec web coverage run --source='.' manage.py test
	$(DOCKER_COMPOSE) exec web coverage report
	$(DOCKER_COMPOSE) exec web coverage html

lint: ## Run code linting
	$(DOCKER_COMPOSE) exec web flake8 .

format: ## Format code with black
	$(DOCKER_COMPOSE) exec web black .

check: ## Run all checks (lint + test)
	make lint
	make test

# Database commands
dbshell: ## Access database shell
	$(DOCKER_COMPOSE) exec db psql -U logistics_user -d logistics_db

backup-db: ## Backup database
	$(DOCKER_COMPOSE) exec db pg_dump -U logistics_user logistics_db > backup_$$(date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore database (specify file with FILE=backup.sql)
	$(DOCKER_COMPOSE) exec -T db psql -U logistics_user -d logistics_db < $(FILE)

# Data management
load-data: ## Load test data
	$(DOCKER_COMPOSE) exec web python manage.py setup_initial_data

flush-db: ## Flush database
	$(DOCKER_COMPOSE) exec web python manage.py flush --noinput

reset-db: ## Reset database (flush + migrate + load data)
	make flush-db
	make migrate
	make load-data

# Maintenance
clean: ## Remove all containers, volumes, and images
	$(DOCKER_COMPOSE) down -v --rmi all

clean-cache: ## Clean Docker cache
	docker system prune -f

update: ## Update all dependencies
	$(DOCKER_COMPOSE) exec web pip install -r requirements.txt --upgrade

# Health checks
health: ## Check service health
	@echo "Checking service health..."
	@curl -s http://localhost/health/ | python -m json.tool || echo "Health check failed"

status: ## Show service status
	$(DOCKER_COMPOSE) ps

# Production helpers
deploy-prod: ## Deploy to production (use with caution)
	@echo "⚠️  This will deploy to production. Are you sure? [y/N]"
	@read confirm; [ "$$confirm" = "y" ] || exit 1
	LOAD_TEST_DATA=false $(DOCKER_COMPOSE) -f docker-compose.prod.yml up -d --build

backup-all: ## Backup everything (database + media)
	mkdir -p backups
	make backup-db
	$(DOCKER_COMPOSE) exec web tar -czf /tmp/media_backup_$$(date +%Y%m%d_%H%M%S).tar.gz /app/media/
	$(DOCKER_COMPOSE) cp web:/tmp/media_backup_*.tar.gz ./backups/

# Environment setup
setup: ## Initial setup (copy .env, build, migrate, load data)
	@if [ ! -f .env ]; then cp .env.example .env; echo "Created .env file"; fi
	make build
	make up-test
	@echo ""
	@echo "🎉 Setup complete! Services are running:"
	@echo "   🌐 Application: http://localhost"
	@echo "   📊 Flower:      http://localhost:5555"
	@echo "   📚 Docs:        http://localhost/api/docs/"

# Documentation
docs: ## Generate documentation
	$(DOCKER_COMPOSE) exec web python manage.py spectacular --file schema.yml
	@echo "API schema generated: schema.yml"

# Development workflow
dev: ## Start development environment
	make setup
	make logs

# Quick commands for common tasks
quick-reset: ## Quick reset for development
	make down
	make up-test
	make logs-web
