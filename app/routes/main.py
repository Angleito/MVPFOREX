"""Main application routes."""
import os
import uuid
import logging
import time
from flask import Blueprint, render_template, jsonify, request, current_app
from dotenv import load_dotenv
from app.utils.ai_client import get_multi_model_analysis
from app.utils.market_data import get_latest_market_data
from app.utils.ai_analysis import generate_strategy_analysis
from app.utils.market_analysis import calculate_ote_zone

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)

# Initialize OandaClient lazily to prevent issues in serverless environments
oanda_client = None

def get_oanda_client():
    """Lazily initialize the OandaClient only when needed."""
    global oanda_client
    if oanda_client is None:
        try:
            # Only import when needed to reduce cold start time
            from app.utils.oanda_client import OandaClient
            logger.info("Initializing OandaClient...")
            start_time = time.time()
            oanda_client = OandaClient()
            logger.info(f"OandaClient initialized successfully in {time.time() - start_time:.2f}s")
        except Exception as e:
            logger.error(f"Failed to initialize OandaClient: {str(e)}", exc_info=True)
            # Return None instead of assigning to global variable
            return None
    return oanda_client

# --- Routes ---
from config.settings import MODELS

@bp.route('/test-candles')
def test_candles():
    """Test endpoint to verify Supabase/Postgres candlestick DB integration."""
    from app.db import SessionLocal
    from app.utils.candles_db import get_candles_from_db
    session = SessionLocal()
    try:
        from datetime import datetime, timedelta
        end = datetime.utcnow()
        start = end - timedelta(minutes=5*5)  # 5 candles of M5
        candles = get_candles_from_db(session, 'XAU_USD', 'M5', start, end)
        data = [
            {
                'instrument': c.instrument,
                'granularity': c.granularity,
                'timestamp': c.timestamp.isoformat(),
                'open': c.open,
                'high': c.high,
                'low': c.low,
                'close': c.close,
                'volume': c.volume
            }
            for c in candles[-5:]
        ]
        return jsonify({'status': 'ok', 'candles': data})
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e)}), 500
    finally:
        session.close()

@bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html', MODELS=MODELS)


from app.utils.ai_client import generate_analysis

@bp.route('/analyze', methods=['POST'])
def analyze():
    """Fetch data and run analysis for all models or a specific model based on request."""
    logger.info("Received request for /analyze endpoint")
    client = get_oanda_client()
    if not client:
        logger.error("OANDA client initialization failed. Cannot proceed with analysis.")
        return jsonify({"status": "error", "error": "OANDA client initialization failed."}), 500
    try:
        # Parse request body
        req_json = request.get_json(force=True, silent=True) or {}
        model = req_json.get('model')
        instrument = req_json.get('instrument', "XAU_USD")
        granularity = req_json.get('granularity', "H1")
        count = req_json.get('count', 100)
        chart_image_path = req_json.get('chart_image_path')

        # Fetch market data
        market_data_result = get_latest_market_data(client, instrument, granularity, count)
        if market_data_result.get("error"):
            logger.error(f"Error fetching market data: {market_data_result['error']}")
            return jsonify({"status": "error", "error": f"Failed to fetch market data: {market_data_result['error']}"}), 500
        market_data = market_data_result["data"]
        trend_info = market_data_result["trend_info"]
        structure_points = market_data_result["structure_points"]
        logger.info("Market data fetched successfully.")

        # If a specific model is requested
        if model:
            logger.info(f"Running analysis for model: {model}")
            from app.utils.ai_client import analyze_single_model
            try:
                result = analyze_single_model(
                    model=model,
                    market_data=market_data,
                    trend_info=trend_info,
                    structure_points=structure_points,
                    chart_image_path=chart_image_path
                )
                return jsonify({"status": "ok", "result": result})
            except Exception as e:
                logger.error(f"Error analyzing with model {model}: {str(e)}", exc_info=True)
                return jsonify({"status": "error", "error": f"Failed to analyze with model {model}: {str(e)}"}), 500

        # Otherwise, analyze all models
        logger.info("Starting AI analysis for all models")
        from app.utils.ai_client import get_multi_model_analysis
        analysis_results = get_multi_model_analysis(
            market_data=market_data,
            trend_info=trend_info,
            structure_points=structure_points
        )
        return jsonify({"status": "completed", "data": analysis_results})
    except Exception as e:
        error_message = str(e)
        logger.error(f"An unexpected error occurred during analysis: {error_message}", exc_info=True)
        return jsonify({
            "status": "error", 
            "error": f"An internal server error occurred: {error_message}",
            "error_type": type(e).__name__
        }), 500

