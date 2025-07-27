"""
API module for the Bengaluru services application.
Provides endpoints for chatbot, news, weather, predictions, and financial information.
"""

import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app import chatbot
from app.agents.news_agent import run_bengaluru_news
from app.agents.twitter_agent import run_twitter_to_summary
from app.agents.weather_agent import run_weather_summary
from app.agents.prediction_agent import run_prediction_to_summary, run_prediction_for_area
from app.agents.vision_agent import run_image_analysis
from app.agents.financial_agent import (
    run_income_data, run_cost_of_living_data, run_rental_data,
    run_property_market_data, run_affordable_markets_data,
    run_financial_comparison, run_financial_summary
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Define API models
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

class QueryRequest(BaseModel):
    """Query request model."""
    query: str

class VisionRequest(BaseModel):
    """Vision request model."""
    link: str
    description: str
    location: str

class PredictionRequest(BaseModel):
    """Prediction request model."""
    area: Optional[str] = None

class FinancialAreaRequest(BaseModel):
    """Financial area request model."""
    area: Optional[str] = None

class FinancialCategoryRequest(BaseModel):
    """Financial category request model."""
    category: Optional[str] = None

class FinancialRentalRequest(BaseModel):
    """Financial rental request model."""
    area: Optional[str] = None
    property_type: Optional[str] = None

class FinancialPropertyRequest(BaseModel):
    """Financial property market request model."""
    area: Optional[str] = None
    property_type: Optional[str] = None

class FinancialComparisonRequest(BaseModel):
    """Financial comparison request model."""
    area1: str
    area2: str

# Chat endpoints
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Get a chat response.
    
    Args:
        request: Chat request
        
    Returns:
        Chat response
    """
    try:
        result = await run_chatbot(request.message, request.session_id)
        return ChatResponse(**result)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/healthcheck", response_model=StatusResponse)
async def healthcheck():
    """
    Check if the API is running.
    
    Returns:
        Status response
    """
    return StatusResponse(status="success", message="API is running")

# Twitter endpoints
@router.get("/twitter/summary")
async def get_twitter_summary():
    """
    Get a summary of recent tweets about Bengaluru.
    
    Returns:
        Twitter summary
    """
    summary = await run_twitter_to_summary()
    return {"TwitterSummary": summary}

# Weather endpoints
@router.get("/weather/summary/{query}")
async def get_weather_summary(query: str):
    """
    Get a weather summary for the specified location.
    
    Args:
        query: Location query
        
    Returns:
        Weather summary
    """
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    
    weather_summary = await run_weather_summary(query)
    if "error" in weather_summary:
        raise HTTPException(status_code=500, detail=weather_summary["error"])
    return weather_summary

# News endpoints
@router.get("/news/summary")
async def get_news_summary():
    """
    Get a summary of recent news about Bengaluru.
    
    Returns:
        News summary
    """
    news_articles = run_bengaluru_news()
    if not news_articles:
        raise HTTPException(status_code=404, detail="No news articles found")
    return news_articles

# Vision endpoints
@router.post("/vision/summary")
async def get_vision_summary(request: VisionRequest):
    """
    Analyze an image with the vision agent.
    
    Args:
        request: Vision request
        
    Returns:
        Vision summary
    """
    vision_data = run_image_analysis(request.link, request.description, request.location)
    if not vision_data:
        raise HTTPException(status_code=404, detail="No Vision data found")
    return {"image": request.link, "location": request.location, "AI response": vision_data}

# Prediction endpoints
@router.post("/prediction")
async def get_prediction(request: PredictionRequest = None):
    """
    Get a prediction of potential civic issues in Bengaluru.
    
    Args:
        request: Optional prediction request with area
        
    Returns:
        Prediction summary
    """
    try:
        # Log the request for debugging
        logger.info(f"Processing prediction request: {request}")
        
        if request and request.area:
            # Get prediction for specific area
            area = request.area
            logger.info(f"Generating area-specific prediction for: {area}")
            prediction = await run_prediction_for_area(area)
        else:
            # Get general prediction
            logger.info("Generating general Bengaluru prediction")
            prediction = await run_prediction_to_summary()
        
        # Return the prediction with a 200 status code
        return {"prediction": prediction}
    
    except Exception as e:
        # Log the full error with traceback
        logger.error(f"Error in prediction endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

# Financial endpoints
@router.post("/financial/income")
async def get_income_data(request: FinancialAreaRequest = None):
    """
    Get average income data for Bengaluru.
    
    Args:
        request: Optional area filter
        
    Returns:
        Income data
    """
    try:
        area = request.area if request and request.area else None
        logger.info(f"Fetching income data for area: {area}")
        
        income_data = await run_income_data(area)
        return {"data": income_data}
    
    except Exception as e:
        logger.error(f"Error in income endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching income data: {str(e)}")

@router.post("/financial/cost-of-living")
async def get_cost_of_living(request: FinancialCategoryRequest = None):
    """
    Get cost of living data for Bengaluru.
    
    Args:
        request: Optional category filter
        
    Returns:
        Cost of living data
    """
    try:
        category = request.category if request and request.category else None
        logger.info(f"Fetching cost of living data for category: {category}")
        
        cost_data = await run_cost_of_living_data(category)
        return {"data": cost_data}
    
    except Exception as e:
        logger.error(f"Error in cost of living endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching cost of living data: {str(e)}")

@router.post("/financial/rental")
async def get_rental_data(request: FinancialRentalRequest = None):
    """
    Get rental cost data for Bengaluru.
    
    Args:
        request: Optional area and property type filters
        
    Returns:
        Rental data
    """
    try:
        area = request.area if request and request.area else None
        property_type = request.property_type if request and request.property_type else None
        logger.info(f"Fetching rental data for area: {area}, property type: {property_type}")
        
        rental_data = await run_rental_data(area, property_type)
        return {"data": rental_data}
    
    except Exception as e:
        logger.error(f"Error in rental endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching rental data: {str(e)}")

@router.post("/financial/property-market")
async def get_property_market(request: FinancialPropertyRequest = None):
    """
    Get property market data for Bengaluru.
    
    Args:
        request: Optional area and property type filters
        
    Returns:
        Property market data
    """
    try:
        area = request.area if request and request.area else None
        property_type = request.property_type if request and request.property_type else None
        logger.info(f"Fetching property market data for area: {area}, property type: {property_type}")
        
        property_data = await run_property_market_data(area, property_type)
        return {"data": property_data}
    
    except Exception as e:
        logger.error(f"Error in property market endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching property market data: {str(e)}")

@router.post("/financial/affordable-markets")
async def get_affordable_markets(request: FinancialCategoryRequest = None):
    """
    Get affordable markets data for Bengaluru.
    
    Args:
        request: Optional category filter
        
    Returns:
        Affordable markets data
    """
    try:
        category = request.category if request and request.category else None
        logger.info(f"Fetching affordable markets data for category: {category}")
        
        markets_data = await run_affordable_markets_data(category)
        return {"data": markets_data}
    
    except Exception as e:
        logger.error(f"Error in affordable markets endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching affordable markets data: {str(e)}")

@router.post("/financial/compare-areas")
async def compare_areas(request: FinancialComparisonRequest):
    """
    Compare financial data between two areas in Bengaluru.
    
    Args:
        request: Areas to compare
        
    Returns:
        Comparison data
    """
    try:
        logger.info(f"Comparing areas: {request.area1} and {request.area2}")
        
        comparison_data = await run_financial_comparison(request.area1, request.area2)
        return {"data": comparison_data}
    
    except Exception as e:
        logger.error(f"Error in area comparison endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error comparing areas: {str(e)}")

@router.post("/financial/summary")
async def get_financial_summary(request: FinancialAreaRequest = None):
    """
    Get a comprehensive financial summary for Bengaluru.
    
    Args:
        request: Optional area filter
        
    Returns:
        Financial summary
    """
    try:
        area = request.area if request and request.area else None
        logger.info(f"Generating financial summary for area: {area}")
        
        summary_data = await run_financial_summary(area)
        return {"data": summary_data}
    
    except Exception as e:
        logger.error(f"Error in financial summary endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating financial summary: {str(e)}")

# Test endpoint to verify API is working
@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify API is working."""
    return {"status": "success", "message": "API is working!"}