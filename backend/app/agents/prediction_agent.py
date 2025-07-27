"""
Prediction Agent for Bengaluru Civic Issues with JSON Output

This agent analyzes data from weather, news, and social media sources
to predict potential civic issues in Bengaluru and provides output
in both text and JSON formats for frontend integration.
"""

import logging
import pandas as pd
import random
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

from app.services.prediction_service import PredictionService
from app.services.twitter_service import TwitterCivicAgent
from app.services.weather_service import WeatherFetcher
from app.services.news_service import BengaluruNewsFetcher
from app.utils.gemini import generate_response

# Configure logging
logger = logging.getLogger(__name__)

# Area-specific known issues database for fallback
AREA_KNOWLEDGE = {
    "koramangala": {
        "flood_spots": [
            {"location": "80 Feet Road near Sony World Signal", "severity": "high", "details": "Poor drainage system leads to significant waterlogging during moderate to heavy rainfall"},
            {"location": "Koramangala 4th Block near Forum Mall", "severity": "medium", "details": "Road tends to flood during rainfall, affecting traffic flow and pedestrian movement"},
            {"location": "Koramangala 3rd Block near Jyoti Nivas College", "severity": "low", "details": "Minor waterlogging possible during heavy rainfall"}
        ],
        "traffic_spots": [
            {"location": "Sony World Signal", "severity": "high", "details": "Major intersection with frequent congestion during peak hours (9-11 AM, 5-7 PM)"},
            {"location": "Forum Mall junction", "severity": "high", "details": "Shopping area with heavy vehicle and pedestrian traffic, especially on weekends"},
            {"location": "80 Feet Road", "severity": "medium", "details": "Main thoroughfare with moderate to heavy traffic throughout the day"}
        ],
        "infrastructure_issues": [
            {"location": "Inner roads of 5th Block", "severity": "medium", "details": "Multiple potholes reported after recent rainfall"},
            {"location": "Drainage system near Raheja Arcade", "severity": "low", "details": "Aging infrastructure that may cause issues during heavy rainfall"},
            {"location": "Road quality in parts of 1st Block", "severity": "medium", "details": "Uneven surfaces and patches that can worsen after rain"}
        ]
    },
    "whitefield": {
        "flood_spots": [
            {"location": "ITPL Main Road junction", "severity": "high", "details": "Prone to severe waterlogging during rainfall due to inadequate drainage"},
            {"location": "Hope Farm junction", "severity": "medium", "details": "Water accumulation during moderate to heavy rainfall"},
            {"location": "Varthur Kodi", "severity": "high", "details": "Area near Varthur Lake experiences significant flooding during monsoon"}
        ],
        "traffic_spots": [
            {"location": "Graphite India signal", "severity": "high", "details": "Major bottleneck during peak hours with traffic jams extending for kilometers"},
            {"location": "ITPL Main Road", "severity": "high", "details": "Heavy traffic throughout the day due to IT companies and residential complexes"},
            {"location": "Whitefield Main Road", "severity": "medium", "details": "Congestion due to ongoing metro construction and narrow road width"}
        ],
        "infrastructure_issues": [
            {"location": "Roads near Phoenix Marketcity", "severity": "medium", "details": "Multiple potholes that worsen during rainy season"},
            {"location": "Whitefield Main Road", "severity": "high", "details": "Ongoing metro construction causing road quality issues"},
            {"location": "Hoodi Circle", "severity": "medium", "details": "Deteriorating road conditions reported by residents"}
        ]
    },
    "indiranagar": {
        "flood_spots": [
            {"location": "100 Feet Road near CMH Road junction", "severity": "medium", "details": "Water accumulation during moderate to heavy rainfall"},
            {"location": "Doopanahalli underpass", "severity": "high", "details": "Prone to flooding during rainfall, sometimes becoming impassable"},
            {"location": "Low-lying areas near Old Airport Road", "severity": "low", "details": "Minor waterlogging possible during heavy rainfall"}
        ],
        "traffic_spots": [
            {"location": "100 Feet Road", "severity": "high", "details": "Commercial hub with heavy traffic throughout the day and evening"},
            {"location": "Double Road junction", "severity": "medium", "details": "Congestion during peak hours due to narrow road width"},
            {"location": "CMH Road", "severity": "medium", "details": "Shopping area with heavy vehicle and pedestrian traffic, especially on weekends"}
        ],
        "infrastructure_issues": [
            {"location": "Inner roads of HAL 2nd Stage", "severity": "medium", "details": "Aging roads with multiple patches and potholes"},
            {"location": "Drainage system in Old Indiranagar", "severity": "low", "details": "Older infrastructure that may cause issues during heavy rainfall"},
            {"location": "Footpaths on 12th Main", "severity": "medium", "details": "Uneven and broken in several places, hazardous for pedestrians"}
        ]
    },
    "marathahalli": {
        "flood_spots": [
            {"location": "Outer Ring Road near Marathahalli Bridge", "severity": "high", "details": "Significant waterlogging during rainfall, affecting traffic flow"},
            {"location": "Marathahalli underpass", "severity": "high", "details": "Frequently flooded during heavy rainfall, sometimes becoming impassable"},
            {"location": "Kundalahalli Gate", "severity": "medium", "details": "Water accumulation reported during moderate to heavy rainfall"}
        ],
        "traffic_spots": [
            {"location": "Marathahalli Bridge", "severity": "high", "details": "Major bottleneck with severe congestion during peak hours"},
            {"location": "Outer Ring Road", "severity": "high", "details": "Heavy traffic throughout the day, worsens during evenings"},
            {"location": "HAL Airport Road junction", "severity": "medium", "details": "Congestion due to merging traffic from multiple directions"}
        ],
        "infrastructure_issues": [
            {"location": "Service roads along Outer Ring Road", "severity": "medium", "details": "Narrow and pothole-filled, difficult for two-wheelers"},
            {"location": "Footpaths near Marathahalli Market", "severity": "medium", "details": "Broken or missing in several places, forcing pedestrians onto the road"},
            {"location": "Drainage system near Kundalahalli Gate", "severity": "high", "details": "Inadequate infrastructure causing frequent waterlogging"}
        ]
    }
}