# Per-model endpoints for direct LLM analysis
@bp.route('/analyze/gpt4', methods=['POST'])
def analyze_gpt4():
    return _analyze_single_model('gpt4')

@bp.route('/analyze/claude', methods=['POST'])
def analyze_claude():
    """Generate trading strategy analysis using Claude 3.7 Vision API."""
    logger.info("Received request for /analyze/claude")

    # Lazily initialize the OANDA client
    client = get_oanda_client()
    if not client:
        logger.error("OANDA client initialization failed. Cannot proceed with analysis.")
        return jsonify({"status": "error", "error": "OANDA client initialization failed."}), 500

    try:
        # 1. Fetch Market Data
        logger.info("Fetching latest market data...")
        instrument = request.json.get('instrument', 'XAU_USD')
        granularity = request.json.get('granularity', 'M5')
        count = request.json.get('count', 100)
        
        market_data_result = get_latest_market_data(client, instrument, granularity, count)
        
        if market_data_result.get("error"):
            logger.error(f"Error fetching market data: {market_data_result['error']}")
            return jsonify({"status": "error", "error": f"Failed to fetch market data: {market_data_result['error']}"}), 500
        
        market_data = market_data_result["data"]
        trend_info = market_data_result["trend_info"]
        structure_points = market_data_result["structure_points"]
        logger.info("Market data fetched successfully.")
        
        # 2. Calculate OTE zone based on trend and structure points
        ote_zone = None
        if trend_info.get('direction') in ['Bullish', 'Bearish'] and structure_points.get('swing_highs') and structure_points.get('swing_lows'):
            try:
                ote_zone = calculate_ote_zone(trend_info['direction'], structure_points)
                logger.info(f"OTE zone calculated: {ote_zone.get('entry_price')}")
            except Exception as e:
                logger.warning(f"Could not calculate OTE zone: {str(e)}")
        
        # 3. Get chart image path if provided
        chart_image_path = request.json.get('chart_image_path')
        if chart_image_path and not os.path.exists(chart_image_path):
            logger.warning(f"Chart image not found at path: {chart_image_path}")
            chart_image_path = None
        
        # 4. Generate strategy analysis using Claude 3.7
        logger.info("Generating strategy analysis with Claude 3.7...")
        from app.utils.ai_analysis_claude import generate_strategy_analysis_claude
        
        analysis_result = generate_strategy_analysis_claude(
            trend_info=trend_info,
            structure_points=structure_points,
            ote_zone=ote_zone,
            chart_image_path=chart_image_path
        )
        
        # 5. Prepare and return response
        if analysis_result.get('status') == 'success':
            logger.info(f"Strategy analysis generated successfully in {analysis_result.get('elapsed_time', 0):.2f}s")
            return jsonify({
                "status": "success",
                "data": {
                    "trend_info": trend_info,
                    "structure_points": structure_points,
                    "ote_zone": ote_zone,
                    "analysis": analysis_result.get('analysis'),
                    "model": analysis_result.get('model'),
                    "elapsed_time": analysis_result.get('elapsed_time')
                }
            })
        else:
            logger.error(f"Error generating Claude analysis: {analysis_result.get('analysis')}")
            return jsonify({
                "status": "error",
                "error": analysis_result.get('analysis', "Unknown error generating Claude analysis")
            }), 500
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"An unexpected error occurred during Claude analysis: {error_message}", exc_info=True)
        
        return jsonify({
            "status": "error", 
            "error": f"An internal server error occurred: {error_message}",
            "error_type": type(e).__name__
        }), 500

