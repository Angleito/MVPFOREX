"""Main application routes."""
import os
import json
from flask import Blueprint, render_template, jsonify, request, current_app
from dotenv import load_dotenv
import logging

load_dotenv()

from app.utils.ai_client import get_multi_model_analysis
from app.utils.oanda_client import oanda_client
from config.settings import MODELS

logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@bp.route('/analyze', methods=['POST'])
def start_analysis_task():
    """Start the analysis and return results directly for local development."""
    try:
        # Get OANDA data
        current_price_data = oanda_client.get_current_price("XAU_USD")
        live_price = None
        if current_price_data and 'prices' in current_price_data and current_price_data['prices']:
            live_price = float(current_price_data['prices'][0]['asks'][0]['price'])
        else:
            live_price = 2300.00  # Fallback
            logger.warning("Failed to fetch live price from OANDA, using fallback.")
        
        logger.info(f"Using live price: {live_price}")
        
        # Prepare analysis data
        trend_info = {
            "direction": "N/A", 
            "strength": "N/A", 
            "current_price": live_price
        }
        structure_points = {"swing_highs": [], "swing_lows": []}
        market_data = {
            "price": live_price,
            "timestamp": current_price_data['prices'][0]['time'] if current_price_data.get('prices') else None
        }

        # Get analysis from all models
        analysis_results = get_multi_model_analysis(
            market_data=market_data,
            trend_info=trend_info,
            structure_points=structure_points
        )
        
        return jsonify({
            "status": "completed",
            "data": analysis_results
        })

    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@bp.route('/results/<task_id>', methods=['GET'])
def get_analysis_results(task_id: str):
    """Maintain compatibility with the frontend but return not found for local dev."""
    return jsonify({"error": "Task not found"}), 404