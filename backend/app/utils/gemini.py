import google.generativeai as genai
from config import GEMINI_TEXT_API_KEY

API_KEY = GEMINI_TEXT_API_KEY
genai.configure(api_key=API_KEY)
def generate_response(system_prompt: str, input_text: str) -> str:
    model = genai.GenerativeModel('gemini-2.0-flash')

    full_prompt = f"{system_prompt.strip()}\n\nUser: {input_text}"
    response = model.generate_content(full_prompt)
    return response.text.strip()