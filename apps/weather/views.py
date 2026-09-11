"""
Views for the Weather App.

- home: single-city search + compare-two-cities mode
- city_suggest: JSON autocomplete for city dropdowns
"""

import json

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from .forms import CitySearchForm, CompareCitiesForm
from .services.weather_api import compare_cities, get_weather, search_cities


def home(request):
    """
    Home page — search one city or compare two cities.
    """
    mode = request.POST.get('mode') or request.GET.get('mode') or 'search'
    if mode not in ('search', 'compare'):
        mode = 'search'

    form = CitySearchForm()
    compare_form = CompareCitiesForm()
    weather = None
    comparison = None
    error_message = None
    background_url = None

    if request.method == 'POST':
        if mode == 'compare':
            compare_form = CompareCitiesForm(request.POST)
            if compare_form.is_valid():
                city_a = compare_form.cleaned_data['city_a']
                city_b = compare_form.cleaned_data['city_b']
                result = compare_cities(city_a, city_b)
                if result.get('success'):
                    comparison = result
                    background_url = result.get('background_url')
                else:
                    error_message = result.get('error', 'Could not compare cities.')
            else:
                if compare_form.non_field_errors():
                    error_message = compare_form.non_field_errors()[0]
                elif compare_form.errors.get('city_a'):
                    error_message = compare_form.errors['city_a'][0]
                elif compare_form.errors.get('city_b'):
                    error_message = compare_form.errors['city_b'][0]
                else:
                    error_message = 'Please enter two valid city names.'
        else:
            form = CitySearchForm(request.POST)
            if form.is_valid():
                city = form.cleaned_data['city']
                result = get_weather(city)
                if result.get('success'):
                    weather = result
                    background_url = result.get('background_url')
                else:
                    error_message = result.get(
                        'error',
                        'Something went wrong. Please try again.',
                    )
            else:
                if form.errors.get('city'):
                    error_message = form.errors['city'][0]
                else:
                    error_message = 'Please enter a valid city name.'

    # Prefer weather night hint; otherwise day
    is_night = bool(weather and weather.get('is_night'))

    context = {
        'mode': mode,
        'form': form,
        'compare_form': compare_form,
        'weather': weather,
        'comparison': comparison,
        'error_message': error_message,
        'background_url': background_url,
        'is_night': is_night,
        'weather_json': json.dumps({
            'timezone_offset': weather.get('timezone_offset', 0) if weather else 0,
            'city': weather.get('city', '') if weather else '',
            'mode': mode,
        }),
    }

    return render(request, 'weather/home.html', context)


@require_GET
def city_suggest(request):
    """JSON endpoint for city autocomplete. Example: /api/cities/?q=del"""
    query = request.GET.get('q', '')
    cities = search_cities(query, limit=10)
    return JsonResponse({'cities': cities})
