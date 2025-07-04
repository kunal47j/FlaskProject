import requests
import string
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from collections import defaultdict, Counter

app = Flask(__name__)

# TODO: For production, use environment variables for secret keys and API keys instead of hardcoding them.
app.secret_key = 'your_secret_key_here'
API_KEY = 'b21a2633ddaac750a77524f91fe104e7'

CITIES = [
    'London', 'New York', 'Paris', 'Tokyo', 'Sydney', 'Berlin', 'Moscow', 'Beijing', 'Mumbai', 'Cairo'
]

# Function to get current weather data
def get_weather_data(city, unit='metric'):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units={unit}&appid={API_KEY}"
    r = requests.get(url).json()
    return r

# Function to get forecast data
def get_forecast_data(city, unit='metric'):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units={unit}&appid={API_KEY}"
    r = requests.get(url).json()
    return r

# Helper to extract daily forecast from 3-hourly data
def extract_daily_forecast(forecast_list):
    days = defaultdict(list)
    for entry in forecast_list:
        day = datetime.fromtimestamp(entry['dt']).strftime('%a')
        days[day].append(entry)
    daily = []
    for day, entries in list(days.items())[:5]:
        # Pick the entry closest to 12:00, or just the middle one
        target = min(entries, key=lambda e: abs(datetime.fromtimestamp(e['dt']).hour - 12))
        temps = [e['main']['temp'] for e in entries]
        icons = [e['weather'][0]['icon'] for e in entries]
        icon = Counter(icons).most_common(1)[0][0]
        avg_temp = sum(temps) / len(temps)
        daily.append({
            'day': day,
            'icon': icon,
            'temp': avg_temp
        })
    return daily

def format_time(utime, tz):
    return datetime.utcfromtimestamp(utime + tz).strftime('%H:%M')

# Home route (GET)
@app.route('/', methods=['GET', 'POST'])
def index():
    err_msg = ''
    unit = session.get('unit', 'metric')
    city = None
    if request.method == 'POST':
        city = request.form.get('city')
        unit_form = request.form.get('unit')
        if unit_form:
            unit = unit_form
            session['unit'] = unit
        if not city:
            city = 'London'
    else:
        city = 'London'
    data = get_weather_data(city, unit)
    forecast = get_forecast_data(city, unit)
    if data.get('cod') == 200 and forecast.get('cod') == '200':
        weather_data = {
            'city': city,
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'humidity': data['main'].get('humidity'),
            'wind_speed': data['wind'].get('speed'),
            'pressure': data['main'].get('pressure'),
            'visibility': round(data.get('visibility', 0) / 1000, 1) if data.get('visibility') else 'N/A',
            'rain_chance': forecast['list'][0].get('pop', 0) * 100 if forecast['list'] else 0,
            'temp_max': data['main'].get('temp_max'),
            'temp_min': data['main'].get('temp_min'),
            'sunrise': format_time(data['sys']['sunrise'], data['timezone']) if data['sys'].get('sunrise') else '',
            'sunset': format_time(data['sys']['sunset'], data['timezone']) if data['sys'].get('sunset') else '',
        }
        hourly_forecast = []
        for entry in forecast['list'][:8]:
            hour = {
                'time': datetime.fromtimestamp(entry['dt']).strftime('%H:%M'),
                'icon': entry['weather'][0]['icon'],
                'temp': entry['main']['temp'],
                'rain_chance': entry.get('pop', 0) * 100
            }
            hourly_forecast.append(hour)
        weather_data['hourly_forecast'] = hourly_forecast
        weather_data['daily_forecast'] = extract_daily_forecast(forecast['list'])
        return render_template('index.html', weather_data=[weather_data], unit=unit, cities=CITIES)
    else:
        err_msg = 'That is not a valid city!'
        flash(err_msg, 'error')
        return render_template('index.html', weather_data=None, unit=unit, cities=CITIES)

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
        