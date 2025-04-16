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
@bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@bp.route('/analyze', methods=['POST'])
def analyze():
    """Fetch data, run analysis synchronously, and return results."""
    logger.info("Received request for /analyze (synchronous)")

    if not oanda_client:
        logger.error("OANDA client not initialized. Cannot proceed with analysis.")
        return jsonify({"status": "error", "error": "OANDA client initialization failed."}), 500

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
        
        # 2. Run AI Analysis (Directly)
        logger.info("Starting synchronous AI analysis...")
        analysis_results = get_multi_model_analysis(market_data, trend_info, structure_points)
        logger.info("AI analysis completed.")

        # 3. Return Results
        return jsonify({"status": "completed", "data": analysis_results})

    except Exception as e:
        logger.error(f"An unexpected error occurred during analysis: {e}", exc_info=True)
        return jsonify({"status": "error", "error": f"An internal server error occurred: {str(e)}"}), 500