# General Bengaluru issues for fallback
BENGALURU_GENERAL = {
    "flood_spots": [
        {"location": "Silk Board Junction", "severity": "high", "details": "Prone to severe waterlogging during rainfall"},
        {"location": "KR Puram Bridge", "severity": "medium", "details": "Water accumulation during moderate to heavy rainfall"},
        {"location": "Bellandur area near the lake", "severity": "high", "details": "Significant flooding during monsoon season"}
    ],
    "traffic_spots": [
        {"location": "Silk Board Junction", "severity": "high", "details": "One of the most congested junctions in the city"},
        {"location": "Hebbal Flyover", "severity": "high", "details": "Major bottleneck during peak hours"},
        {"location": "Outer Ring Road", "severity": "high", "details": "Heavy traffic throughout the day, especially near tech parks"}
    ],
    "infrastructure_issues": [
        {"location": "Old City areas", "severity": "medium", "details": "Aging infrastructure and narrow roads"},
        {"location": "Metro construction zones", "severity": "medium", "details": "Road quality issues and diversions"},
        {"location": "Underpasses during rainy season", "severity": "high", "details": "Prone to flooding due to inadequate drainage"}
    ]
}

async def run_prediction_to_summary() -> str:
    """
    Generate a comprehensive prediction summary for Bengaluru civic issues
    by analyzing weather, social media, and news data.
    
    Returns:
        str: A detailed summary of predicted civic issues in Bengaluru
    """
    try:
        logger.info("Starting civic issue prediction for Bengaluru")
        
        # Initialize services
        prediction_service = PredictionService()
        twitter_service = TwitterCivicAgent()
        weather_service = WeatherFetcher()
        news_service = BengaluruNewsFetcher()
        
        # Fetch weather data
        logger.info("Fetching weather data for Bengaluru")
        weather_data = weather_service.get_weather("Bengaluru")
        
        # Fetch social media data about civic issues
        logger.info("Fetching social media data about civic issues")
        tweet_query = "bengaluru flood OR waterlogging OR pothole OR traffic OR road condition OR power cut OR water supply"
        try:
            social_data = twitter_service.fetch_and_process(
                query=tweet_query, 
                issue_type="civic", 
                save=False
            )
        except Exception as e:
            logger.warning(f"Error fetching social data: {e}")
            social_data = None
        
        # Fetch news data
        logger.info("Fetching recent news articles about Bengaluru")
        try:
            news_articles = news_service.fetch_news()
        except Exception as e:
            logger.warning(f"Error fetching news data: {e}")
            news_articles = []
        
        # Check if we have weather data at minimum
        if not weather_data or "error" in weather_data:
            logger.warning("Insufficient weather data for prediction")
            # Even with no data, we'll generate a prediction with fallback data
            weather_condition = "Unknown"
            is_rainy = False
        else:
            weather_condition = weather_data.get("weather", "Unknown")
            is_rainy = any(term in weather_condition.lower() for term in ["rain", "shower", "drizzle", "thunderstorm"])
        
        # Always generate a prediction, even with limited data
        prediction_result = await generate_bengaluru_prediction(weather_data, social_data, news_articles, is_rainy)
        
        # Format the results into both text and JSON formats
        text_prediction = format_prediction(prediction_result)
        json_prediction = create_prediction_json(prediction_result)
        
        # Return combined result
        result = {
            "text": text_prediction,
            "json": json_prediction
        }
        
        return json.dumps(json_prediction)
        
    except Exception as e:
        logger.error(f"Error generating prediction: {e}", exc_info=True)
        # Even if there's an error, return a basic prediction using fallback data
        fallback_prediction = generate_fallback_prediction()
        fallback_json = create_prediction_json(fallback_prediction)
        return json.dumps(fallback_json)

