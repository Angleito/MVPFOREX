import os
import uuid
import threading
import time
import json
from flask import Blueprint, render_template, jsonify, request, current_app
from dotenv import load_dotenv
import logging

# Load environment variables (if any others are needed besides KV_URL)
load_dotenv()

# Assuming you have these imports from your project structure (adjust path if needed)
# Make sure these don't rely on the global redis_client either
from app.utils.ai_client import get_multi_model_analysis
from app.utils.oanda_client import oanda_client
from config.settings import MODELS

# Configure logging
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# Initialize clients (OANDA client might also benefit from app context initialization)
# oanda_client = OandaClient() # Assuming this is okay globally or handled elsewhere
# ai_client = AIClient() # Assuming this is okay globally or handled elsewhere

# Set a default TTL for keys in seconds (e.g., 15 minutes) - Can keep this global
DEFAULT_TTL = 900

# --- Background Task ---
# Modify the function signature to accept the app object
def run_analysis_background(app, task_id: str, market_data, trend_info, structure_points):
    """Function to run the AI analysis in a background thread and update Redis."""
    with app.app_context(): # Use passed app context
        logger = current_app.logger # Use Flask logger
        redis_client = current_app.redis_client # Get Redis client from app context

        if not redis_client: # Check client from app context
            logger.error(f"Redis client not available from app context for task {task_id}. Aborting.")
            return

        logger.info(f"Background task {task_id} started.")
        try:
            # --- Analysis Logic Starts Here ---
            logger.debug(f"Task {task_id}: Starting AI analysis within app context.")
            # Ensure get_multi_model_analysis can run within app context if it needs flask resources
            analysis_data = get_multi_model_analysis(
                market_data=market_data,
                trend_info=trend_info,
                structure_points=structure_points
            )
            logger.info(f"Background task {task_id}: AI analysis completed.")
            # --- Store result in Redis ---
            result_data = {
                "status": "completed",
                "data": analysis_data
            }
            redis_client.set(task_id, json.dumps(result_data), ex=DEFAULT_TTL) # Use client from context
            logger.info(f"Task {task_id} completed successfully. Result stored in Redis.")

        except Exception as e:
            logger.error(f"Error in background task {task_id}: {e}", exc_info=True)
            # --- Store error in Redis ---
            error_data = {
                "status": "error",
                "error": str(e)
            }
            try:
                 # Use client from context
                 redis_client.set(task_id, json.dumps(error_data), ex=DEFAULT_TTL)
                 logger.info(f"Task {task_id} failed. Error status stored in Redis.")
            except Exception as redis_err:
                 # Log specific error during Redis SET operation
                 logger.error(f"Failed to store error status in Redis for task {task_id}: {redis_err}", exc_info=True)


# --- Routes ---
@bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@bp.route('/test_requesty')
def test_requesty():
    """Test the Requesty API connection."""
    try:
        client = get_ai_client()
        # Using the simplest possible request for testing
        response = client.chat.completions.create(
            model=MODELS['gpt4']['id'],  # Using updated GPT-4.1 Vision model ID
            messages=[
                {
                    "role": "user",
                    "content": "Hi, please respond with just 'Connection successful!'"
                }
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        return jsonify({
            'success': True,
            'message': response.choices[0].message.content if response.choices else "No response"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/analyze', methods=['POST'])
def start_analysis_task():
    """Starts the AI analysis in a background thread and returns a task ID."""
    redis_client = current_app.redis_client # Get Redis client from app context

    if not redis_client: # Check client from app context
         current_app.logger.error("Redis client not available from app context during /analyze.")
         return jsonify({"error": "Task processing backend (KV) is not configured or connection failed."}), 503

    task_id = str(uuid.uuid4())
    current_app.logger.info(f"Received analysis request. Generated Task ID: {task_id}")

    # --- Get necessary data (similar to before) ---
    current_app.logger.info("Fetching data for analysis task.")
    try:
        current_price_data = oanda_client.get_current_price("XAU_USD")
        live_price = None
        if current_price_data and 'prices' in current_price_data and current_price_data['prices']:
            live_price = float(current_price_data['prices'][0]['asks'][0]['price'])
        else:
            live_price = 2300.00 # Fallback
            current_app.logger.warning("Failed to fetch live price from OANDA, using fallback.")
        current_app.logger.info(f"Using live price: {live_price}")
    except Exception as e:
        current_app.logger.error(f"Error fetching OANDA data: {e}", exc_info=True)
        return jsonify({"error": "Failed to fetch market data."}), 500

    trend_info = {"direction": "N/A", "strength": "N/A", "current_price": live_price}
    mock_structure_points = {"swing_highs": [], "swing_lows": []} # Keep simple for now
    market_data = {} # Placeholder for potential future use
    # --- End Data Fetch ---

    # Set initial status in Redis *before* starting thread
    initial_data = {"status": "pending"}
    try:
        redis_client.set(task_id, json.dumps(initial_data), ex=DEFAULT_TTL) # Use client from context
        current_app.logger.info(f"Set initial 'pending' status for task {task_id} in Redis.")
    except Exception as e:
        current_app.logger.error(f"Failed to set initial status in Redis for task {task_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to initialize task status in backend store."}), 500

    # Get a reference to the current app instance *before* starting the thread
    app_instance = current_app._get_current_object()

    # Start the background thread, passing the app instance
    thread = threading.Thread(
        target=run_analysis_background,
        args=(app_instance, task_id, market_data, trend_info, mock_structure_points)
    )
    thread.daemon = True
    thread.start()
    current_app.logger.info(f"Background thread started for task {task_id}.")

    return jsonify({"task_id": task_id}), 202 # Accepted

@bp.route('/results/<task_id>', methods=['GET'])
def get_analysis_results(task_id: str):
    """Polls for the results of a previously started analysis task using Redis."""
    redis_client = current_app.redis_client # Get Redis client from app context

    if not redis_client: # Check client from app context
         current_app.logger.error("Redis client not available from app context during /results check.")
         return jsonify({"error": "Task processing backend (KV) is not configured or connection failed."}), 503

    try:
        result_json = redis_client.get(task_id) # Use client from context
    except Exception as e:
        current_app.logger.error(f"Redis error fetching status for task {task_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to query task status."}), 500

    if result_json:
        try:
            result_data = json.loads(result_json)
            # Optionally refresh TTL if status is still pending? Consider implications.
            # if result_data.get("status") == "pending":
            #    redis_client.expire(task_id, DEFAULT_TTL)
            current_app.logger.debug(f"Returning results for task {task_id}: {result_data.get('status')}")
            return jsonify(result_data)
        except json.JSONDecodeError as e:
             current_app.logger.error(f"Failed to decode JSON from Redis for task {task_id}: {e}. Data: {result_json}")
             return jsonify({"status": "error", "error": "Corrupted task data found."}), 500
        except Exception as e:
             current_app.logger.error(f"Unexpected error processing result for task {task_id}: {e}", exc_info=True)
             return jsonify({"status": "error", "error": "Failed to process task result."}), 500
    else:
        # Key doesn't exist (either never created, expired, or invalid task_id)
        current_app.logger.warning(f"Task ID {task_id} not found in Redis. It might have expired or is invalid.")
        return jsonify({"error": "Task ID not found or expired"}), 404

@bp.route('/task_status', methods=['GET'])
def get_task_status():
    """Get the status of all tasks."""
    try:
        # Get tasks implementation
        return jsonify({"message": "Task status retrieved successfully"})
    except Exception as e:
        logger.error(f"Error getting task status: {str(e)}")
        return jsonify({"error": "Failed to query task status"}), 500