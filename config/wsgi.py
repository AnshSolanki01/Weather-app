"""
WSGI config for the Weather App project.

Exposes the WSGI callable as a module-level variable named ``application``.
Used by production servers (Gunicorn, uWSGI, etc.).
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
