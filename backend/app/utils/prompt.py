# twitter_prompt ="""
# Here are several recent tweets about civic issues in Bengaluru.
# Summarize the key themes, concerns, and insights expressed by the users.
# Focus on extracting common sentiments, recurring problems, and any useful information for public decision-making.
# Keep the summary concise but informative.
# """

twitter_prompt = """
You are given a list of recent tweets about civic issues in Bengaluru.

If the tweets mention specific areas (like Whitefield, Yelahanka, Indiranagar, etc.), group them by area and generate a short summary for each area highlighting common issues, concerns, and sentiments.

If area information is not available or minimal, provide a single general summary.

Focus on recurring civic problems and useful insights for decision-makers. Keep summaries concise but informative.
"""


weather_prompt ="""
Here is the weather information for the specified location.
Summarize the key weather conditions, forecasts, and any relevant alerts.
Focus on extracting important details that users need to know.
Keep the summary concise but informative.
"""


vision_prompt = """
        Image analysis: {analysis_response.text}
        
        User input: {user_input}
        
        Compare the user's description and location with the image analysis.
        
        Your response must be in exactly this format:
        
        The user's description is **[consistency level]** with the image analysis.
        
        **Consistency Rate: XX%**
        
        **Explanation:**
        1. **"[quote part of description]":** [explanation of how this matches or doesn't match what's visible]
        2. **"[location]":** [explanation of how the location is supported or not supported by visual evidence]
        
        Where consistency level should be one of: "highly consistent" (80-100%), "moderately consistent" (50-79%), "somewhat consistent" (20-49%), or "inconsistent" (0-19%).
        
        Choose a specific percentage value, not a range.
        Your explanation should reference specific details from both the image analysis and user input.
"""