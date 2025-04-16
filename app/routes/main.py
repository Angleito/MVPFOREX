"""Main application routes."""
import os
import uuid
import logging
from flask import Blueprint, render_template, jsonify, request, current_app
from dotenv import load_dotenv
from app.utils.oanda_client import OandaClient
from app.utils.ai_client import get_multi_model_analysis
from app.utils.market_data import get_latest_market_data

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)

# Initialize OandaClient globally or within application context if preferred
try:
    oanda_client = OandaClient()
except Exception as e:
    logger.error(f"Failed to initialize OandaClient: {e}", exc_info=True)
    oanda_client = None # Ensure it exists but indicates failure

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


@bp.route('/analyze', methods=['POST'])
def analyze():
    """Fetch data, run analysis for a single model, and return result."""
    logger.info("Received request for /analyze (single model)")

    if not oanda_client:
        logger.error("OANDA client not initialized. Cannot proceed with analysis.")
        return jsonify({"status": "error", "error": "OANDA client initialization failed."}), 500

    # Accept model param from query string or JSON
    model_type = (request.args.get('model') or request.json.get('model') if request.is_json else None)
    if not model_type:
        logger.error("No model parameter provided in request.")
        return jsonify({"status": "error", "error": "No model specified."}), 400

    from config.settings import MODELS
    if model_type not in MODELS:
        logger.error(f"Requested model '{model_type}' not in MODELS config.")
        return jsonify({"status": "error", "error": f"Model '{model_type}' not supported."}), 400

    try:
        # 1. Fetch Market Data
        logger.info("Fetching latest market data...")
        instrument = "EUR_USD"
        granularity = "H1"
        count = 100
        market_data_result = get_latest_market_data(oanda_client, instrument, granularity, count)
        
        if market_data_result.get("error"):
            logger.error(f"Error fetching market data: {market_data_result['error']}")
            return jsonify({"status": "error", "error": f"Failed to fetch market data: {market_data_result['error']}"}), 500
        
        market_data = market_data_result["data"]
        trend_info = market_data_result["trend_info"]
        structure_points = market_data_result["structure_points"]
        logger.info("Market data fetched successfully.")
        
        # 2. Run AI Analysis for the selected model
        logger.info(f"Starting AI analysis for model: {model_type}")
        from app.utils.ai_client import generate_analysis
        try:
            analysis = generate_analysis(market_data, trend_info, structure_points, None, model_type)
            result = {
                'analysis': analysis,
                'model': MODELS[model_type]['id']
            }
            logger.info(f"AI analysis for model '{model_type}' completed successfully.")
            return jsonify({"status": "completed", "data": {model_type: result}})
        except Exception as e:
            logger.error(f"Error generating analysis for {model_type}: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "error": str(e)}), 500

    except Exception as e:
        logger.error(f"An unexpected error occurred during analysis: {e}", exc_info=True)
        return jsonify({"status": "error", "error": f"An internal server error occurred: {str(e)}"}), 500