@bp.route('/analyze/perplexity', methods=['POST'])
def analyze_perplexity():
    """Generate trading strategy analysis using Perplexity Vision API."""
    logger.info("Received request for /analyze/perplexity")

    # Lazily initialize the OANDA client
    client = get_oanda_client()
    if not client:
        logger.error("OANDA client initialization failed. Cannot proceed with analysis.")
        return jsonify({"status": "error", "error": "OANDA client initialization failed."}), 500

    try:
        # 1. Fetch Market Data
        logger.info("Fetching latest market data...")
        instrument = request.json.get('instrument', 'XAU_USD')
        granularity = request.json.get('granularity', 'M5')
        count = request.json.get('count', 100)
        
        market_data_result = get_latest_market_data(client, instrument, granularity, count)
        
        if market_data_result.get("error"):
            logger.error(f"Error fetching market data: {market_data_result['error']}")
            return jsonify({"status": "error", "error": f"Failed to fetch market data: {market_data_result['error']}"}), 500
        
        market_data = market_data_result["data"]
        trend_info = market_data_result["trend_info"]
        structure_points = market_data_result["structure_points"]
        logger.info("Market data fetched successfully.")
        
        # 2. Calculate OTE zone based on trend and structure points
        ote_zone = None
        if trend_info.get('direction') in ['Bullish', 'Bearish'] and structure_points.get('swing_highs') and structure_points.get('swing_lows'):
            try:
                ote_zone = calculate_ote_zone(trend_info['direction'], structure_points)
                logger.info(f"OTE zone calculated: {ote_zone.get('entry_price')}")
            except Exception as e:
                logger.warning(f"Could not calculate OTE zone: {str(e)}")
        
        # 3. Get chart image path if provided
        chart_image_path = request.json.get('chart_image_path')
        if chart_image_path and not os.path.exists(chart_image_path):
            logger.warning(f"Chart image not found at path: {chart_image_path}")
            chart_image_path = None
        
        # 4. Generate strategy analysis using Perplexity Vision
        logger.info("Generating strategy analysis with Perplexity Vision...")
        from app.utils.ai_analysis_perplexity import generate_strategy_analysis_perplexity
        
        analysis_result = generate_strategy_analysis_perplexity(
            trend_info=trend_info,
            structure_points=structure_points,
            ote_zone=ote_zone,
            chart_image_path=chart_image_path
        )
        
        # 5. Prepare and return response
        if analysis_result.get('status') == 'success':
            logger.info(f"Strategy analysis generated successfully in {analysis_result.get('elapsed_time', 0):.2f}s")
            return jsonify({
                "status": "success",
                "data": {
                    "trend_info": trend_info,
                    "structure_points": structure_points,
                    "ote_zone": ote_zone,
                    "analysis": analysis_result.get('analysis'),
                    "model": analysis_result.get('model'),
                    "elapsed_time": analysis_result.get('elapsed_time')
                }
            })
        else:
            logger.error(f"Error generating Perplexity analysis: {analysis_result.get('analysis')}")
            return jsonify({
                "status": "error",
                "error": analysis_result.get('analysis', "Unknown error generating Perplexity analysis")
            }), 500
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"An unexpected error occurred during Perplexity analysis: {error_message}", exc_info=True)
        
        return jsonify({
            "status": "error", 
            "error": f"An internal server error occurred: {error_message}",
            "error_type": type(e).__name__
        }), 500

