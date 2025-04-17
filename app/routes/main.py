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
    """Fetch data and run analysis for all models."""
    logger.info("Received request for /analyze (all models)")
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
        logger.info("Market data fetched successfully.")
        logger.info("Starting AI analysis for all models")
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
    return _analyze_single_model('claude')

@bp.route('/analyze/perplexity', methods=['POST'])
def analyze_perplexity():
    return _analyze_single_model('perplexity')

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