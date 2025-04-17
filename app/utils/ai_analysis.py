"""
Module for generating trading strategy analysis using OpenAI's ChatGPT API.
"""

import os
import base64
import logging
import time
from typing import Dict, Any, List, Optional
import openai
from openai import OpenAI
from app.utils.api_helpers import get_api_key
from config.settings import MODEL_NAME_OPENAI, MAX_RETRIES, RETRY_DELAY

# Configure logging
logger = logging.getLogger(__name__)

def initialize_openai_client() -> OpenAI:
    """
    Initialize and return an OpenAI client using the Requesty router (ROUTER_API_KEY and REQUESTY_BASE_URL).
    """
    from config.settings import ROUTER_API_KEY, REQUESTY_BASE_URL
    if not ROUTER_API_KEY or not REQUESTY_BASE_URL:
        logger.error("Missing ROUTER_API_KEY or REQUESTY_BASE_URL")
        raise ValueError("ROUTER_API_KEY and REQUESTY_BASE_URL are required for router-based LLM access.")
    return OpenAI(
        api_key=ROUTER_API_KEY,
        base_url=REQUESTY_BASE_URL,
        default_headers={"Authorization": f"Bearer {ROUTER_API_KEY}"},
        timeout=60.0
    )

def construct_strategy_prompt(
    trend_info: Dict[str, Any], 
    structure_points: Dict[str, List[Dict[str, Any]]],
    ote_zone: Optional[Dict[str, Any]] = None
) -> str:
    """
    Construct a detailed prompt for the strategy analysis.
    
    Args:
        trend_info: Dictionary with trend direction, strength, current price, and SMAs
        structure_points: Dictionary with swing highs and swing lows
        ote_zone: Optional dictionary with OTE zone calculations
        
    Returns:
        Formatted prompt string for the GPT model
    """
    # Format swing points for readability
    swing_highs_formatted = []
    for h in structure_points.get('swing_highs', []):
        time_str = h['time'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(h['time'], 'strftime') else str(h['time'])
        swing_highs_formatted.append(f"${h['price']:.2f} at {time_str}")
    
    swing_lows_formatted = []
    for l in structure_points.get('swing_lows', []):
        time_str = l['time'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(l['time'], 'strftime') else str(l['time'])
        swing_lows_formatted.append(f"${l['price']:.2f} at {time_str}")
    
    # Start building the prompt
    prompt = f"""
    As a professional trading analyst, analyze the following XAUUSD (Gold) market data and provide a detailed explanation of the current setup according to the Fibonacci OTE strategy:
    
    Current Market Information:
    - Timeframe: M5 (5-minute candles)
    - Current Price: ${trend_info.get('current_price', 'N/A'):.2f}
    - Identified Trend: {trend_info.get('direction', 'Unknown')} ({trend_info.get('strength', 'Unknown')})
    """
    
    # Add SMA information if available
    if trend_info.get('sma20') is not None:
        prompt += f"    - 20-period SMA: ${trend_info['sma20']:.2f}\n"
    if trend_info.get('sma50') is not None:
        prompt += f"    - 50-period SMA: ${trend_info['sma50']:.2f}\n"
    
    prompt += f"""
    Recent Structure Points:
    - Swing Highs: {swing_highs_formatted}
    - Swing Lows: {swing_lows_formatted}
    """
    
    # Add OTE zone information if available
    if ote_zone and ote_zone.get('entry_price') is not None:
        prompt += f"""
    Pre-calculated Fibonacci Levels:
    - Entry Price (0.705 Fib): ${ote_zone['entry_price']:.2f}
    - OTE Zone: ${ote_zone['ote_zone']['start']:.2f} to ${ote_zone['ote_zone']['end']:.2f}
    - Stop Loss: ${ote_zone['stop_loss']:.2f}
    - Take Profit 1 (1:1 RR): ${ote_zone['take_profit1']:.2f}
    - Take Profit 2 (Swing): ${ote_zone['take_profit2']:.2f}
    """
    
    # Add strategy rules
    prompt += """
    Strategy Rules:
    For Bullish Trend:
    - Use Fibonacci from the last significant low to the last high
    - Enter buy limit at 0.705 Fibonacci level (OTE zone)
    - Place stop loss 3 pips below the last significant low
    - TP1 at 1:1 risk-reward ratio, TP2 at the 0% Fibonacci level
    
    For Bearish Trend:
    - Use Fibonacci from the last significant high to the last low
    - Enter sell limit at 0.705 Fibonacci level (OTE zone)
    - Place stop loss 3 pips above the last significant high
    - TP1 at 1:1 risk-reward ratio, TP2 at the 0% Fibonacci level
    
    Please provide:
    1. A detailed assessment of the current trend, including confirmation of BOS or CHoCH
    2. Identification of which swing points should be used for Fibonacci placement
    3. Calculation of the OTE zone (61.8% to 79% Fibonacci levels)
    4. Exact entry price recommendation at the 0.705 Fibonacci level
    5. Precise stop loss and take profit levels with pip distances
    6. Any potential warnings or special considerations for this setup
    7. A confidence rating (1-10) for this trading opportunity
    
    Support your analysis with specific price levels and clear reasoning.
    """
    
    return prompt

def generate_strategy_analysis(
    trend_info: Dict[str, Any],
    structure_points: Dict[str, List[Dict[str, Any]]],
    ote_zone: Optional[Dict[str, Any]] = None,
    chart_image_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate detailed trading strategy analysis using ChatGPT 4.1.
    
    Args:
        trend_info: Dictionary with trend direction, strength, current price, and SMAs
        structure_points: Dictionary with swing highs and swing lows
        ote_zone: Optional dictionary with OTE zone calculations
        chart_image_path: Optional path to a chart image for vision analysis
        
    Returns:
        Dictionary with the generated analysis and status information
        
    Raises:
        RuntimeError: If there's an error calling the OpenAI API
    """
    start_time = time.time()
    logger.info("Generating trading strategy analysis with ChatGPT")
    
    try:
        # Initialize OpenAI client
        client = initialize_openai_client()
        
        # Construct the prompt
        prompt = construct_strategy_prompt(trend_info, structure_points, ote_zone)
        
        # Set up the system prompt
        system_prompt = """You are an expert trading analyst specializing in Fibonacci trading strategies 
        for gold (XAUUSD). You provide precise, detailed analysis with exact price levels and clear reasoning. 
        Focus on concrete, actionable advice based on the Fibonacci OTE strategy, and ensure all calculations are accurate. 
        Format your response with clear headings and sections to make it easy to read and implement."""
        
        # Set up messages for the API call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        # Include image if provided (for vision capability)
        if chart_image_path and os.path.exists(chart_image_path):
            with open(chart_image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                
            # Replace the second message with content that includes the image
            messages[1] = {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        
        # Make the API call with retry logic
        response = None
        retries = 0
        
        while retries <= MAX_RETRIES:
            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME_OPENAI,
                    messages=messages,
                    temperature=0.2,  # Lower temperature for more consistent responses
                    max_tokens=2000
                )
                break  # Success, exit retry loop
                
            except (openai.RateLimitError, openai.APIConnectionError) as e:
                retries += 1
                if retries <= MAX_RETRIES:
                    logger.warning(f"OpenAI API error (attempt {retries}/{MAX_RETRIES}): {str(e)}. Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Max retries reached for OpenAI API call: {str(e)}")
                    raise RuntimeError(f"Failed to generate analysis after {MAX_RETRIES} retries: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Unexpected error calling OpenAI API: {str(e)}")
                raise RuntimeError(f"Failed to generate analysis: {str(e)}")
        
        # Process the response
        if response and response.choices and len(response.choices) > 0:
            analysis_text = response.choices[0].message.content
            
            elapsed_time = time.time() - start_time
            logger.info(f"Successfully generated analysis in {elapsed_time:.2f} seconds")
            
            return {
                "status": "success",
                "analysis": analysis_text,
                "elapsed_time": elapsed_time,
                "model": MODEL_NAME_OPENAI
            }
        else:
            logger.error("Empty or invalid response from OpenAI API")
            return {
                "status": "error",
                "analysis": "Failed to generate analysis: Empty response from AI model.",
                "elapsed_time": time.time() - start_time
            }
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating analysis: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "analysis": f"Failed to generate analysis: {str(e)}",
            "elapsed_time": elapsed_time
        }