async def run_prediction_for_area(area: str) -> str:
    """
    Generate a focused prediction for a specific area in Bengaluru.
    Always provides alerts with severity levels even with limited data.
    
    Args:
        area: Name of the area in Bengaluru (e.g., Whitefield, Koramangala)
        
    Returns:
        str: A detailed prediction for the specified area
    """
    try:
        logger.info(f"Starting civic issue prediction for {area}, Bengaluru")
        
        # Initialize services
        prediction_service = PredictionService()
        twitter_service = TwitterCivicAgent()
        weather_service = WeatherFetcher()
        
        # Fetch weather data
        logger.info(f"Fetching weather data relevant to {area}")
        try:
            weather_data = weather_service.get_weather("Bengaluru")  # Use Bengaluru weather as base
            weather_condition = weather_data.get("weather", "Unknown")
            is_rainy = any(term in weather_condition.lower() for term in ["rain", "shower", "drizzle", "thunderstorm"])
        except Exception as e:
            logger.warning(f"Error fetching weather data: {e}")
            weather_data = None
            weather_condition = "Unknown"
            is_rainy = False
        
        # Fetch area-specific social media data
        logger.info(f"Fetching social media data specific to {area}")
        area_query = f"{area} bengaluru flood OR waterlogging OR pothole OR traffic OR road condition OR power cut OR water supply"
        try:
            social_data = twitter_service.fetch_and_process(
                query=area_query, 
                issue_type="civic", 
                save=False
            )
        except Exception as e:
            logger.warning(f"Error fetching social data for {area}: {e}")
            social_data = None
        
        # Generate area-specific prediction
        logger.info(f"Generating civic issue prediction for {area}")
        prediction_result = await generate_area_prediction(area, weather_data, social_data, is_rainy)
        
        # Format the results into both text and JSON formats
        text_prediction = format_area_prediction(area, prediction_result)
        json_prediction = create_area_prediction_json(area, prediction_result)
        
        # Return the JSON result
        return json.dumps(json_prediction)
        
    except Exception as e:
        logger.error(f"Error generating prediction for {area}: {e}", exc_info=True)
        # Even if there's an error, return a basic area prediction using fallback data
        fallback_prediction = generate_fallback_area_prediction(area)
        fallback_json = create_area_prediction_json(area, fallback_prediction)
        return json.dumps(fallback_json)

async def generate_bengaluru_prediction(weather_data, social_data, news_articles, is_rainy) -> Dict[str, Any]:
    """Generate a prediction for Bengaluru, ensuring alerts are always provided."""
    try:
        # If we have enough data, try to use the prediction service
        if weather_data and social_data is not None and not social_data.empty and news_articles:
            # Prepare inputs for the prediction service
            prediction_inputs = {
                "weather": weather_data,
                "social_data": social_data,
                "news_articles": news_articles
            }
            
            # Try to use the prediction service
            try:
                prediction_service = PredictionService()
                prediction_result = await prediction_service.predict_civic_issues(prediction_inputs)
                if prediction_result:
                    # Ensure we have all required fields
                    ensure_prediction_fields(prediction_result, is_rainy)
                    return prediction_result
            except Exception as e:
                logger.warning(f"Error using prediction service: {e}")
                # Continue to fallback if prediction service fails
        
        # If we don't have enough data or prediction service failed, use fallback
        logger.info("Using fallback prediction for Bengaluru")
        return generate_fallback_prediction(is_rainy)
        
    except Exception as e:
        logger.error(f"Error in generate_bengaluru_prediction: {e}", exc_info=True)
        return generate_fallback_prediction(is_rainy)