def _analyze_single_model(model_type):
    logger.info(f"Received request for /analyze/{model_type}")
    client = get_oanda_client()
    if not client:
        logger.error("OANDA client initialization failed. Cannot proceed with analysis.")
        return jsonify({"status": "error", "error": "OANDA client initialization failed."}), 500
    try:
        instrument = "XAU_USD"
        granularity = "H1"
        count = 100
        market_data_result = get_latest_market_data(client, instrument, granularity, count)
        if market_data_result.get("error"):
            logger.error(f"Error fetching market data: {market_data_result['error']}")
            return jsonify({"status": "error", "error": f"Failed to fetch market data: {market_data_result['error']}"}), 500
        market_data = market_data_result["data"]
        trend_info = market_data_result["trend_info"]
        structure_points = market_data_result["structure_points"]
        logger.info(f"Market data fetched successfully for {model_type}.")
        logger.info(f"Starting AI analysis for model: {model_type}")
        analysis_result = generate_analysis(
            market_data=market_data,
            trend_info=trend_info,
            structure_points=structure_points,
            model_type=model_type
        )
        return jsonify({"status": "completed", "data": analysis_result})
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error during analysis for {model_type}: {error_message}", exc_info=True)
        return jsonify({
            "status": "error", 
            "error": f"An internal server error occurred: {error_message}",
            "error_type": type(e).__name__
        }), 500

@bp.route('/analyze/chatgpt41', methods=['POST'])
def analyze_chatgpt41():
    """Generate trading strategy analysis using ChatGPT 4.1 Vision API."""
    logger.info("Received request for /analyze/chatgpt41")

    # Lazily initialize the OANDA client
    client = get_oanda_client()
    if not client:
        logger.error("OANDA client initialization failed. Cannot proceed with analysis.")
        return jsonify({"status": "error", "error": "OANDA client initialization failed."}), 500

    try:
        # 1. Fetch Market Data
        logger.info("Fetching latest market data...")
        instrument = request.json.get('instrument', 'XAU_USD')
        granularity = request.json.get('granularity', 'M5')
        count = request.json.get('count', 100)
        
        market_data_result = get_latest_market_data(client, instrument, granularity, count)
        
        if market_data_result.get("error"):
            logger.error(f"Error fetching market data: {market_data_result['error']}")
            return jsonify({"status": "error", "error": f"Failed to fetch market data: {market_data_result['error']}"}), 500
        
        market_data = market_data_result["data"]
        trend_info = market_data_result["trend_info"]
        structure_points = market_data_result["structure_points"]
        logger.info("Market data fetched successfully.")
        
        # 2. Calculate OTE zone based on trend and structure points
        ote_zone = None
        if trend_info.get('direction') in ['Bullish', 'Bearish'] and structure_points.get('swing_highs') and structure_points.get('swing_lows'):
            try:
                ote_zone = calculate_ote_zone(trend_info['direction'], structure_points)
                logger.info(f"OTE zone calculated: {ote_zone.get('entry_price')}")
            except Exception as e:
                logger.warning(f"Could not calculate OTE zone: {str(e)}")
        
        # 3. Get chart image path if provided
        chart_image_path = request.json.get('chart_image_path')
        if chart_image_path and not os.path.exists(chart_image_path):
            logger.warning(f"Chart image not found at path: {chart_image_path}")
            chart_image_path = None
        
        # 4. Generate strategy analysis using ChatGPT 4.1
        logger.info("Generating strategy analysis with ChatGPT 4.1...")
        analysis_result = generate_strategy_analysis(
            trend_info=trend_info,
            structure_points=structure_points,
            ote_zone=ote_zone,
            chart_image_path=chart_image_path
        )
        
        # 5. Prepare and return response
        if analysis_result.get('status') == 'success':
            logger.info(f"Strategy analysis generated successfully in {analysis_result.get('elapsed_time', 0):.2f}s")
            return jsonify({
                "status": "success",
                "data": {
                    "trend_info": trend_info,
                    "structure_points": structure_points,
                    "ote_zone": ote_zone,
                    "analysis": analysis_result.get('analysis'),
                    "model": analysis_result.get('model'),
                    "elapsed_time": analysis_result.get('elapsed_time')
                }
            })
        else:
            logger.error(f"Error generating analysis: {analysis_result.get('analysis')}")
            return jsonify({
                "status": "error",
                "error": analysis_result.get('analysis', "Unknown error generating analysis")
            }), 500
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"An unexpected error occurred during ChatGPT analysis: {error_message}", exc_info=True)
        
        return jsonify({
            "status": "error", 
            "error": f"An internal server error occurred: {error_message}",
            "error_type": type(e).__name__
        }), 500

