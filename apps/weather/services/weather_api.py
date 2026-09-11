"""
Weather API service.

All OpenWeather / external API logic lives here — views stay thin.
Features:
- Current weather + rain probability
- 3-day forecast
- City geocoding (autocomplete)
- City background photo
- Correct local date & time for the searched city
- Compare two cities
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone as dt_timezone
from urllib.parse import quote

import requests
from django.conf import settings


OPENWEATHER_URL = 'https://api.openweathermap.org/data/2.5/weather'
FORECAST_URL = 'https://api.openweathermap.org/data/2.5/forecast'
GEOCODE_URL = 'https://api.openweathermap.org/geo/1.0/direct'

POPULAR_CITIES = [
    'Delhi', 'Mumbai', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata',
    'Pune', 'Jaipur', 'Ahmedabad', 'Lucknow', 'London', 'New York',
    'Tokyo', 'Paris', 'Dubai', 'Singapore', 'Sydney', 'Toronto',
    'Berlin', 'Rome', 'Madrid', 'Moscow', 'Beijing', 'Seoul',
    'Bangkok', 'Istanbul', 'Cairo', 'Cape Town', 'Rio de Janeiro',
    'Los Angeles', 'Chicago', 'San Francisco', 'Mexico City', 'Amsterdam',
]


def _get_api_key():
    """Read the OpenWeather API key from settings / environment."""
    return getattr(settings, 'OPENWEATHER_API_KEY', '') or os.getenv('API_KEY', '')


def _api_key_error():
    """Standard response when the API key is missing or still a placeholder."""
    return {
        'success': False,
        'error': 'API key is missing. Please add your OpenWeather API key to the .env file.',
    }


def _city_local_now(tz_offset_seconds):
    """
    Return the current wall-clock datetime in the city's timezone.

    OpenWeather gives timezone as seconds offset from UTC (e.g. 19800 for IST).
    We shift UTC "now" by that offset and treat the result as naive local time.
    """
    utc_now = datetime.now(dt_timezone.utc)
    local_naive = (utc_now + timedelta(seconds=tz_offset_seconds)).replace(tzinfo=None)
    return local_naive


def get_weather(city, include_background=True):
    """
    Fetch current weather, rain chance, 3-day forecast, local time, and optional backdrop.

    Args:
        city (str): City name (e.g. "Delhi", "London").
        include_background (bool): Fetch city photo (skip for faster compare mode).

    Returns:
        dict: success=True with weather fields, or success=False with error.
    """
    api_key = _get_api_key()
    if not api_key or api_key == 'YOUR_OPENWEATHER_API_KEY':
        return _api_key_error()

    params = {
        'q': city,
        'appid': api_key,
        'units': 'metric',
    }

    try:
        response = requests.get(OPENWEATHER_URL, params=params, timeout=10)

        if response.status_code == 404:
            return {
                'success': False,
                'error': f'City not found: "{city}". Please check the spelling.',
            }
        if response.status_code == 401:
            return {
                'success': False,
                'error': 'Invalid API key. Please check your API_KEY in the .env file.',
            }
        if response.status_code != 200:
            return {
                'success': False,
                'error': 'Weather service is temporarily unavailable. Please try again later.',
            }

        data = response.json()
        weather = _parse_weather_data(data)

        # Forecast also supplies rain probability (pop) for current + 3 days
        forecast_bundle = get_forecast_bundle(city, api_key)
        weather['forecast'] = forecast_bundle.get('days', [])
        weather['rain_probability'] = forecast_bundle.get(
            'current_pop',
            weather.get('rain_probability', 0),
        )

        if include_background:
            weather['background_url'] = get_city_background(
                weather['city'],
                weather.get('country', ''),
            )
        else:
            weather['background_url'] = None

        return weather

    except requests.exceptions.Timeout:
        return {
            'success': False,
            'error': 'Request timed out. Please check your internet connection and try again.',
        }
    except requests.exceptions.ConnectionError:
        return {
            'success': False,
            'error': 'Network error. Please check your internet connection and try again.',
        }
    except requests.exceptions.RequestException:
        return {
            'success': False,
            'error': 'Unable to reach the weather service. Please try again later.',
        }
    except (KeyError, ValueError, TypeError):
        return {
            'success': False,
            'error': 'Received unexpected data from the weather service.',
        }


def compare_cities(city_a, city_b):
    """
    Fetch weather for two cities and build a side-by-side comparison.

    Returns:
        dict with success, city_a, city_b, and optional error.
    """
    result_a = get_weather(city_a, include_background=False)
    result_b = get_weather(city_b, include_background=False)

    if not result_a.get('success'):
        return {
            'success': False,
            'error': result_a.get('error', 'Could not load the first city.'),
            'city_a': None,
            'city_b': None,
        }
    if not result_b.get('success'):
        return {
            'success': False,
            'error': result_b.get('error', 'Could not load the second city.'),
            'city_a': None,
            'city_b': None,
        }

    return {
        'success': True,
        'city_a': result_a,
        'city_b': result_b,
        'error': None,
        # Use first city's photo as soft background
        'background_url': get_city_background(result_a['city'], result_a.get('country', '')),
    }


def search_cities(query, limit=8):
    """Search cities for autocomplete (popular list + OpenWeather Geocoding)."""
    query = (query or '').strip()

    if not query:
        return [
            {'name': name, 'label': name, 'country': '', 'state': ''}
            for name in POPULAR_CITIES[:limit]
        ]

    popular_matches = [
        {'name': name, 'label': name, 'country': '', 'state': ''}
        for name in POPULAR_CITIES
        if query.lower() in name.lower()
    ]

    api_key = _get_api_key()
    if not api_key or api_key == 'YOUR_OPENWEATHER_API_KEY':
        return popular_matches[:limit]

    try:
        response = requests.get(
            GEOCODE_URL,
            params={'q': query, 'limit': limit, 'appid': api_key},
            timeout=8,
        )
        if response.status_code != 200:
            return popular_matches[:limit]

        results = []
        seen = set()
        for item in response.json():
            name = item.get('name', '')
            country = item.get('country', '')
            state = item.get('state', '')
            label_parts = [name]
            if state:
                label_parts.append(state)
            if country:
                label_parts.append(country)
            label = ', '.join(label_parts)
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            results.append({
                'name': name,
                'label': label,
                'country': country,
                'state': state,
            })

        for match in popular_matches:
            if match['name'].lower() not in seen:
                results.insert(0, match)
                seen.add(match['name'].lower())

        return results[:limit]

    except requests.exceptions.RequestException:
        return popular_matches[:limit]


def get_forecast_bundle(city, api_key=None):
    """
    Build 3-day forecast + nearest rain probability from the 5-day / 3-hour API.

    OpenWeather `pop` is 0–1; we convert to percent.
    """
    api_key = api_key or _get_api_key()
    empty = {'days': [], 'current_pop': 0}
    if not api_key:
        return empty

    try:
        response = requests.get(
            FORECAST_URL,
            params={'q': city, 'appid': api_key, 'units': 'metric'},
            timeout=10,
        )
        if response.status_code != 200:
            return empty

        payload = response.json()
        tz_offset = payload.get('city', {}).get('timezone', 0)
        entries = payload.get('list', [])
        if not entries:
            return empty

        # Nearest forecast slot → current rain probability
        current_pop = round(entries[0].get('pop', 0) * 100)

        grouped = defaultdict(list)
        for entry in entries:
            local_dt = datetime.fromtimestamp(entry['dt'], tz=dt_timezone.utc) + timedelta(
                seconds=tz_offset
            )
            day_key = local_dt.strftime('%Y-%m-%d')
            grouped[day_key].append(entry)

        forecast_days = []
        today_local = _city_local_now(tz_offset).strftime('%Y-%m-%d')

        for day_key in sorted(grouped.keys()):
            if day_key < today_local:
                continue
            day_entries = grouped[day_key]
            temps = [e['main']['temp'] for e in day_entries]
            pops = [e.get('pop', 0) for e in day_entries]
            mid = min(
                day_entries,
                key=lambda e: abs(
                    (
                        datetime.fromtimestamp(e['dt'], tz=dt_timezone.utc)
                        + timedelta(seconds=tz_offset)
                    ).hour
                    - 12
                ),
            )
            weather_main = (mid.get('weather') or [{}])[0]
            icon = weather_main.get('icon', '01d')
            local_date = datetime.strptime(day_key, '%Y-%m-%d')

            forecast_days.append({
                'date': day_key,
                'weekday': local_date.strftime('%a'),
                'day_label': 'Today' if day_key == today_local else local_date.strftime('%a'),
                'full_date': local_date.strftime('%d %b'),
                'temp_min': round(min(temps)),
                'temp_max': round(max(temps)),
                'condition': weather_main.get('description', '').title(),
                'rain_probability': round(max(pops) * 100),
                'icon': icon,
                'icon_url': f'https://openweathermap.org/img/wn/{icon}@2x.png',
            })

            if len(forecast_days) >= 3:
                break

        return {'days': forecast_days, 'current_pop': current_pop}

    except (requests.exceptions.RequestException, KeyError, ValueError, TypeError):
        return empty


def get_three_day_forecast(city, api_key=None):
    """Compatibility helper — returns only the 3-day list."""
    return get_forecast_bundle(city, api_key).get('days', [])


def get_city_background(city, country=''):
    """Resolve a scenic background photo URL for the city."""
    titles = [city.replace(' ', '_')]
    if country:
        titles.append(f'{city.replace(" ", "_")},_{country}')

    headers = {
        'Accept': 'application/json',
        'User-Agent': 'WeatherApp/1.0 (Django learning project)',
    }

    for title in titles:
        try:
            wiki = requests.get(
                f'https://en.wikipedia.org/api/rest_v1/page/summary/{quote(title)}',
                headers=headers,
                timeout=6,
            )
            if wiki.status_code != 200:
                continue
            data = wiki.json()
            original = data.get('originalimage', {}).get('source')
            thumb = data.get('thumbnail', {}).get('source')
            if original:
                return original
            if thumb:
                return thumb
        except requests.exceptions.RequestException:
            continue

    safe_city = ''.join(ch for ch in city if ch.isalnum() or ch in ' -_')
    safe_city = safe_city.replace(' ', '').strip() or 'cityscape'
    return f'https://loremflickr.com/1600/900/{safe_city},cityscape,skyline'


def _parse_weather_data(data):
    """Convert raw OpenWeather JSON into a template-friendly dictionary."""
    wind_ms = data.get('wind', {}).get('speed', 0)
    wind_kmh = round(wind_ms * 3.6, 1)

    weather_list = data.get('weather', [{}])
    weather_main = weather_list[0] if weather_list else {}
    icon_code = weather_main.get('icon', '01d')

    tz_offset = int(data.get('timezone', 0) or 0)
    local_now = _city_local_now(tz_offset)

    # Rough rain hint from current rain volume if present (mm); pop comes from forecast
    rain_1h = data.get('rain', {}).get('1h')
    rain_probability = 0
    if rain_1h is not None and rain_1h > 0:
        rain_probability = min(100, round(40 + rain_1h * 15))

    return {
        'success': True,
        'city': data.get('name', ''),
        'country': data.get('sys', {}).get('country', ''),
        'temperature': round(data.get('main', {}).get('temp', 0)),
        'feels_like': round(data.get('main', {}).get('feels_like', 0)),
        'condition': weather_main.get('description', '').title(),
        'humidity': data.get('main', {}).get('humidity', 0),
        'wind_speed': wind_kmh,
        'pressure': data.get('main', {}).get('pressure', 0),
        'rain_probability': rain_probability,
        'icon': icon_code,
        'icon_url': f'https://openweathermap.org/img/wn/{icon_code}@2x.png',
        'timezone_offset': tz_offset,
        'local_date': local_now.strftime('%A, %d %B %Y'),
        'local_time': local_now.strftime('%I:%M %p'),
        'local_time_24': local_now.strftime('%H:%M:%S'),
        'is_night': icon_code.endswith('n'),
        'error': None,
    }
