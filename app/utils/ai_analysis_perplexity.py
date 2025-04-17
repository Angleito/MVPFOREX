"""
Module for generating trading strategy analysis using Perplexity Vision API.
This module provides functions to analyze XAUUSD (Gold) trading charts and market data.
"""
import time
import os
import base64
import logging
from typing import Dict, List, Any, Optional
import json
import openai

from config.settings import MODELS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PERPLEXITY_MODEL = MODELS['perplexity']['id']
PERPLEXITY_MAX_TOKENS = MODELS['perplexity']['max_tokens']
PERPLEXITY_TEMPERATURE = MODELS['perplexity']['temperature']


def initialize_perplexity_client() -> openai.OpenAI:
    """Initialize and return a Perplexity client using the Requesty router if configured."""
    from config.settings import ROUTER_API_KEY, REQUESTY_BASE_URL
    if not ROUTER_API_KEY or not REQUESTY_BASE_URL:
        raise ValueError("ROUTER_API_KEY and REQUESTY_BASE_URL are required for router-based LLM access.")
    return openai.OpenAI(
        api_key=ROUTER_API_KEY,
        base_url=REQUESTY_BASE_URL,
        default_headers={"Authorization": f"Bearer {ROUTER_API_KEY}"},
        timeout=60.0
    )

def construct_perplexity_strategy_prompt(
    trend_info: Dict[str, Any], 
    structure_points: Dict[str, List[Dict[str, Any]]],
    ote_zone: Optional[Dict[str, Any]] = None
) -> str:
    """Construct a prompt for Perplexity to analyze trading strategy.
    
    Args:
        trend_info: Dictionary containing trend information
        structure_points: Dictionary containing structure points (swing highs/lows)
        ote_zone: Optional dictionary containing OTE (Optimal Trade Entry) zone information
        
    Returns:
        A formatted prompt string
    """
    # Extract trend information
    trend_direction = trend_info.get('direction', 'Unknown')
    trend_strength = trend_info.get('strength', 'Unknown')
    current_price = trend_info.get('current_price', 0)
    sma20 = trend_info.get('sma20', 0)
    sma50 = trend_info.get('sma50', 0)
    
    # Format structure points
    formatted_swing_highs = []
    for high in structure_points.get('swing_highs', []):
        price = high.get('price', 0)
        time_str = high.get('time', '')
        formatted_swing_highs.append(f"${price:.2f} at {time_str}")
    
    formatted_swing_lows = []
    for low in structure_points.get('swing_lows', []):
        price = low.get('price', 0)
        time_str = low.get('time', '')
        formatted_swing_lows.append(f"${price:.2f} at {time_str}")
    
    # Build the prompt
    prompt = f"""
As a professional forex trading analyst, I need your detailed analysis on the XAUUSD (Gold) market data and chart I'm about to show you.

Current Market Data:
- Current Price: ${current_price:.2f}
- Trend Direction: {trend_direction}
- Trend Strength: {trend_strength}
- 20-period SMA: ${sma20:.2f}
- 50-period SMA: ${sma50:.2f}

Structure Points:
Swing Highs: {', '.join(formatted_swing_highs)}
Swing Lows: {', '.join(formatted_swing_lows)}
"""

    # Add OTE zone information if provided
    if ote_zone and isinstance(ote_zone, dict):
        entry_price = ote_zone.get('entry_price', 0)
        stop_loss = ote_zone.get('stop_loss', 0)
        take_profit1 = ote_zone.get('take_profit1', 0)
        take_profit2 = ote_zone.get('take_profit2', 0)
        ote_zone_range = ote_zone.get('ote_zone', {})
        ote_start = ote_zone_range.get('start', 0) if ote_zone_range is not None else 0
        ote_end = ote_zone_range.get('end', 0)
        
        prompt += f"""
Fibonacci Levels:
- Recommended Entry Price: ${entry_price:.2f}
- Stop Loss: ${stop_loss:.2f}
- Take Profit 1: ${take_profit1:.2f}
- Take Profit 2: ${take_profit2:.2f}
- OTE Zone: ${ote_start:.2f} - ${ote_end:.2f}
"""

    # Add analysis request
    prompt += """
Based on this information and the chart image, please provide:

1. A comprehensive technical analysis of the XAUUSD market situation
2. Commentary on the Fibonacci levels and key price zones
3. Trade recommendation including:
   - Entry strategy (limit order or market order)
   - Stop loss placement with reasoning
   - Take profit targets with reasoning
4. Risk management advice for this trade
5. Overall market sentiment and factors that could affect this trade

Please be specific with price levels and include your reasoning for all recommendations.
"""

    return prompt

