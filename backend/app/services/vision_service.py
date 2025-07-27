import base64
import google.generativeai as genai
from app.utils.prompt import vision_prompt
def analyze_image_with_gemini(image_bytes, description, location):
    """
    Analyze the image with Gemini AI and compare with the description/location
    Returns a formatted verification result with percentage and explanation
    """
    try:
        # Configure Gemini model
        model = genai.GenerativeModel('gemini-2.5-flash')

        # Prepare the image for Gemini
        image_parts = [
            {
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(image_bytes).decode('utf-8')
                }
            }
        ]

        # Analyze the image content
        prompt = "Describe this image in detail. Include the surroundings, elements visible, and any clues about the location."
        analysis_response = model.generate_content(contents=[prompt] + image_parts)

        # Get user's combined input (description + location)
        user_input = f"Description: {description}\nLocation: {location}"

        # Compare the description with the image analysis
        comparison_prompt = vision_prompt.format(
            analysis_response=analysis_response,
            user_input=user_input
        )
        verification_response = model.generate_content(comparison_prompt)

        return verification_response.text
    except Exception as e:
        print(f"Error analyzing image with Gemini: {e}")
        return f"Error: {str(e)}"