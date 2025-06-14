"""
Models module for users app.
This module imports all models from infrastructure layer to make them available
for Django's app discovery and migration system.
"""

from .infrastructure.models import *