async def generate_area_prediction(area, weather_data, social_data, is_rainy) -> Dict[str, Any]:
    """Generate a prediction for a specific area, ensuring alerts are always provided."""
    try:
        area_lower = area.lower()
        
        # If we have enough data, try to use the prediction service
        if weather_data and social_data is not None and not social_data.empty:
            # Prepare inputs for area-specific prediction
            prediction_inputs = {
                "area": area,
                "weather": weather_data,
                "social_data": social_data,
                "is_area_specific": True
            }
            
            # Try to use the prediction service
            try:
                prediction_service = PredictionService()
                prediction_result = await prediction_service.predict_area_issues(prediction_inputs)
                if prediction_result:
                    # Ensure we have all required fields
                    ensure_area_prediction_fields(prediction_result, area, is_rainy)
                    return prediction_result
            except Exception as e:
                logger.warning(f"Error using prediction service for {area}: {e}")
                # Continue to fallback if prediction service fails
        
        # If we don't have enough data or prediction service failed, use area-specific fallback
        logger.info(f"Using fallback prediction for {area}")
        return generate_fallback_area_prediction(area, is_rainy)
        
    except Exception as e:
        logger.error(f"Error in generate_area_prediction for {area}: {e}", exc_info=True)
        return generate_fallback_area_prediction(area, is_rainy)

def generate_fallback_prediction(is_rainy=False) -> Dict[str, Any]:
    """Generate a fallback prediction for Bengaluru when data is limited."""
    # Get current date for summary
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    today_str = today.strftime("%A, %B %d")
    tomorrow_str = tomorrow.strftime("%A, %B %d")
    
    # Adjust summary based on rain conditions
    if is_rainy:
        summary = f"Based on weather patterns, Bengaluru is likely to experience rainfall today ({today_str}) and possibly tomorrow ({tomorrow_str}). This may lead to waterlogging in low-lying areas, especially near known flooding spots. Traffic congestion is expected to worsen, particularly during peak hours near major junctions and tech corridors."
    else:
        summary = f"For {today_str} and {tomorrow_str}, Bengaluru is expected to have typical urban challenges. Traffic congestion will be significant during peak hours (8-11 AM and 5-8 PM) at major junctions. Infrastructure issues like potholes and road quality may affect commutes in certain areas."
    
    # Create prediction with alerts from our knowledge base
    prediction = {
        "summary": summary,
        "flood_alerts": generate_alerts_from_knowledge(BENGALURU_GENERAL["flood_spots"], is_rainy),
        "traffic_alerts": generate_alerts_from_knowledge(BENGALURU_GENERAL["traffic_spots"], False),
        "infrastructure_alerts": generate_alerts_from_knowledge(BENGALURU_GENERAL["infrastructure_issues"], is_rainy),
        "confidence_score": 0.65 if is_rainy else 0.7
    }
    
    return prediction

