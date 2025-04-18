import os

"""AI client utilities for Requesty integration."""
import base64
import logging
import time
from typing import Optional
import openai
import json
ROUTER_API_KEY = os.environ.get('ROUTER_API_KEY')
REQUESTY_BASE_URL = os.environ.get('REQUESTY_BASE_URL')
MODELS = json.loads(os.environ.get('MODELS', '{}'))
DEFAULT_MODEL = os.environ.get('DEFAULT_MODEL', 'gpt4')
MAX_TOKENS = os.environ.get('MAX_TOKENS', '2000')
TEMPERATURE = os.environ.get('TEMPERATURE', '0.7')

logger = logging.getLogger(__name__)

def get_ai_client():
    """Initialize and return an OpenAI client configured for Requesty."""
    if not ROUTER_API_KEY:
        logger.error("ROUTER_API_KEY not found in environment variables")
        raise ValueError("ROUTER_API_KEY not found. Please check your environment variables.")

    if not REQUESTY_BASE_URL:
        logger.error("REQUESTY_BASE_URL not found in environment variables")
        raise ValueError("REQUESTY_BASE_URL not found. Please check your environment variables.")

    logger.info(f"Initializing OpenAI client with base URL: {REQUESTY_BASE_URL[:20]}...")

    # Initialize OpenAI client with Requesty configuration
    try:
        client = openai.OpenAI(
            api_key=ROUTER_API_KEY,
            base_url=REQUESTY_BASE_URL,
            default_headers={
                "Authorization": f"Bearer {ROUTER_API_KEY}"
            },
            timeout=60.0  # 60 second timeout for API calls
        )
        return client
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}", exc_info=True)
        raise

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
    """
    Generate trading analysis using the specified vision model (OpenAI, Claude, or Perplexity).
    Uses advanced prompt engineering for each model. Handles image input and robust error handling.
    Returns consistent output format for all models.
    """
    import importlib
    logger.info(f"Generating analysis with model: {model_type}")
    try:
        client = get_ai_client()
        model_config = MODELS.get(model_type, MODELS['gpt4'])
        # Use specialized prompt logic for each model
        if model_type == 'gpt4':
            # Use ai_analysis.py logic for OpenAI
            ai_analysis = importlib.import_module('app.utils.ai_analysis')
            ote_zone = None
            if hasattr(ai_analysis, 'calculate_ote_zone'):
                try:
                    ote_zone = ai_analysis.calculate_ote_zone(trend_info.get('direction', ''), structure_points)
                except Exception:
                    ote_zone = None
            result = ai_analysis.generate_strategy_analysis(
                trend_info,
                structure_points,
                ote_zone=ote_zone,
                chart_image_path=chart_image_path
            )
            # Ensure output is consistent
            if isinstance(result, dict):
                return result
            else:
                return {"status": "success", "analysis": str(result), "model": model_config['id']}
        elif model_type == 'claude':
            # Claude prompt engineering
            prompt = f"""
You are an expert trading analyst specializing in Fibonacci OTE strategies for gold (XAUUSD).
Analyze the following market data and structure points:
Current Price: ${trend_info.get('current_price', 'N/A')}
Trend: {trend_info.get('direction', 'Unknown')} ({trend_info.get('strength', 'Unknown')})
Swing Highs: {[f'${h["price"]} at {h["time"]}' for h in structure_points['swing_highs']]}
Swing Lows: {[f'${l["price"]} at {l["time"]}' for l in structure_points['swing_lows']]}
Please provide:
- Technical analysis
- Fibonacci retracement levels
- Trade setup (entry, stop loss, take profit)
- Risk management advice
"""
            content = [{"type": "text", "text": prompt}]
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
                    logger.error(f"Error processing chart image: {str(e)}", exc_info=True)
                    raise Exception(f"Error processing chart image: {str(e)}")
            messages = [
                {"role": "user", "content": content}
            ]
            start_time = time.time()
            try:
                response = client.chat.completions.create(
                    model=model_config['id'],
                    messages=messages,
                    max_tokens=model_config['max_tokens'],
                    temperature=model_config['temperature']
                )
                elapsed = time.time() - start_time
                if not response.choices:
                    raise Exception("No response choices found")
                return {
                    "status": "success",
                    "analysis": response.choices[0].message.content,
                    "elapsed_time": elapsed,
                    "model": model_config['id']
                }
            except Exception as e:
                logger.error(f"Claude API error: {str(e)}", exc_info=True)
                return {
                    "status": "error",
                    "analysis": f"Claude error: {str(e)}",
                    "model": model_config['id']
                }
        elif model_type == 'perplexity':
            # Perplexity prompt engineering
            prompt = f"""
You are a trading advisor. Analyze XAUUSD market data:
Current Price: ${trend_info.get('current_price', 'N/A')}
Trend: {trend_info.get('direction', 'Unknown')} ({trend_info.get('strength', 'Unknown')})
Swing Highs: {[f'${h["price"]} at {h["time"]}' for h in structure_points['swing_highs']]}
Swing Lows: {[f'${l["price"]} at {l["time"]}' for l in structure_points['swing_lows']]}
Provide:
1. Technical analysis
2. Fibonacci levels
3. Entry/SL/TP
4. Risk management
"""
            content = [{"type": "text", "text": prompt}]
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
                    logger.error(f"Error processing chart image: {str(e)}", exc_info=True)
                    raise Exception(f"Error processing chart image: {str(e)}")
            messages = [
                {"role": "user", "content": content}
            ]
            start_time = time.time()
            try:
                response = client.chat.completions.create(
                    model=model_config['id'],
                    messages=messages,
                    max_tokens=model_config['max_tokens'],
                    temperature=model_config['temperature']
                )
                elapsed = time.time() - start_time
                if not response.choices:
                    raise Exception("No response choices found")
                return {
                    "status": "success",
                    "analysis": response.choices[0].message.content,
                    "elapsed_time": elapsed,
                    "model": model_config['id']
                }
            except Exception as e:
                logger.error(f"Perplexity API error: {str(e)}", exc_info=True)
                return {
                    "status": "error",
                    "analysis": f"Perplexity error: {str(e)}",
                    "model": model_config['id']
                }
        else:
            return {"status": "error", "analysis": f"Unknown model_type: {model_type}", "model": model_type}
    except Exception as e:
        logger.error(f"Error in generate_analysis for {model_type}: {str(e)}", exc_info=True)
        return {"status": "error", "analysis": str(e), "model": model_type}
    """Generate trading analysis using the specified vision model through Requesty.
    
    Args:
        market_data: Dictionary containing market data
        trend_info: Dictionary containing trend information
        structure_points: Dictionary containing structure points
        chart_image_path: Optional path to the chart image for analysis
        model_type: Type of model to use ('gpt4', 'claude', or 'perplexity')
    """
    logger.info(f"Generating analysis with model: {model_type}")
    
    try:
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
                logger.error(f"Error processing chart image: {str(e)}", exc_info=True)
                raise Exception(f"Error processing chart image: {str(e)}")

        messages.append({"role": "user", "content": content})
        
        start_time = time.time()
        logger.info(f"Sending request to {model_config['id']}...")
        
        try:
            response = client.chat.completions.create(
                model=model_config['id'],
                messages=messages,
                max_tokens=model_config['max_tokens'],
                temperature=model_config['temperature']
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"Response received from {model_config['id']} in {elapsed_time:.2f} seconds")
            
            if not response.choices:
                logger.warning(f"No response choices found from {model_config['id']}")
                raise Exception("No response choices found")
            
            return response.choices[0].message.content
            
        except openai.OpenAIError as e:
            logger.error(f"OpenAI API Error with {model_config['id']}: {str(e)}", exc_info=True)
            raise Exception(f"AI Analysis Error with {model_config['id']}: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during API call to {model_config['id']}: {str(e)}", exc_info=True)
            raise Exception(f"Unexpected error during analysis: {str(e)}")
    except Exception as e:
        logger.error(f"Error in generate_analysis for {model_type}: {str(e)}", exc_info=True)
        raise

