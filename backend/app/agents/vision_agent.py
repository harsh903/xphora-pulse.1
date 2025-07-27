from app.services.vision_service import analyze_image_with_gemini
import base64
from PIL import Image
import requests
from io import BytesIO

def run_image_analysis(image_link, description, location):
    """
    Run image analysis using Gemini AI and return the verification result.
    """

    # Download image from URL or open local file
    if image_link.startswith('http://') or image_link.startswith('https://'):
        response = requests.get(image_link)
        image = Image.open(BytesIO(response.content))
    else:
        image = Image.open(image_link)

    buffered = BytesIO()
    image.save(buffered, format=image.format if image.format else 'PNG')
    image_bytes = base64.b64encode(buffered.getvalue()).decode("utf-8")
    result = analyze_image_with_gemini(image_bytes, description, location)
    return result