def generate_fallback_area_prediction(area, is_rainy=False) -> Dict[str, Any]:
    """Generate a fallback prediction for a specific area when data is limited."""
    area_lower = area.lower()
    
    # Get current date for summary
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    today_str = today.strftime("%A, %B %d")
    tomorrow_str = tomorrow.strftime("%A, %B %d")
    
    # Get area data from knowledge base or use general data
    area_data = AREA_KNOWLEDGE.get(area_lower)
    
    if area_data:
        # We have specific knowledge about this area
        if is_rainy:
            summary = f"For {today_str} and {tomorrow_str}, {area} may experience rainfall which could lead to waterlogging in low-lying areas, particularly near {area_data['flood_spots'][0]['location']} and {area_data['flood_spots'][1]['location']}. Traffic congestion is expected to increase during rainfall, especially at major junctions."
        else:
            summary = f"For {today_str} and {tomorrow_str}, {area} is expected to experience typical traffic congestion at key junctions such as {area_data['traffic_spots'][0]['location']} during peak hours (8-11 AM and 5-8 PM). Some infrastructure issues may affect commutes in certain sections."
        
        # Create alerts for this area from our knowledge base
        alerts = []
        hotspots = []
        
        # Add flood spots as alerts and hotspots if rainy
        if is_rainy:
            for spot in area_data["flood_spots"]:
                alerts.append({
                    "location": spot["location"],
                    "issue": "waterlogging",
                    "severity": spot["severity"],
                    "details": spot["details"]
                })
                hotspots.append({
                    "location": spot["location"],
                    "issue": "flooding risk",
                    "severity": spot["severity"]
                })
        
        # Always add traffic spots
        for spot in area_data["traffic_spots"]:
            alerts.append({
                "location": spot["location"],
                "issue": "traffic congestion",
                "severity": spot["severity"],
                "details": spot["details"]
            })
            hotspots.append({
                "location": spot["location"],
                "issue": "congestion",
                "severity": spot["severity"]
            })
        
        # Add infrastructure issues
        for spot in area_data["infrastructure_issues"]:
            alerts.append({
                "location": spot["location"],
                "issue": "infrastructure",
                "severity": spot["severity"],
                "details": spot["details"]
            })
            
        # Generate area-specific recommendations
        recommendations = generate_area_recommendations(area, is_rainy, alerts)
        
    else:
        # We don't have specific knowledge about this area, create generic content
        if is_rainy:
            summary = f"For {today_str} and {tomorrow_str}, {area} may experience rainfall which could lead to waterlogging in low-lying areas. Traffic congestion is expected to increase during rainfall, especially at major junctions."
        else:
            summary = f"For {today_str} and {tomorrow_str}, {area} is expected to experience typical traffic congestion at key junctions during peak hours (8-11 AM and 5-8 PM). Some infrastructure issues may affect commutes in certain sections."
        
        # Create generic alerts for this area
        alerts = [
            {
                "location": f"Main roads in {area}",
                "issue": "traffic congestion",
                "severity": "medium",
                "details": "Typical congestion during peak hours (8-11 AM and 5-8 PM)"
            },
            {
                "location": f"Market areas in {area}",
                "issue": "traffic congestion",
                "severity": "high",
                "details": "Heavy vehicle and pedestrian traffic, especially on weekends"
            }
        ]
        
        # Add rain-specific alerts if rainy
        if is_rainy:
            alerts.append({
                "location": f"Low-lying areas in {area}",
                "issue": "waterlogging",
                "severity": "medium",
                "details": "Possible water accumulation during rainfall due to drainage issues"
            })
            alerts.append({
                "location": f"Main junctions in {area}",
                "issue": "waterlogging",
                "severity": "low",
                "details": "Minor water accumulation possible during heavy rainfall"
            })
        
        # Add infrastructure alerts
        alerts.append({
            "location": f"Inner roads of {area}",
            "issue": "infrastructure",
            "severity": "medium",
            "details": "Potential for potholes and uneven surfaces, especially after rainfall"
        })
        
        # Generate generic hotspots
        hotspots = [
            {
                "location": f"Main market junction in {area}",
                "issue": "congestion",
                "severity": "high"
            },
            {
                "location": f"Major bus stops in {area}",
                "issue": "congestion",
                "severity": "medium"
            }
        ]
        
        # Generate generic recommendations
        recommendations = f"""
1. Allow extra time for commuting through {area}, especially during peak hours.
2. Consider alternative routes to avoid main junctions during rush hours.
3. Stay updated with weather forecasts before planning travel.
4. Exercise caution on inner roads where infrastructure issues may be present.
"""
        if is_rainy:
            recommendations += f"""
5. Avoid low-lying areas in {area} during heavy rainfall due to potential waterlogging.
6. Keep emergency contact numbers handy for waterlogging assistance.
"""
    
    # Create prediction with alerts from our knowledge base or generic content
    prediction = {
        "summary": summary,
        "alerts": alerts,
        "hotspots": hotspots,
        "recommendations": recommendations,
        "confidence_score": 0.6 if area_data else 0.5  # Lower confidence for unknown areas
    }
    
    return prediction

def generate_alerts_from_knowledge(knowledge_spots, is_rainy=False) -> List[Dict[str, Any]]:
    """Generate alerts from knowledge base data."""
    alerts = []
    
    for spot in knowledge_spots:
        # Adjust severity based on rain for flood spots
        severity = spot["severity"]
        if is_rainy and "flood" in str(knowledge_spots):
            # Increase severity during rain for flood-prone areas
            if severity == "low":
                severity = "medium"
            elif severity == "medium":
                severity = "high"
        
        # Create the alert
        alert = {
            "area": spot["location"],
            "risk_level": severity,
            "prediction": spot["details"]
        }
        alerts.append(alert)
    
    return alerts

