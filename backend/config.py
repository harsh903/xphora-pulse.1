from dotenv import load_dotenv
import os
load_dotenv()



GEMINI_TEXT_API_KEY = os.getenv("GEMINI_TEXT_API_KEY")
GEMINI_VISION_API_KEY = os.getenv("GEMINI_VISION_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")