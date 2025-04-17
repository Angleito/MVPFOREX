"""
Module for generating trading strategy analysis using Anthropic's Claude 3.7 Vision API.
This module provides functions to analyze XAUUSD (Gold) trading charts and market data.
"""
import time
import os
import base64
import logging
from typing import Dict, List, Any, Optional
import json
from anthropic import Anthropic

from config.settings import ANTHROPIC_MODEL, ANTHROPIC_API_TEMPERATURE
from app.utils.data_processing import format_structure_points

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_api_key(provider: str) -> Optional[str]:
    """Get API key for the specified provider from environment variables."""
    env_vars = {
        'anthropic': ['ANTHROPIC_API_KEY', 'CLAUDE_API_KEY'],
    }
    
    for env_var in env_vars.get(provider.lower(), []):
        api_key = os.environ.get(env_var)
        if api_key:
            return api_key
    
    return None

def initialize_anthropic_client() -> Anthropic:
    """Initialize and return an Anthropic client."""
    api_key = get_api_key('anthropic')
    if not api_key:
        raise ValueError("Anthropic API key not found in environment variables")
    
    return Anthropic(api_key=api_key)

def construct_claude_strategy_prompt(
    trend_info: Dict[str, Any], 
    structure_points: Dict[str, List[Dict[str, Any]]],
    ote_zone: Optional[Dict[str, Any]] = None
) -> str:
    """Construct a prompt for Claude 3.7 to analyze trading strategy.
    
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
    formatted_swing_highs = format_structure_points(structure_points.get('swing_highs', []))
    formatted_swing_lows = format_structure_points(structure_points.get('swing_lows', []))
    
    # Build the prompt
    prompt = f"""
As an expert forex trading analyst, I need your analysis on the XAUUSD (Gold) trading chart I'm about to show you.

Market Overview:
- Current Price: ${current_price:.2f}
- Trend Direction: {trend_direction}
- Trend Strength: {trend_strength}
- SMA 20: ${sma20:.2f}
- SMA 50: ${sma50:.2f}

Swing Points:
Swing Highs:
{formatted_swing_highs}

Swing Lows:
{formatted_swing_lows}
"""

    # Add OTE zone information if provided
    if ote_zone and isinstance(ote_zone, dict):
        entry_price = ote_zone.get('entry_price', 0)
        stop_loss = ote_zone.get('stop_loss', 0)
        take_profit1 = ote_zone.get('take_profit1', 0)
        take_profit2 = ote_zone.get('take_profit2', 0)
        ote_zone_range = ote_zone.get('ote_zone', {})
        ote_start = ote_zone_range.get('start', 0)
        ote_end = ote_zone_range.get('end', 0)
        
        prompt += f"""
Pre-calculated Fibonacci Levels:
- Suggested Entry Price: ${entry_price:.2f}
- Stop Loss: ${stop_loss:.2f}
- Take Profit 1: ${take_profit1:.2f}
- Take Profit 2: ${take_profit2:.2f}
- OTE Zone: ${ote_start:.2f} - ${ote_end:.2f}
"""

    # Add strategy rules
    prompt += """
Strategy Rules:
1. Trade in the direction of the overall trend
2. Look for price action at key structure points (swing highs/lows)
3. Use Fibonacci retracement levels to find optimal entry points
4. Confirm entries with candlestick patterns and support/resistance
5. Place stop losses below/above significant structure
6. Use a minimum 1:2 risk-to-reward ratio

Analysis Request:
1. Identify the current market structure and trend
2. Analyze the provided chart and point out key price action
3. Evaluate potential trading opportunities based on the strategy rules
4. Suggest entry points, stop loss levels, and take profit targets
5. Highlight any significant risks or considerations for this trade

Please provide a detailed and professional analysis focused on practical trading advice.
"""

    return prompt

def encode_image_to_base64(image_path: str) -> str:
    """Convert an image file to base64 encoding for Claude API."""
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    with open(image_path, "rb") as image_file:
        image_data = image_file.read()
        base64_encoded = base64.b64encode(image_data).decode("utf-8")
    
    return base64_encoded

def generate_strategy_analysis_claude(
    trend_info: Dict[str, Any],
    structure_points: Dict[str, List[Dict[str, Any]]],
    ote_zone: Optional[Dict[str, Any]] = None,
    chart_image_path: Optional[str] = None
) -> Dict[str, Any]:
    """Generate trading strategy analysis using Claude 3.7 Vision.
    
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
        client = initialize_anthropic_client()
        
        # Construct prompt
        prompt = construct_claude_strategy_prompt(trend_info, structure_points, ote_zone)
        
        # Prepare messages for Claude
        messages = [
            {
                "role": "system",
                "content": "You are Claude 3.7, an expert forex trading analyst with years of experience analyzing XAUUSD (Gold) charts. Your analysis is concise, accurate, and focused on practical trading advice. You avoid hypothetical scenarios and focus on what the chart is actually showing. You always provide a clear recommendation on whether to buy, sell, or stay out of the market."
            }
        ]
        
        # Add user message with or without image
        if chart_image_path and os.path.exists(chart_image_path):
            logger.info(f"Including chart image in Claude analysis: {chart_image_path}")
            base64_image = encode_image_to_base64(chart_image_path)
            messages.append({
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            })
        else:
            logger.info("No chart image provided for Claude analysis")
            messages.append({
                "role": "user",
                "content": prompt
            })
        
        # Call Claude API
        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            temperature=ANTHROPIC_API_TEMPERATURE,
            messages=messages,
            max_tokens=4000
        )
        
        # Extract analysis text from response
        analysis_text = ""
        for content_block in response.content:
            if content_block.type == "text":
                analysis_text += content_block.text
        
        elapsed_time = time.time() - start_time
        logger.info(f"Claude analysis completed in {elapsed_time:.2f} seconds")
        
        return {
            "status": "success",
            "analysis": analysis_text,
            "model": ANTHROPIC_MODEL,
            "elapsed_time": elapsed_time,
            "trend_info": trend_info,
            "ote_zone": ote_zone
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating Claude analysis: {str(e)}", exc_info=True)
        
        return {
            "status": "error",
            "analysis": f"Error generating analysis: {str(e)}",
            "elapsed_time": elapsed_time,
            "trend_info": trend_info,
            "ote_zone": ote_zone
        }