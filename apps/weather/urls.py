"""
URL patterns for the Weather App.
"""

from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.home, name='home'),
    # City autocomplete for the search dropdown
    path('api/cities/', views.city_suggest, name='city_suggest'),
]
