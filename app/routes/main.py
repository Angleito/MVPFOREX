"""Main application routes."""
import os
import uuid
import threading
import time
import json
from flask import Blueprint, render_template, jsonify, request, current_app
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Imports for analysis and OANDA
from app.utils.ai_client import get_multi_model_analysis
from app.utils.oanda_client import oanda_client
from config.settings import MODELS

# Configure logging
logger = logging.getLogger(__name__)
bp = Blueprint('main', __name__)

# Redis key Time-To-Live (e.g., 15 minutes)
DEFAULT_TTL = 900

# --- Background Task ---
def run_analysis_background(app, task_id: str, market_data, trend_info, structure_points):
    """Function to run the AI analysis in a background thread and update Redis."""
    with app.app_context():
        logger = current_app.logger
        redis_client = current_app.redis_client

        if not redis_client:
            logger.error(f"Redis client not available from app context for task {task_id}. Aborting background task.")
            # Optionally try to store an error state if possible, though unlikely if client is unavailable
            return

        logger.info(f"Background task {task_id} started.")
        try:
            # Perform the actual analysis
            logger.debug(f"Task {task_id}: Starting AI analysis.")
            analysis_data = get_multi_model_analysis(
                market_data=market_data,
                trend_info=trend_info,
                structure_points=structure_points
            )
            logger.info(f"Background task {task_id}: AI analysis completed.")

            # Store successful result in Redis
            result_data = {
                "status": "completed",
                "data": analysis_data # Assuming analysis_data is a dict of results { 'claude': {...}, ... }
            }
            redis_client.set(task_id, json.dumps(result_data), ex=DEFAULT_TTL)
            logger.info(f"Task {task_id} completed successfully. Result stored in Redis.")

        except Exception as e:
            logger.error(f"Error in background task {task_id}: {e}", exc_info=True)
            # Store error status in Redis
            error_data = {
                "status": "error",
                "error": f"Analysis failed: {str(e)}"
            }
            try:
                 redis_client.set(task_id, json.dumps(error_data), ex=DEFAULT_TTL)
                 logger.info(f"Task {task_id} failed. Error status stored in Redis.")
            except Exception as redis_err:
                 logger.error(f"Failed to store error status in Redis for task {task_id}: {redis_err}", exc_info=True)

# --- Routes ---
@bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@bp.route('/analyze', methods=['POST'])
def start_analysis_task():
    """Starts the AI analysis in a background thread and returns a task ID."""
    redis_client = current_app.redis_client
    if not redis_client:
         current_app.logger.error("Redis client not available during /analyze.")
         # Return 503 as the service depends on Redis
         return jsonify({"error": "Task processing backend (KV) is not configured or connection failed."}), 503

    task_id = str(uuid.uuid4())
    current_app.logger.info(f"Received analysis request. Generated Task ID: {task_id}")

    # --- Get necessary data (simplified for now) ---
    try:
        current_price_data = oanda_client.get_current_price("XAU_USD")
        live_price = float(current_price_data['prices'][0]['asks'][0]['price']) if current_price_data.get('prices') else 2300.00
    except Exception as e:
         current_app.logger.error(f"Error fetching OANDA data for task {task_id}: {e}", exc_info=True)
         live_price = 2300.00 # Use fallback on error
         current_app.logger.warning("Using fallback price due to OANDA fetch error.")
    current_app.logger.info(f"Using live price for task {task_id}: {live_price}")

    trend_info = {"direction": "N/A", "strength": "N/A", "current_price": live_price}
    mock_structure_points = {"swing_highs": [], "swing_lows": []}
    market_data = {}
    # --- End Data Fetch ---

    # Set initial "pending" status in Redis
    initial_data = {"status": "pending"}
    try:
        redis_client.set(task_id, json.dumps(initial_data), ex=DEFAULT_TTL)
        current_app.logger.info(f"Set initial 'pending' status for task {task_id} in Redis.")
    except Exception as e:
        current_app.logger.error(f"Failed to set initial status in Redis for task {task_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to initialize task status in backend store."}), 500

    # Start the background thread
    app_instance = current_app._get_current_object() # Get app instance for the thread
    thread = threading.Thread(
        target=run_analysis_background,
        args=(app_instance, task_id, market_data, trend_info, mock_structure_points)
    )
    thread.daemon = True # Allow app to exit even if thread is running
    thread.start()
    current_app.logger.info(f"Background thread started for task {task_id}.")

    # Return 202 Accepted with the task ID
    return jsonify({"task_id": task_id}), 202

@bp.route('/results/<task_id>', methods=['GET'])
def get_analysis_results(task_id: str):
    """Polls for the results of a previously started analysis task using Redis."""
    redis_client = current_app.redis_client
    if not redis_client:
         current_app.logger.error("Redis client not available during /results check.")
         return jsonify({"error": "Task processing backend (KV) is not configured or connection failed."}), 503

    try:
        result_json = redis_client.get(task_id)
    except Exception as e:
        current_app.logger.error(f"Redis error fetching status for task {task_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to query task status."}), 500

    if result_json:
        try:
            result_data = json.loads(result_json)
            current_app.logger.debug(f"Returning results for task {task_id}: status {result_data.get('status')}")
            return jsonify(result_data)
        except json.JSONDecodeError as e:
             current_app.logger.error(f"Failed to decode JSON from Redis for task {task_id}: {e}. Data: {result_json}")
             # Return an error status consistent with the background task failure format
             return jsonify({"status": "error", "error": "Corrupted task data found."}), 500
    else:
        # Task ID not found (expired or invalid)
        current_app.logger.warning(f"Task ID {task_id} not found in Redis.")
        # Return 404 with a specific status for the frontend to handle
        return jsonify({"status": "not_found", "error": "Task ID not found or expired"}), 404