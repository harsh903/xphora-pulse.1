"""
Chatbot module for Bengaluru information chatbot.
"""

import os
import uuid
import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.news_agent import run_bengaluru_news
from app.agents.twitter_agent import run_twitter_to_summary
from app.agents.weather_agent import run_weather_summary
from app.utils.gemini import generate_response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str
    
class StatusResponse(BaseModel):
    """Status response model."""
    status: str
    message: str

class BengaluruChatbot:
    """Simple chatbot for answering questions about Bengaluru."""
    
    def __init__(self):
        """Initialize the chatbot."""
        # In-memory session storage (will be lost when the server restarts)
        self.sessions = {}
        
        # Define default system prompt
        self.system_prompt = """
        You are BengaluruBot, a helpful assistant that provides information about Bengaluru (Bangalore), India.
        You can answer questions about locations, civic issues, infrastructure, traffic, cultural aspects, 
        historical information, tourist attractions, and other facts about the city.
        
        Guidelines:
        1. Focus ONLY on providing factual information about Bengaluru.
        2. If you don't know the answer, admit it rather than making up information.
        3. Keep responses concise, informative, and helpful.
        4. Base your answers on the retrieved context when available.
        
        Remember that you are representing Bengaluru in a positive but honest way.
        """
        
        logger.info("BengaluruChatbot initialized successfully")
    
    async def process_query(self, message: str, session_id: Optional[str] = None) -> Dict:
        """
        Process a user query and generate a response.
        
        Args:
            message: User message
            session_id: Optional session ID
            
        Returns:
            Dictionary with response and session_id
        """
        # Create a session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Initialize session if it doesn't exist
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        try:
            # Process the message based on its content
            response = await self._generate_response(message)
            
            # Store the message and response in the session (temporary, in-memory only)
            self.sessions[session_id].append({"role": "user", "content": message})
            self.sessions[session_id].append({"role": "assistant", "content": response})
            
            return {
                "response": response,
                "session_id": session_id
            }
        
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "response": "I'm sorry, but I encountered an error while processing your question. Please try again.",
                "session_id": session_id
            }
    
    async def _generate_response(self, message: str) -> str:
        """
        Generate a response based on the user's message.
        
        Args:
            message: User message
            
        Returns:
            Chatbot response
        """
        message_lower = message.lower()
        
        # Check for specific topics and use appropriate services
        if "weather" in message_lower and any(city in message_lower for city in ["bengaluru", "bangalore"]):
            # Extract city from message or default to Bengaluru
            city = "Bengaluru"
            weather_data = await run_weather_summary(city)
            if "error" in weather_data:
                return f"I'm sorry, but I couldn't fetch the weather data: {weather_data['error']}"
            return f"Here's the current weather in Bengaluru: {weather_data.get('summary', '')}"
        
        elif "news" in message_lower and any(city in message_lower for city in ["bengaluru", "bangalore"]):
            news_articles = run_bengaluru_news()
            if not news_articles:
                return "I'm sorry, but I couldn't find any recent news articles for Bengaluru."
            
            # Format the top 3 news articles
            news_response = "Here are the latest news from Bengaluru:\n\n"
            for i, article in enumerate(news_articles[:3], 1):
                news_response += f"{i}. {article.get('title', 'No title')}\n"
                if article.get('description'):
                    news_response += f"   {article.get('description')}\n"
            
            return news_response
        
        elif any(term in message_lower for term in ["civic issue", "civic problem", "infrastructure", "public service"]):
            twitter_summary = await run_twitter_to_summary()
            return f"Here's a summary of recent civic issues mentioned on social media:\n\n{twitter_summary}"
        
        else:
            # For general queries, use Gemini to generate a response
            try:
                response = generate_response(self.system_prompt, message)
                return response
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                return "I'm sorry, but I'm having trouble understanding. Could you please rephrase your question about Bengaluru?"

# Create an instance of the chatbot
chatbot = BengaluruChatbot()

# Create a router for the chatbot
chatbot_router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

@chatbot_router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Get a chat response.
    
    Args:
        request: Chat request
        
    Returns:
        Chat response
    """
    try:
        result = await chatbot.process_query(request.message, request.session_id)
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@chatbot_router.get("/healthcheck", response_model=StatusResponse)
async def healthcheck():
    """
    Check if the chatbot is running.
    
    Returns:
        Status response
    """
    return StatusResponse(status="success", message="Chatbot API is running")