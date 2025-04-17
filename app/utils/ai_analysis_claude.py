"""Module for generating trading strategy analysis using Anthropic's Claude 3.7 API."""
import os
import base64
import time
import logging
import json
import anthropic
from typing import Dict, Any, Optional, List
from config.settings import CLAUDE_MODEL_NAME, MAX_RETRIES, RETRY_DELAY

# Configure logging
logger = logging.getLogger(__name__)

def get_api_key(provider: str) -> Optional[str]:
    """Get API key for the specified AI provider.
    
    Args:
        provider: The provider name (e.g., 'anthropic')
        
    Returns:
        API key if found, None otherwise
    """
    api_key = None
    
    # Check for provider-specific environment variable
    if provider.lower() == 'anthropic':
        api_key = os.getenv('ANTHROPIC_API_KEY')
    
    # Fallback to generic API key variable (with prefix)
    if not api_key:
        api_key = os.getenv(f'{provider.upper()}_API_KEY')
    
    return api_key

def initialize_anthropic_client() -> anthropic.Anthropic:
    """Initialize and return an Anthropic client.
    
    Returns:
        Anthropic client instance
        
    Raises:
        ValueError: If the API key is missing
    """
    api_key = get_api_key('anthropic')
    
    if not api_key:
        logger.error("Missing Anthropic API key. Please set ANTHROPIC_API_KEY environment variable.")
        raise ValueError("Missing Anthropic API key. Please set ANTHROPIC_API_KEY environment variable.")
    
    return anthropic.Anthropic(api_key=api_key)

def construct_claude_strategy_prompt(
    trend_info: Dict[str, Any],
    structure_points: Dict[str, List[Dict[str, Any]]],
    ote_zone: Optional[Dict[str, Any]] = None
) -> str:
    """Construct a detailed prompt for Claude to analyze the trading strategy.
    
    Args:
        trend_info: Dictionary with trend direction, strength, current price, and SMAs
        structure_points: Dictionary with swing highs and swing lows
        ote_zone: Optional dictionary with OTE zone calculations
        
    Returns:
        Prompt string for Claude
    """
    # Format the prompt with detailed market information
    prompt = "Please analyze the current XAUUSD (Gold) market and provide a detailed trading strategy based on the Fibonacci OTE (Optimal Trade Entry) strategy.\n\n"
    
    # Current Market Information
    prompt += "### Current Market Information\n"
    prompt += f"- **Market:** XAUUSD (Gold)\n"
    prompt += f"- **Current Price:** ${trend_info.get('current_price', 'Unknown')}\n"
    prompt += f"- **Trend Direction:** {trend_info.get('direction', 'Unknown')} ({trend_info.get('strength', 'Unknown')})\n"
    
    # Add SMA information if available
    if 'sma20' in trend_info:
        prompt += f"- **SMA 20:** ${trend_info['sma20']}\n"
    if 'sma50' in trend_info:
        prompt += f"- **SMA 50:** ${trend_info['sma50']}\n"
    
    # Add structure points
    prompt += "\n### Recent Structure Points\n"
    
    # Add swing highs
    prompt += "**Swing Highs:**\n"
    if structure_points.get('swing_highs'):
        for i, high in enumerate(structure_points['swing_highs'][:3]):  # Only include the most recent 3
            time_str = high['time'].strftime("%Y-%m-%d %H:%M") if hasattr(high['time'], 'strftime') else str(high['time'])
            prompt += f"- High {i+1}: ${high['price']} at {time_str}\n"
    else:
        prompt += "- No significant swing highs identified\n"
    
    # Add swing lows
    prompt += "\n**Swing Lows:**\n"
    if structure_points.get('swing_lows'):
        for i, low in enumerate(structure_points['swing_lows'][:3]):  # Only include the most recent 3
            time_str = low['time'].strftime("%Y-%m-%d %H:%M") if hasattr(low['time'], 'strftime') else str(low['time'])
            prompt += f"- Low {i+1}: ${low['price']} at {time_str}\n"
    else:
        prompt += "- No significant swing lows identified\n"
    
    # Add OTE zone information if available
    if ote_zone:
        prompt += "\n### Pre-calculated Fibonacci Levels\n"
        
        if 'ote_zone' in ote_zone:
            prompt += f"- **OTE Zone:** ${ote_zone['ote_zone'].get('start', 'Unknown')} to ${ote_zone['ote_zone'].get('end', 'Unknown')}\n"
        
        if 'entry_price' in ote_zone:
            prompt += f"- **Suggested Entry Price:** ${ote_zone['entry_price']}\n"
        
        if 'stop_loss' in ote_zone:
            prompt += f"- **Stop Loss:** ${ote_zone['stop_loss']}\n"
        
        if 'take_profit1' in ote_zone:
            prompt += f"- **Take Profit 1:** ${ote_zone['take_profit1']}\n"
        
        if 'take_profit2' in ote_zone:
            prompt += f"- **Take Profit 2:** ${ote_zone['take_profit2']}\n"
    
    # Add strategy rules
    prompt += "\n### Strategy Rules\n"
    prompt += "- In a bullish trend, look for buys at the 0.618-0.786 Fibonacci retracement level of the last significant impulse move\n"
    prompt += "- In a bearish trend, look for sells at the 0.618-0.786 Fibonacci retracement level of the last significant impulse move\n"
    prompt += "- Place stop loss beyond the 0.886 Fibonacci level, typically at the nearest structure point\n"
    prompt += "- First take profit at the 0.618 projection level\n"
    prompt += "- Second take profit at the 1.0 projection level\n"
    
    # Add specific analysis request
    prompt += "\n### Analysis Request\n"
    prompt += "Please provide a detailed analysis with the following:\n"
    prompt += "1. Current market assessment, including trend confirmation and strength\n"
    prompt += "2. Key support and resistance levels based on structure and Fibonacci\n"
    prompt += "3. Specific trade recommendations with entry, stop loss, and take profit levels\n"
    prompt += "4. Risk management advice including position sizing and risk-to-reward ratio\n"
    prompt += "5. Timing considerations for when to execute the trade\n"
    
    # If image is being provided
    prompt += "\nThe chart image shows the recent XAUUSD price action. Please analyze the visual patterns and provide additional insights based on the chart.\n"
    
    return prompt