def ensure_prediction_fields(prediction, is_rainy):
    """Ensure prediction has all required fields with reasonable values."""
    if "summary" not in prediction or not prediction["summary"]:
        prediction["summary"] = generate_fallback_prediction(is_rainy)["summary"]
    
    if "flood_alerts" not in prediction or not prediction["flood_alerts"]:
        prediction["flood_alerts"] = generate_fallback_prediction(is_rainy)["flood_alerts"]
    
    if "traffic_alerts" not in prediction or not prediction["traffic_alerts"]:
        prediction["traffic_alerts"] = generate_fallback_prediction(is_rainy)["traffic_alerts"]
    
    if "infrastructure_alerts" not in prediction or not prediction["infrastructure_alerts"]:
        prediction["infrastructure_alerts"] = generate_fallback_prediction(is_rainy)["infrastructure_alerts"]
    
    if "confidence_score" not in prediction:
        prediction["confidence_score"] = 0.65

def ensure_area_prediction_fields(prediction, area, is_rainy):
    """Ensure area prediction has all required fields with reasonable values."""
    fallback = generate_fallback_area_prediction(area, is_rainy)
    
    if "summary" not in prediction or not prediction["summary"]:
        prediction["summary"] = fallback["summary"]
    
    if "alerts" not in prediction or not prediction["alerts"]:
        prediction["alerts"] = fallback["alerts"]
    
    if "hotspots" not in prediction or not prediction["hotspots"]:
        prediction["hotspots"] = fallback["hotspots"]
    
    if "recommendations" not in prediction or not prediction["recommendations"]:
        prediction["recommendations"] = fallback["recommendations"]
    
    if "confidence_score" not in prediction:
        prediction["confidence_score"] = 0.6

def format_prediction(prediction_result: Dict[str, Any]) -> str:
    """
    Format prediction results into a readable, structured summary.
    
    Args:
        prediction_result: Dictionary containing prediction data
        
    Returns:
        str: Formatted prediction summary
    """
    summary = prediction_result.get("summary", "No summary available.")
    flood_alerts = prediction_result.get("flood_alerts", [])
    traffic_alerts = prediction_result.get("traffic_alerts", [])
    infrastructure_alerts = prediction_result.get("infrastructure_alerts", [])
    confidence = prediction_result.get("confidence_score", 0.5)
    
    formatted_summary = f"""
BENGALURU CIVIC PREDICTION SUMMARY
==================================

{summary}

ALERTS BY CATEGORY:
------------------

🌧️ FLOODING & WATERLOGGING: 
{format_alerts(flood_alerts)}

🚗 TRAFFIC CONGESTION: 
{format_alerts(traffic_alerts)}

⚠️ INFRASTRUCTURE ISSUES: 
{format_alerts(infrastructure_alerts)}

RECOMMENDATIONS:
---------------
{generate_recommendations(flood_alerts, traffic_alerts, infrastructure_alerts)}

This prediction is based on current weather conditions, recent news, and social media activity.
Confidence level: {int(confidence * 100)}%
    """
    
    return formatted_summary

def format_area_prediction(area: str, prediction_result: Dict[str, Any]) -> str:
    """
    Format area-specific prediction results into a readable, structured summary.
    
    Args:
        area: Name of the area
        prediction_result: Dictionary containing prediction data
        
    Returns:
        str: Formatted area prediction summary
    """
    summary = prediction_result.get("summary", f"No specific issues predicted for {area} at this time.")
    alerts = prediction_result.get("alerts", [])
    hotspots = prediction_result.get("hotspots", [])
    recommendations = prediction_result.get("recommendations", "No specific recommendations at this time.")
    confidence = prediction_result.get("confidence_score", 0.5)
    
    formatted_summary = f"""
CIVIC PREDICTION FOR {area.upper()}, BENGALURU
{'=' * (len(area) + 29)}

{summary}

SPECIFIC ALERTS:
--------------
{format_area_alerts(alerts)}

HOTSPOT LOCATIONS:
----------------
{format_hotspots(hotspots)}

RECOMMENDATIONS:
--------------
{recommendations}

This prediction is based on current weather conditions and recent social media activity.
Confidence level: {int(confidence * 100)}%
    """
    
    return formatted_summary

