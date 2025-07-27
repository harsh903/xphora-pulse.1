import requests
from config import WEATHER_API_KEY
class WeatherFetcher:
    def __init__(self):
        self.api_key = WEATHER_API_KEY
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def get_weather(self, city: str) -> dict:
        if not self.api_key:
            return {"error": "API key not set. Use set_api_key() to configure it."}

        params = {
            'q': city,
            'appid': self.api_key,
            'units': 'metric'
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            return {
                "city": city,
                "weather": data['weather'][0]['description'],
                "temperature_celsius": data['main']['temp'],
                "feels_like_celsius": data['main']['feels_like'],
                "min_temperature_celsius": data['main']['temp_min'],
                "max_temperature_celsius": data['main']['temp_max'],
                "data": data
            }
        except requests.RequestException as e:
            return {
                "error": str(e),
                "city": city
            }