def encode_image_to_base64(image_path: str) -> str:
    """Convert an image file to base64 encoding for Perplexity API."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_encoded = base64.b64encode(image_data).decode("utf-8")
    
    return base64_encoded

def generate_strategy_analysis_perplexity(
    trend_info: Dict[str, Any],
    structure_points: Dict[str, List[Dict[str, Any]]],
    ote_zone: Optional[Dict[str, Any]] = None,
    chart_image_path: Optional[str] = None
) -> Dict[str, Any]:
    # --- DEBUG LOGGING ---
    logger.info(f"[DEBUG] trend_info: {trend_info}")
    logger.info(f"[DEBUG] structure_points: {structure_points}")
    logger.info(f"[DEBUG] ote_zone: {ote_zone}")
    logger.info(f"[DEBUG] chart_image_path: {chart_image_path}")
    # --- END DEBUG LOGGING ---
    """Generate trading strategy analysis using Perplexity Vision.
    
    Args:
        trend_info: Dictionary containing trend information
        structure_points: Dictionary containing structure points (swing highs/lows)
        ote_zone: Optional dictionary containing OTE zone information
        chart_image_path: Optional path to chart image
        
    Returns:
        Dictionary containing analysis results
    """
    start_time = time.time()
    
    try:
        # Initialize client
        client = initialize_perplexity_client()
        
        # Construct prompt
        prompt = construct_perplexity_strategy_prompt(trend_info, structure_points, ote_zone)
        
        # Prepare messages for Perplexity
        if chart_image_path and os.path.exists(chart_image_path):
            logger.info(f"Including chart image in Perplexity analysis: {chart_image_path}")
            base64_image = encode_image_to_base64(chart_image_path)
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        else:
            logger.info("No chart image provided for Perplexity analysis")
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        
        # Call Perplexity API
        logger.info(f"Sending request to Perplexity API...")
        response = client.chat.completions.create(
            model=PERPLEXITY_MODEL,
            messages=messages,
            max_tokens=PERPLEXITY_MAX_TOKENS,
            temperature=PERPLEXITY_TEMPERATURE
        )
        
        elapsed_time = time.time() - start_time
        logger.info(f"Perplexity analysis completed in {elapsed_time:.2f} seconds")
        
        # Extract analysis from response
        if response.choices and len(response.choices) > 0:
            analysis_text = response.choices[0].message.content
            
            return {
                "status": "success",
                "analysis": analysis_text,
                "model": PERPLEXITY_MODEL,
                "elapsed_time": elapsed_time,
                "trend_info": trend_info,
                "ote_zone": ote_zone
            }
        else:
            return {
                "status": "error",
                "analysis": "No response received from Perplexity API",
                "elapsed_time": elapsed_time,
                "model": PERPLEXITY_MODEL
            }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating Perplexity analysis: {str(e)}", exc_info=True)
        
        return {
            "status": "error",
            "analysis": f"Error generating analysis: {str(e)}",
            "elapsed_time": elapsed_time,
            "model": PERPLEXITY_MODEL,
            "trend_info": trend_info,
            "ote_zone": ote_zone
        }