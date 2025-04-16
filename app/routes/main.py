"""Main application routes."""
from flask import Blueprint, render_template, jsonify, request, current_app
from app.utils.ai_client import get_multi_model_analysis
from app.utils.oanda_client import oanda_client
from config.settings import MODELS
import logging
import threading
import uuid
import time
import os
import json
import redis

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# Initialize clients (consider initializing within app context if needed)
# oanda_client = OandaClient()
# ai_client = AIClient()

# --- Vercel KV (Redis) Integration ---
# Remove the in-memory task storage
# task_results = {}

# Initialize Redis client from Vercel KV URL
# Vercel automatically sets KV_URL environment variable when a store is linked
kv_url = os.getenv("KV_URL")
redis_client = None
if kv_url:
    try:
        redis_client = redis.from_url(kv_url)
        # Use current_app.logger within a request context or app setup
        # For now, using print for initialization logging
        print("Successfully connected to Vercel KV (Redis).")
    except Exception as e:
        print(f"Failed to connect to Vercel KV: {e}")
        # Depending on requirements, you might want to raise an error or handle gracefully
else:
    print("WARNING: KV_URL environment variable not set. Vercel KV integration disabled. Task persistence will not work.")
    # Optionally, provide a fallback or mock client for local testing without KV
    # redis_client = None # Or some mock object

# Set a default TTL for keys in seconds (e.g., 15 minutes)
DEFAULT_TTL = 900

# --- Background Task ---
def run_analysis_background(task_id: str, market_data, trend_info, structure_points):
    """Function to run the AI analysis in a background thread and update Redis."""
    # Access Flask app context if needed (e.g., for logging)
    # Requires app context setup if run outside request lifecycle
    logger = current_app.logger if current_app else print # Fallback logger

    if not redis_client:
        logger(f"Redis client not available for task {task_id}. Aborting.")
        return # Cannot proceed without Redis

    logger(f"Background task {task_id} started.")
    try:
        # This still calls the function that currently only runs Claude
        analysis_data = get_multi_model_analysis(
            market_data=market_data,
            trend_info=trend_info,
            structure_points=structure_points
        )
        logger(f"Background task {task_id}: AI analysis completed.")
        # 3. Store completed result in Redis
        result_data = {
            "status": "completed",
            "data": analysis_data
        }
        redis_client.set(task_id, json.dumps(result_data), ex=DEFAULT_TTL)
        logger(f"Task {task_id} completed successfully. Result stored in Redis.")

    except Exception as e:
        logger(f"Error in background task {task_id}: {e}", exc_info=True)
        # Store error status in Redis
        error_data = {
            "status": "error",
            "error": str(e)
        }
        try:
             redis_client.set(task_id, json.dumps(error_data), ex=DEFAULT_TTL)
             logger(f"Task {task_id} failed. Error status stored in Redis.")
        except Exception as redis_err:
             logger(f"Failed to store error status in Redis for task {task_id}: {redis_err}")


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
    if not redis_client:
         # Use current_app.logger here as we are in a request context
         current_app.logger.error("Vercel KV (Redis) client is not configured or connection failed.")
         return jsonify({"error": "Task processing backend (KV) is not configured."}), 503 # Service Unavailable

    task_id = str(uuid.uuid4())
    current_app.logger.info(f"Received analysis request. Generated Task ID: {task_id}")

    # --- Get necessary data (similar to before) ---
    logger.info("Received request to start analysis task.")
    # Fetch live OANDA data
    current_price_data = oanda_client.get_current_price("XAU_USD")
    live_price = None
    if current_price_data and 'prices' in current_price_data and current_price_data['prices']:
        live_price = float(current_price_data['prices'][0]['asks'][0]['price'])
    else: live_price = 2300.00 # Fallback
    logger.info(f"Using live price: {live_price}")

    trend_info = {"direction": "N/A", "strength": "N/A", "current_price": live_price}
    mock_structure_points = {"swing_highs": [], "swing_lows": []} # Keep simple for now
    market_data = {}
    # --- End Data Fetch ---

    # Set initial status in Redis *before* starting thread
    initial_data = {"status": "pending"}
    try:
        redis_client.set(task_id, json.dumps(initial_data), ex=DEFAULT_TTL)
        current_app.logger.info(f"Set initial 'pending' status for task {task_id} in Redis.")
    except Exception as e:
        current_app.logger.error(f"Failed to set initial status in Redis for task {task_id}: {e}")
        return jsonify({"error": "Failed to initialize task status."}), 500

    # Start the background thread
    thread = threading.Thread(
        target=run_analysis_background,
        args=(task_id, market_data, trend_info, mock_structure_points)
    )
    thread.daemon = True  # Allow app to exit even if threads are running
    thread.start()

    return jsonify({"task_id": task_id}), 202 # Accepted

@bp.route('/results/<task_id>', methods=['GET'])
def get_analysis_results(task_id: str):
    """Polls for the results of a previously started analysis task using Redis."""
    if not redis_client:
         current_app.logger.error("Vercel KV (Redis) client is not configured or connection failed during results check.")
         return jsonify({"error": "Task processing backend (KV) is not configured."}), 503

    try:
        result_json = redis_client.get(task_id)
    except Exception as e:
        current_app.logger.error(f"Redis error fetching status for task {task_id}: {e}")
        return jsonify({"error": "Failed to query task status."}), 500

    if result_json:
        try:
            result_data = json.loads(result_json)
            # Optionally refresh TTL if status is still pending? Consider implications.
            # if result_data.get("status") == "pending":
            #    redis_client.expire(task_id, DEFAULT_TTL)
            return jsonify(result_data)
        except json.JSONDecodeError as e:
             current_app.logger.error(f"Failed to decode JSON from Redis for task {task_id}: {e}. Data: {result_json}")
             # Return a server error, but indicate the task might be corrupted
             return jsonify({"status": "error", "error": "Corrupted task data found."}), 500
        except Exception as e:
             current_app.logger.error(f"Unexpected error processing result for task {task_id}: {e}")
             return jsonify({"status": "error", "error": "Failed to process task result."}), 500
    else:
        # Key doesn't exist (either never created, expired, or invalid task_id)
        current_app.logger.warning(f"Task ID {task_id} not found in Redis. It might have expired or is invalid.")
        # Return 404 is appropriate here
        return jsonify({"error": "Task ID not found or expired"}), 404