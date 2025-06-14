"""
Celery configuration for Logistics API.
This module contains the Celery application configuration for handling asynchronous tasks.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery application
app = Celery('logistics_api')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Celery beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Example: Clean expired auctions every hour
    'clean-expired-auctions': {
        'task': 'apps.auctions.application.tasks.clean_expired_auctions',
        'schedule': 3600.0,  # Every hour
    },
    
    # Example: Send daily reports
    'send-daily-reports': {
        'task': 'apps.audit.application.tasks.send_daily_reports',
        'schedule': 86400.0,  # Every day
    },
    
    # Example: Update vehicle locations
    'update-vehicle-locations': {
        'task': 'apps.vehicles.application.tasks.update_vehicle_locations',
        'schedule': 300.0,  # Every 5 minutes
    },
}

app.conf.timezone = 'America/Mexico_City'

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f'Request: {self.request!r}')