@bp.route('/upload-chart', methods=['POST'])
def upload_chart():
    """Upload a chart image for analysis.
    
    Expects a file with the key 'chart' in the request.
    Returns a JSON object with the path to the uploaded image.
    """
    logger.info("Received chart image upload request")
    
    if 'chart' not in request.files:
        logger.error("No chart file in request")
        return jsonify({
            "status": "error",
            "error": "No chart file uploaded"
        }), 400
    
    chart_file = request.files['chart']
    
    if chart_file.filename == '':
        logger.error("Empty chart filename")
        return jsonify({
            "status": "error",
            "error": "No chart file selected"
        }), 400
    
    # Check if the file is an allowed image type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not ('.' in chart_file.filename and chart_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
        logger.error(f"Invalid chart file type: {chart_file.filename}")
        return jsonify({
            "status": "error",
            "error": "Invalid file type. Allowed types: png, jpg, jpeg, gif"
        }), 400
    
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uploads')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        
        # Generate a unique filename with timestamp
        filename = f"{int(time.time())}_{uuid.uuid4().hex}.{chart_file.filename.rsplit('.', 1)[1].lower()}"
        filepath = os.path.join(upload_dir, filename)
        
        # Save the file
        chart_file.save(filepath)
        logger.info(f"Chart image saved to {filepath}")
        
        return jsonify({
            "status": "success",
            "chart_image_path": filepath
        })
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing chart upload: {error_message}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Error processing chart upload: {error_message}"
        }), 500

@bp.route('/api/info', methods=['GET'])
def api_info():
    """Get information about the API, including available models and versions.
    
    Returns a JSON object with information about the API, including:
    - API version
    - Available models
    - Model capabilities
    - Server information
    """
    logger.info("Request for API information")
    
    import platform
    import sys
    
    try:
        api_info = {
            "api_version": "1.0.0",
            "name": "MVPFOREX API",
            "description": "AI Trading Strategy Advisors for XAUUSD (Gold)",
            "models": {
                model_name: {
                    "id": model_info['id'],
                    "max_tokens": model_info['max_tokens'],
                    "temperature": model_info['temperature'],
                    "capabilities": [
                        "text_analysis",
                        "chart_vision" if model_name in ['gpt4', 'claude', 'perplexity'] else None,
                        "fibonacci_strategies"
                    ],
                    "endpoint": f"/analyze/{model_name}"
                }
                for model_name, model_info in MODELS.items()
            },
            "global_endpoint": "/analyze",
            "allowed_instruments": ["XAU_USD"],
            "server_info": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "timestamp": time.time()
            }
        }
        
        # Remove any None values from capabilities
        for model_name in api_info["models"]:
            api_info["models"][model_name]["capabilities"] = [
                cap for cap in api_info["models"][model_name]["capabilities"] if cap is not None
            ]
        
        return jsonify(api_info)
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error generating API info: {error_message}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Error generating API info: {error_message}"
        }), 500

