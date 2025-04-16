"""AI client utilities for Requesty integration."""
import base64
from typing import Optional
import openai
from config.settings import (
    ROUTER_API_KEY,
    REQUESTY_BASE_URL,
    MODELS,
    DEFAULT_MODEL,
    MAX_TOKENS,
    TEMPERATURE
)

def get_ai_client():
    """Initialize and return an OpenAI client configured for Requesty."""
    if not ROUTER_API_KEY:
        raise ValueError("ROUTER_API_KEY not found. Please check your .env file.")

    # Initialize OpenAI client with Requesty configuration
    client = openai.OpenAI(
        api_key=ROUTER_API_KEY,
        base_url=REQUESTY_BASE_URL,
        default_headers={
            "Authorization": f"Bearer {ROUTER_API_KEY}"
        }
    )
    return client

def encode_image(image_path: str) -> str:
    """Convert an image to base64 encoding."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def generate_analysis(
    market_data,
    trend_info,
    structure_points,
    chart_image_path: Optional[str] = None,
    model_type: str = 'gpt4'
):
    """Generate trading analysis using the specified vision model through Requesty.
    
    Args:
        market_data: Dictionary containing market data
        trend_info: Dictionary containing trend information
        structure_points: Dictionary containing structure points
        chart_image_path: Optional path to the chart image for analysis
        model_type: Type of model to use ('gpt4', 'claude', or 'perplexity')
    """
    client = get_ai_client()
    model_config = MODELS.get(model_type, MODELS['gpt4'])
    
    # Prepare the messages
    messages = [
        {
            "role": "system",
            "content": "You are an expert trading analyst specializing in Fibonacci trading strategies for gold (XAUUSD)."
        }
    ]

    # Prepare the content with market data
    content = [
        {
            "type": "text",
            "text": f"""
                Analyze the following XAUUSD market data:
                Current Price: ${trend_info['current_price']}
                Trend Direction: {trend_info['direction']}
                Trend Strength: {trend_info['strength']}
                
                Recent Structure Points:
                Swing Highs: {[f'${h["price"]} at {h["time"]}' for h in structure_points['swing_highs']]}
                Swing Lows: {[f'${l["price"]} at {l["time"]}' for l in structure_points['swing_lows']]}
                
                Please provide:
                1. Technical Analysis of the chart
                2. Fibonacci retracement levels and key zones
                3. Potential trade setup with entry, stop loss, and take profit levels
                4. Risk management recommendations
            """
        }
    ]

    # Add image analysis if chart is provided
    if chart_image_path:
        try:
            base64_image = encode_image(chart_image_path)
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            })
        except Exception as e:
            raise Exception(f"Error processing chart image: {str(e)}")

    messages.append({"role": "user", "content": content})
    
    try:
        response = client.chat.completions.create(
            model=model_config['id'],
            messages=messages,
            max_tokens=model_config['max_tokens'],
            temperature=model_config['temperature']
        )
        
        if not response.choices:
            raise Exception("No response choices found")
        
        return response.choices[0].message.content
        
    except openai.OpenAIError as e:
        raise Exception(f"AI Analysis Error: {str(e)}")

def get_multi_model_analysis(
    market_data,
    trend_info,
    structure_points,
    chart_image_path: Optional[str] = None
):
    """Generate analysis from all three models and return combined results."""
    results = {}
    
    for model_type in MODELS.keys():
        try:
            analysis = generate_analysis(
                market_data,
                trend_info,
                structure_points,
                chart_image_path,
                model_type
            )
            results[model_type] = {
                'analysis': analysis,
                'model': MODELS[model_type]['id']
            }
        except Exception as e:
            results[model_type] = {
                'error': str(e),
                'model': MODELS[model_type]['id']
            }
    
    return results