def create_prediction_json(prediction_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a JSON-friendly structure for the prediction result.
    
    Args:
        prediction_result: Dictionary containing prediction data
        
    Returns:
        Dict: JSON-friendly prediction data
    """
    summary = prediction_result.get("summary", "No summary available.")
    flood_alerts = prediction_result.get("flood_alerts", [])
    traffic_alerts = prediction_result.get("traffic_alerts", [])
    infrastructure_alerts = prediction_result.get("infrastructure_alerts", [])
    confidence = prediction_result.get("confidence_score", 0.5)
    
    # Sort alerts by severity
    alerts_by_severity = {
        "high": [],
        "medium": [],
        "low": []
    }
    
    # Process flood alerts
    for alert in flood_alerts:
        severity = alert.get("risk_level", "medium").lower()
        if severity not in alerts_by_severity:
            severity = "medium"
        
        alert_json = {
            "location": alert.get("area", "Unknown location"),
            "issue": "waterlogging",
            "details": alert.get("prediction", "No details available"),
            "severity": severity,
            "category": "flooding"
        }
        alerts_by_severity[severity].append(alert_json)
    
    # Process traffic alerts
    for alert in traffic_alerts:
        severity = alert.get("congestion_level", alert.get("risk_level", "medium")).lower()
        if severity not in alerts_by_severity:
            severity = "medium"
        
        alert_json = {
            "location": alert.get("area", "Unknown location"),
            "issue": "traffic congestion",
            "details": alert.get("prediction", "No details available"),
            "severity": severity,
            "category": "traffic"
        }
        alerts_by_severity[severity].append(alert_json)
    
    # Process infrastructure alerts
    for alert in infrastructure_alerts:
        severity = alert.get("risk_level", "medium").lower()
        if severity not in alerts_by_severity:
            severity = "medium"
        
        alert_json = {
            "location": alert.get("area", "Unknown location"),
            "issue": alert.get("issue_type", "infrastructure issue"),
            "details": alert.get("prediction", "No details available"),
            "severity": severity,
            "category": "infrastructure"
        }
        alerts_by_severity[severity].append(alert_json)
    
    # Create recommendations
    recommendations = generate_recommendations(flood_alerts, traffic_alerts, infrastructure_alerts).split("\n")
    recommendations = [rec.strip("- ") for rec in recommendations if rec.strip()]
    
    # Create the final JSON structure
    json_result = {
        "summary": summary,
        "alerts": {
            "high": alerts_by_severity["high"],
            "medium": alerts_by_severity["medium"],
            "low": alerts_by_severity["low"]
        },
        "recommendations": recommendations,
        "confidence_score": int(confidence * 100)
    }
    
    return json_result

def create_area_prediction_json(area: str, prediction_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a JSON-friendly structure for the area prediction result.
    
    Args:
        area: Name of the area
        prediction_result: Dictionary containing prediction data
        
    Returns:
        Dict: JSON-friendly area prediction data
    """
    summary = prediction_result.get("summary", f"No specific issues predicted for {area} at this time.")
    alerts = prediction_result.get("alerts", [])
    hotspots = prediction_result.get("hotspots", [])
    recommendations = prediction_result.get("recommendations", "")
    confidence = prediction_result.get("confidence_score", 0.5)
    
    # Sort alerts by severity
    alerts_by_severity = {
        "high": [],
        "medium": [],
        "low": []
    }
    
    # Process alerts
    for alert in alerts:
        severity = alert.get("severity", "medium").lower()
        if severity not in alerts_by_severity:
            severity = "medium"
        
        issue_type = alert.get("issue", "general issue")
        category = "infrastructure"
        if "water" in issue_type.lower() or "flood" in issue_type.lower():
            category = "flooding"
        elif "traffic" in issue_type.lower() or "congestion" in issue_type.lower():
            category = "traffic"
        
        alert_json = {
            "location": alert.get("location", "Unknown location"),
            "issue": issue_type,
            "details": alert.get("details", "No details available"),
            "severity": severity,
            "category": category
        }
        alerts_by_severity[severity].append(alert_json)
    
    # Process hotspots
    hotspots_json = []
    for hotspot in hotspots:
        hotspots_json.append({
            "location": hotspot.get("location", "Unknown location"),
            "issue": hotspot.get("issue", "Unknown issue"),
            "severity": hotspot.get("severity", "medium").lower()
        })
    
    # Process recommendations
    if isinstance(recommendations, str):
        recommendations = recommendations.split("\n")
    recommendations = [rec.strip("- ") for rec in recommendations if rec.strip()]
    
    # Create the final JSON structure
    json_result = {
        "area": area,
        "summary": summary,
        "alerts": {
            "high": alerts_by_severity["high"],
            "medium": alerts_by_severity["medium"],
            "low": alerts_by_severity["low"]
        },
        "hotspots": hotspots_json,
        "recommendations": recommendations,
        "confidence_score": int(confidence * 100)
    }
    
    return json_result

def format_alerts(alerts: List[Dict[str, Any]]) -> str:
    """Format a list of alerts into a readable string."""
    if not alerts:
        return "No significant alerts at this time."
    
    formatted = []
    for alert in alerts:
        if isinstance(alert, dict):
            area = alert.get('area', 'Unknown area')
            level = alert.get('risk_level', alert.get('congestion_level', 'moderate')).upper()
            details = alert.get('prediction', 'No details available')
            formatted.append(f"- {area} ({level}): {details}")
    
    return "\n".join(formatted) if formatted else "No details available."

def format_area_alerts(alerts: List[Dict[str, Any]]) -> str:
    """Format a list of area-specific alerts into a readable string."""
    if not alerts:
        return "No significant alerts at this time."
    
    formatted = []
    for alert in alerts:
        if isinstance(alert, dict):
            location = alert.get('location', 'Unknown location')
            issue = alert.get('issue', 'general issue')
            severity = alert.get('severity', 'moderate').upper()
            details = alert.get('details', 'No details available')
            formatted.append(f"- {location} - {issue.title()} ({severity}): {details}")
    
    return "\n".join(formatted) if formatted else "No details available."

def format_hotspots(hotspots: List[Dict[str, Any]]) -> str:
    """Format a list of hotspot locations into a readable string."""
    if not hotspots:
        return "No specific hotspots identified at this time."
    
    formatted = []
    for hotspot in hotspots:
        if isinstance(hotspot, dict):
            location = hotspot.get('location', 'Unknown location')
            issue = hotspot.get('issue', 'Unknown issue')
            severity = hotspot.get('severity', 'moderate').upper()
            formatted.append(f"- {location}: {issue} ({severity})")
    
    return "\n".join(formatted) if formatted else "No specific hotspots identified."

def generate_recommendations(flood_alerts, traffic_alerts, infrastructure_alerts) -> str:
    """Generate recommendations based on alerts."""
    recommendations = []
    
    # Add flood recommendations if needed
    if flood_alerts:
        recommendations.append("- Avoid low-lying areas during heavy rainfall, especially those mentioned in flooding alerts.")
        recommendations.append("- Keep emergency contact numbers handy for waterlogging assistance.")
        recommendations.append("- Use waterproof bags and cases for electronic devices when traveling in rainy conditions.")
    
    # Add traffic recommendations if needed
    if traffic_alerts:
        recommendations.append("- Plan alternative routes to avoid congested areas mentioned in traffic alerts.")
        recommendations.append("- Allow extra travel time during peak hours, especially if rain is forecast.")
        recommendations.append("- Consider using public transportation or carpooling to reduce congestion.")
    
    # Add infrastructure recommendations if needed
    if infrastructure_alerts:
        recommendations.append("- Report dangerous potholes or infrastructure issues to BBMP helpline (080-22660000).")
        recommendations.append("- Exercise caution around areas with known infrastructure issues, especially in rain.")
        recommendations.append("- Consider using navigation apps that provide real-time updates on road conditions.")
    
    # General recommendations
    recommendations.append("- Stay updated with weather forecasts before planning travel.")
    recommendations.append("- Consider working from home if severe weather or traffic conditions are predicted.")
    
    return "\n".join(recommendations) if recommendations else "No specific recommendations at this time."

def generate_area_recommendations(area, is_rainy, alerts) -> str:
    """Generate area-specific recommendations based on alerts."""
    recommendations = []
    
    # Add area-specific recommendations
    recommendations.append(f"- Plan travel routes through {area} to avoid known congestion points, especially during peak hours.")
    
    # Check for high severity alerts
    high_severity_issues = [alert for alert in alerts if alert.get('severity') == 'high']
    if high_severity_issues:
        high_locations = ", ".join([issue.get('location') for issue in high_severity_issues[:2]])
        recommendations.append(f"- Avoid {high_locations} if possible, as these areas have high-severity issues.")
    
    # Add rain-specific recommendations
    if is_rainy:
        recommendations.append(f"- Check for waterlogging updates before traveling through {area} during rainfall.")
        recommendations.append(f"- Keep a 10-15 minute buffer in travel plans for {area} due to potential rain-related delays.")
    
    # Add issue-specific recommendations
    traffic_issues = [alert for alert in alerts if alert.get('issue') == 'traffic congestion']
    if traffic_issues:
        recommendations.append(f"- Consider alternative transport options when traveling through {area} during peak hours.")
    
    infra_issues = [alert for alert in alerts if alert.get('issue') == 'infrastructure']
    if infra_issues:
        recommendations.append(f"- Drive cautiously on inner roads in {area} due to reported infrastructure issues.")
    
    # Add general recommendations
    recommendations.append(f"- Stay updated with real-time traffic apps when traveling through {area}.")
    recommendations.append(f"- Report any new civic issues in {area} to the BBMP helpline (080-22660000).")
    
    return "\n".join(recommendations)