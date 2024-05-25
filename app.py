
from flask import Flask, jsonify, request, render_template
import requests
import datetime as dt
import os

app = Flask(__name__)

BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
API_KEY = "b69553333dafad4bd0d40cf76f4e7f8a"

def kelvin_to_celsius_fahrenheit(kelvin):
    celsius = kelvin - 273.15
    fahrenheit = celsius * (9 / 5) + 32
    return celsius, fahrenheit

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city')
    if not city:
        return jsonify({"error": "City not provided"}), 400

    url = f"{BASE_URL}appid={API_KEY}&q={city}"
    response = requests.get(url).json()

    if response.get('cod') != 200:
        return jsonify({"error": response.get('message', 'Failed to retrieve data')}), response.get('cod', 500)

    try:
        pressure = response['main']['pressure']
        temp_kelvin = response['main']['temp']
        temp_celsius, temp_fahrenheit = kelvin_to_celsius_fahrenheit(temp_kelvin)
        feels_like_kelvin = response['main']['feels_like']
        feels_like_celsius, feels_like_fahrenheit = kelvin_to_celsius_fahrenheit(feels_like_kelvin)
        wind_speed = response['wind']['speed']
        humidity = response['main']['humidity']
        description = response['weather'][0]['description']
        timezone_offset = response['timezone']
        sunrise_time = dt.datetime.utcfromtimestamp(response['sys']['sunrise'] + timezone_offset)
        sunset_time = dt.datetime.utcfromtimestamp(response['sys']['sunset'] + timezone_offset)

        weather_data = {
            "temperature": {
                "celsius": temp_celsius,
                "fahrenheit": temp_fahrenheit
            },
            "feels_like": {
                "celsius": feels_like_celsius,
                "fahrenheit": feels_like_fahrenheit
            },
            "wind_speed": wind_speed,
            "humidity": humidity,
            "pressure": pressure,
            "description": description,
            "sunrise": sunrise_time.isoformat(),
            "sunset": sunset_time.isoformat()
        }

        return jsonify(weather_data)
    except KeyError as e:
        return jsonify({"error": f"Missing data in response: {e}"}), 500

if __name__ == '__main__':
    app.run(debug=False,host='0.0.0.0')