def generate_strategy_analysis_claude(
    trend_info: Dict[str, Any],
    structure_points: Dict[str, List[Dict[str, Any]]],
    ote_zone: Optional[Dict[str, Any]] = None,
    chart_image_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate detailed trading strategy analysis using Claude 3.7.
    
    Args:
        trend_info: Dictionary with trend direction, strength, current price, and SMAs
        structure_points: Dictionary with swing highs and swing lows
        ote_zone: Optional dictionary with OTE zone calculations
        chart_image_path: Optional path to a chart image for vision analysis
        
    Returns:
        Dictionary with the generated analysis and status information
        
    Raises:
        RuntimeError: If there's an error calling the Anthropic API
    """
    start_time = time.time()
    logger.info("Generating trading strategy analysis with Claude 3.7")
    
    try:
        # Initialize Anthropic client
        client = initialize_anthropic_client()
        
        # Construct the prompt
        prompt = construct_claude_strategy_prompt(trend_info, structure_points, ote_zone)
        
        # Prepare the messages structure
        system_prompt = """You are an expert trading analyst specializing in Fibonacci trading strategies 
        for gold (XAUUSD). You provide precise, detailed analysis with exact price levels and clear reasoning. 
        Focus on concrete, actionable advice based on the Fibonacci OTE strategy, and ensure all calculations are accurate. 
        Format your response with clear headings and sections to make it easy to read and implement."""
        
        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ]
        
        # Set up message content
        if chart_image_path and os.path.exists(chart_image_path):
            # Process the image if provided
            with open(chart_image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Add message with image content
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
            # Text-only prompt
            messages.append({
                "role": "user",
                "content": prompt
            })
        
        # Make the API call with retry logic
        response = None
        retries = 0
        
        while retries <= MAX_RETRIES:
            try:
                response = client.messages.create(
                    model=CLAUDE_MODEL_NAME,
                    max_tokens=2000,
                    temperature=0.2,
                    messages=messages
                )
                break  # Success, exit retry loop
                
            except anthropic.APIError as e:
                retries += 1
                if retries <= MAX_RETRIES:
                    logger.warning(f"Anthropic API error (attempt {retries}/{MAX_RETRIES}): {str(e)}. Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Max retries reached for Anthropic API call: {str(e)}")
                    raise RuntimeError(f"Failed to generate analysis after {MAX_RETRIES} retries: {str(e)}")
                    
            except Exception as e:
                logger.error(f"Unexpected error calling Anthropic API: {str(e)}")
                raise RuntimeError(f"Failed to generate analysis: {str(e)}")
        
        # Process the response
        if response and response.content:
            analysis_text = ""
            for content_block in response.content:
                if content_block.type == "text":
                    analysis_text += content_block.text
            
            elapsed_time = time.time() - start_time
            logger.info(f"Successfully generated Claude analysis in {elapsed_time:.2f} seconds")
            
            return {
                "status": "success",
                "analysis": analysis_text,
                "elapsed_time": elapsed_time,
                "model": CLAUDE_MODEL_NAME
            }
        else:
            logger.error("Empty or invalid response from Anthropic API")
            return {
                "status": "error",
                "analysis": "Failed to generate analysis: Empty response from AI model.",
                "elapsed_time": time.time() - start_time
            }
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Error generating analysis with Claude: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "analysis": f"Failed to generate analysis with Claude: {str(e)}",
            "elapsed_time": elapsed_time
        }