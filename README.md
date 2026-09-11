# Weather App

A simple, beginner-friendly weather search application built with **Python**, **Django**, **HTML5**, **CSS3**, and a small amount of **vanilla JavaScript**. Users enter a city name and see live weather data from the **OpenWeather API**.

---

## Project Description

This project demonstrates a clean Django workflow:

**User → Form → Django View → Weather Service → OpenWeather API → Template → Browser**

API logic is kept in a dedicated service module (`weather_api.py`), not inside the view. The UI is a centered white card on a blue–cyan gradient background — no Bootstrap, Tailwind, React, or Vue.

---

## Features

- Search weather by city name
- Display city, country, temperature (°C), feels like, condition, humidity, wind speed, pressure, and weather icon
- Django form with empty-input validation
- Clear error messages for:
  - Empty city
  - City not found
  - Invalid / missing API key
  - Network errors / API unavailable
- Responsive layout (mobile, tablet, desktop)
- Soft card shadow, hover effects, and light animations
- SQLite database (Django default)
- Environment-based API key via `.env`

---

## Requirements

- Python 3.8+
- Django
- requests
- python-dotenv
- An OpenWeatherMap API key (free)

See `requirements.txt` for package versions.

---

## Installation

1. **Clone or open the project folder**

```bash
cd weather_app
```

2. **Create and activate a virtual environment (recommended)**

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Configure your API key**

Open the `.env` file in the project root and replace the placeholder:

```env
API_KEY=YOUR_OPENWEATHER_API_KEY
```

with your real key, for example:

```env
API_KEY=abc123yourrealkeyhere
```

5. **Run database migrations**

```bash
python manage.py migrate
```

---

## How to Run

```bash
python manage.py runserver
```

Open your browser at:

**http://127.0.0.1:8000/**

1. Enter a city name (e.g. `Delhi`, `London`, `Tokyo`)
2. Click **Search**
3. View the live weather results on the card

---

## API Setup

1. Go to [https://openweathermap.org/api](https://openweathermap.org/api)
2. Sign up for a free account
3. Create an API key under **API keys**
4. Paste the key into `.env` as `API_KEY=...`
5. Wait a few minutes if a brand-new key is not active yet

The service builds a request like:

```text
https://api.openweathermap.org/data/2.5/weather?q=CITY&appid=API_KEY&units=metric
```

---

## Screenshots

Add screenshots of the app here after running it:

1. **Home / Search** — empty card with search box
2. **Success** — weather details for a city (icon, temperature, humidity, etc.)
3. **Error** — “City not found” or similar message

Suggested files:

- `screenshots/home.png`
- `screenshots/result.png`
- `screenshots/error.png`

---

## Folder Structure

```text
weather_app/
├── manage.py
├── requirements.txt
├── .env
├── .gitignore
├── README.md
├── db.sqlite3                 # created after migrate
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   └── weather/
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── forms.py
│       ├── models.py
│       ├── urls.py
│       ├── views.py
│       ├── tests.py
│       ├── migrations/
│       ├── services/
│       │   ├── __init__.py
│       │   └── weather_api.py   # OpenWeather API logic
│       ├── templates/
│       │   └── weather/
│       │       ├── base.html
│       │       └── home.html
│       └── static/
│           └── weather/
│               ├── css/
│               │   └── style.css
│               └── js/
│                   └── script.js
├── templates/                   # optional project-level templates
├── static/                      # optional project-level static files
└── media/                       # media uploads (if needed later)
```

---

## Tech Stack

| Layer     | Technology                          |
|-----------|-------------------------------------|
| Backend   | Python 3, Django                    |
| Frontend  | HTML5, CSS3, Vanilla JavaScript     |
| API       | OpenWeather API + `requests`        |
| Database  | SQLite                              |
| Config    | `python-dotenv` (`.env`)            |

---

## Error Handling

| Situation           | User message                                      |
|---------------------|---------------------------------------------------|
| Empty city          | Please enter a city name.                         |
| Unknown city        | City not found. Please check the spelling...      |
| Missing API key     | API key is missing. Please add your key to .env   |
| Network / timeout   | Network error or request timed out...             |
| API down / other    | Weather service is temporarily unavailable...     |

---

## License

This project is for learning and educational use.
