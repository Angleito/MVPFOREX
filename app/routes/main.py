"""Main application routes."""
import os
import uuid
import logging
import time
from flask import Blueprint, render_template, jsonify, request, current_app
from dotenv import load_dotenv
from app.utils.ai_client import get_multi_model_analysis
from app.utils.market_data import get_latest_market_data

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


@bp.route('/analyze', methods=['POST'])
def analyze():
    """Fetch data and run analysis for all models."""
    logger.info("Received request for /analyze (all models)")

    # Lazily initialize the OANDA client
    client = get_oanda_client()
    if not client:
        logger.error("OANDA client initialization failed. Cannot proceed with analysis.")
        return jsonify({"status": "error", "error": "OANDA client initialization failed."}), 500

    try:
        # 1. Fetch Market Data
        logger.info("Fetching latest market data...")
        instrument = "XAU_USD"
        granularity = "H1"
        count = 100
        
        try:
            market_data_result = get_latest_market_data(client, instrument, granularity, count)
            
            if market_data_result.get("error"):
                logger.error(f"Error fetching market data: {market_data_result['error']}")
                return jsonify({"status": "error", "error": f"Failed to fetch market data: {market_data_result['error']}"}), 500
            
            market_data = market_data_result["data"]
            trend_info = market_data_result["trend_info"]
            structure_points = market_data_result["structure_points"]
            logger.info("Market data fetched successfully.")
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "error": f"Error fetching market data: {str(e)}"}), 500
        
        # 2. Run AI Analysis for all models
        logger.info("Starting AI analysis for all models")
        
        # Initialize empty results
        analysis_results = {}
        
        # Get model types from settings
        model_types = list(MODELS.keys())
        logger.info(f"Will process {len(model_types)} models: {', '.join(model_types)}")
        
        # Due to serverless timeout constraints, only process one model
        model_type = model_types[0] if model_types else "gpt4"
        logger.info(f"In serverless environment - processing only one model: {model_type}")
        
        try:
            logger.info(f"Starting analysis for model: {model_type}")
            start_time = time.time()
            
            analysis = get_multi_model_analysis(
                market_data=market_data,
                trend_info=trend_info,
                structure_points=structure_points
            )
            
            # Store the results and log performance
            analysis_results = analysis
            logger.info(f"Analysis completed in {time.time() - start_time:.2f}s")
                
        except Exception as e:
            logger.error(f"Error analyzing with model {model_type}: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "error": f"Error analyzing with {model_type}: {str(e)}"}), 500
        
        # Return whatever results we have
        return jsonify({"status": "completed", "data": analysis_results})
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"An unexpected error occurred during analysis: {error_message}", exc_info=True)
        
        # Make sure we return a valid response even in case of errors
        return jsonify({
            "status": "error", 
            "error": f"An internal server error occurred: {error_message}",
            "error_type": type(e).__name__
        }), 500