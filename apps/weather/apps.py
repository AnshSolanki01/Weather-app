"""
App configuration for the weather application.
"""

from django.apps import AppConfig


class WeatherConfig(AppConfig):
    """Registers the weather app with Django."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.weather'
    verbose_name = 'Weather'