@bp.route('/api/docs', methods=['GET'])
def api_docs():
    """Return API documentation in JSON format.
    
    This provides detailed documentation for all available endpoints,
    including parameters, request methods, and response formats.
    """
    logger.info("Request for API documentation")
    
    try:
        docs = {
            "name": "MVPFOREX API Documentation",
            "version": "1.0.0",
            "base_url": request.url_root.rstrip('/'),
            "endpoints": [
                {
                    "path": "/",
                    "method": "GET",
                    "description": "Render the main web interface",
                    "response_format": "HTML page",
                    "authentication_required": False
                },
                {
                    "path": "/api/info",
                    "method": "GET",
                    "description": "Get information about the API, available models, and capabilities",
                    "response_format": "JSON object with API details",
                    "authentication_required": False
                },
                {
                    "path": "/api/docs",
                    "method": "GET",
                    "description": "Get API documentation",
                    "response_format": "JSON object with endpoint documentation",
                    "authentication_required": False
                },
                {
                    "path": "/upload-chart",
                    "method": "POST",
                    "description": "Upload a chart image for analysis",
                    "parameters": {
                        "chart": {
                            "type": "file",
                            "description": "The chart image file (PNG, JPG, JPEG, or GIF)"
                        }
                    },
                    "response_format": "JSON object with the path to the uploaded image",
                    "authentication_required": False
                },
                {
                    "path": "/analyze",
                    "method": "POST",
                    "description": "Generate trading strategy analysis from all configured models",
                    "parameters": {
                        "instrument": {
                            "type": "string",
                            "description": "Trading instrument (default: XAU_USD)",
                            "optional": True
                        },
                        "granularity": {
                            "type": "string",
                            "description": "Timeframe granularity (default: M5)",
                            "optional": True
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of candles to fetch (default: 100)",
                            "optional": True
                        },
                        "chart_image_path": {
                            "type": "string",
                            "description": "Path to chart image (from upload-chart endpoint)",
                            "optional": True
                        }
                    },
                    "response_format": "JSON object with analysis from all models",
                    "authentication_required": False
                },
                {
                    "path": "/analyze/{model}",
                    "method": "POST",
                    "description": "Generate trading strategy analysis from a specific model (gpt4, claude, perplexity, chatgpt41)",
                    "parameters": {
                        "instrument": {
                            "type": "string",
                            "description": "Trading instrument (default: XAU_USD)",
                            "optional": True
                        },
                        "granularity": {
                            "type": "string",
                            "description": "Timeframe granularity (default: M5)",
                            "optional": True
                        },
                        "count": {
                            "type": "integer",
                            "description": "Number of candles to fetch (default: 100)",
                            "optional": True
                        },
                        "chart_image_path": {
                            "type": "string",
                            "description": "Path to chart image (from upload-chart endpoint)",
                            "optional": True
                        }
                    },
                    "response_format": "JSON object with analysis from the specified model",
                    "authentication_required": False
                },
                {
                    "path": "/health",
                    "method": "GET",
                    "description": "Health check endpoint to verify application is running",
                    "response_format": "JSON object with status information",
                    "authentication_required": False
                }
            ],
            "response_format": {
                "success": {
                    "status": "success",
                    "data": {
                        "description": "The data object contains the results of the operation",
                        "properties": {
                            "trend_info": "Object containing trend direction, strength, and price information",
                            "structure_points": "Object containing swing highs and lows",
                            "ote_zone": "Object containing Fibonacci OTE zone information (if available)",
                            "analysis": "String containing the analysis text from the model",
                            "model": "String identifying the model used for analysis",
                            "elapsed_time": "Time in seconds to generate the analysis"
                        }
                    }
                },
                "error": {
                    "status": "error",
                    "error": "String containing error message",
                    "error_type": "String identifying the error type (optional)"
                }
            },
            "models": [model_name for model_name in MODELS.keys()]
        }
        
        return jsonify(docs)
    
    except Exception as e:
        error_message = str(e)
        logger.error(f"Error generating API documentation: {error_message}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"Error generating API documentation: {error_message}"
        }), 500