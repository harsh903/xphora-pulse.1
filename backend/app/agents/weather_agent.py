from app.services.weather_service import WeatherFetcher
from app.utils.gemini import generate_response
from app.utils.prompt import weather_prompt

async def run_weather_summary(query: str) -> dict:
    weather_fetcher = WeatherFetcher()

    # Fetch weather data for the given query
    weather_data = weather_fetcher.get_weather(query)

    if "error" in weather_data:
        return {"error": f"Error fetching weather data: {weather_data['error']}"}

    # Prepare the input text for summarization
    raw_weather_data = weather_data.get('data')

    # Generate summary using Gemini
    summary = generate_response(weather_prompt, raw_weather_data)
    weather_data['summary'] = summary

    # Remove the raw data from the response
    weather_data.pop('data', None)

    return weather_data
