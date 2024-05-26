from flask import Flask, jsonify, request, render_template
import requests
import datetime as dt
from newspaper import Article
import nltk
from yahoo_fin.stock_info import get_live_price

app = Flask(__name__)

# Weather API config
BASE_URL = "http://api.openweathermap.org/data/2.5/weather?"
WEATHER_API_KEY = "b69553333dafad4bd0d40cf76f4e7f8a"

# News API config
NEWS_API_KEY = '7061c854f0c44d8e8c355e5fe2681891'
NEWS_BASE_URL = 'https://newsapi.org/v2'
NEWS_ENDPOINT = '/top-headlines'

nltk.download('punkt')


def kelvin_to_celsius_fahrenheit(kelvin):
    celsius = kelvin - 273.15
    fahrenheit = celsius * (9 / 5) + 32
    return celsius, fahrenheit


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city', 'New York')
    url = f"{BASE_URL}appid={WEATHER_API_KEY}&q={city}"
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


@app.route('/finance', methods=['GET'])
def get_stock():
    try:
        fb_data = get_live_price("META")
        aapl_data = get_live_price("AAPL")
        msft_data = get_live_price("MSFT")
        googl_data = get_live_price("GOOGL")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    stock_info = {
        "facebook": {"current_price": fb_data},
        "apple": {"current_price": aapl_data},
        "microsoft": {"current_price": msft_data},
        "google": {"current_price": googl_data}
    }

    return jsonify(stock_info)


@app.route('/news', methods=['GET'])
def get_news():
    url = f"{NEWS_BASE_URL}{NEWS_ENDPOINT}"

    params = {
        'category': 'business',
        'country': 'us',
        'apiKey': NEWS_API_KEY
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        articles = data.get('articles', [])
        article_summaries = []

        for article_data in articles:
            article_url = article_data.get('url')
            if article_url:
                try:
                    article = Article(article_url)
                    article.download()
                    article.parse()
                    article.nlp()
                    article_summary = {
                        'title': article.title,
                        'summary': article.summary,
                        'url': article_url
                    }
                    article_summaries.append(article_summary)
                except Exception as e:
                    print(f"Failed to process article at {article_url}: {e}")

        return jsonify(article_summaries)
    else:
        return jsonify({'error': f"Failed to fetch data: {response.status_code}"}), response.status_code


if __name__ == '__main__':
    app.run(debug=True)