def get_multi_model_analysis(
    market_data,
    trend_info,
    structure_points,
    chart_image_path: Optional[str] = None
):
    """Generate analysis from all configured models and return results."""
    logger.info("Starting multi-model analysis")
    results = {}
    
    # Run analysis for each model with proper error handling for serverless environments
    for model_type in MODELS.keys():
        logger.info(f"Processing model: {model_type}")
        
        if model_type not in MODELS:  # Safety check
            logger.warning(f"Model type {model_type} not configured")
            results[model_type] = {'error': f'Model type {model_type} not configured', 'model': 'unknown'}
            continue
        
        try:
            # Process one model at a time to prevent timeouts
            if model_type == 'gpt4':
                # Use the OpenAI module
                from app.utils.ai_analysis import generate_strategy_analysis
                
                # Calculate OTE zone
                ote_zone = None
                try:
                    from app.utils.market_analysis import calculate_ote_zone
                    ote_zone = calculate_ote_zone(trend_info.get('direction', ''), structure_points)
                except Exception as e:
                    logger.warning(f"Could not calculate OTE zone: {str(e)}")
                
                analysis = generate_strategy_analysis(
                    trend_info=trend_info,
                    structure_points=structure_points,
                    ote_zone=ote_zone,
                    chart_image_path=chart_image_path
                )
                
            elif model_type == 'claude':
                # Use the Claude module
                from app.utils.ai_analysis_claude import generate_strategy_analysis_claude
                
                # Calculate OTE zone
                ote_zone = None
                try:
                    from app.utils.market_analysis import calculate_ote_zone
                    ote_zone = calculate_ote_zone(trend_info.get('direction', ''), structure_points)
                except Exception as e:
                    logger.warning(f"Could not calculate OTE zone: {str(e)}")
                
                analysis = generate_strategy_analysis_claude(
                    trend_info=trend_info,
                    structure_points=structure_points,
                    ote_zone=ote_zone,
                    chart_image_path=chart_image_path
                )
                
            elif model_type == 'perplexity':
                # Use the Perplexity module
                from app.utils.ai_analysis_perplexity import generate_strategy_analysis_perplexity
                
                # Calculate OTE zone
                ote_zone = None
                try:
                    from app.utils.market_analysis import calculate_ote_zone
                    ote_zone = calculate_ote_zone(trend_info.get('direction', ''), structure_points)
                except Exception as e:
                    logger.warning(f"Could not calculate OTE zone: {str(e)}")
                
                analysis = generate_strategy_analysis_perplexity(
                    trend_info=trend_info,
                    structure_points=structure_points,
                    ote_zone=ote_zone,
                    chart_image_path=chart_image_path
                )
            else:
                # Fallback to generic implementation
                analysis = generate_analysis(
                    market_data=market_data,
                    trend_info=trend_info,
                    structure_points=structure_points,
                    chart_image_path=chart_image_path,
                    model_type=model_type
                )
            
            logger.info(f"Successfully generated analysis for {model_type}")
            
            # Always return a string for 'analysis' (not a dict)
            if isinstance(analysis, dict) and 'analysis' in analysis:
                results[model_type] = {
                    'analysis': analysis['analysis'],
                    'model': MODELS[model_type]['id']
                }
                if 'elapsed_time' in analysis:
                    results[model_type]['elapsed_time'] = analysis['elapsed_time']
                if 'status' in analysis and analysis['status'] != 'success':
                    results[model_type]['error'] = analysis.get('analysis', 'Unknown error')
            else:
                results[model_type] = {
                    'analysis': str(analysis),
                    'model': MODELS[model_type]['id']
                }
        except Exception as e:
            logger.error(f"Error generating analysis for {model_type}: {str(e)}", exc_info=True)
            results[model_type] = {
                'error': str(e),
                'model': MODELS[model_type]['id']
            }
    
    logger.info(f"Completed multi-model analysis. Results for {len(results)} models")
    return results