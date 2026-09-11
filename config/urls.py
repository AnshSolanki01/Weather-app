"""
Root URL configuration for the Weather App project.

Routes:
    /  -> weather app home page (search form + results)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # Weather app URLs (home page at "/")
    path('', include('apps.weather.urls')),
]

# Serve media files during development.
# App static files are already served by django.contrib.staticfiles.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
