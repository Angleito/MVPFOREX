"""Main application routes."""
from flask import Blueprint, render_template, jsonify, request
from app.utils.ai_client import get_multi_model_analysis
from app.utils.oanda_client import oanda_client
from config.settings import MODELS
import logging
import threading
import uuid
import time

# Configure logging
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

# In-memory storage for task results (simple approach, limitations apply)
# Structure: { 'task_id': {'status': 'pending'/'completed'/'error', 'result': data or None, 'error': msg or None} }
task_results = {}

def run_analysis_background(task_id: str, market_data, trend_info, structure_points):
    """Function to run the AI analysis in a background thread."""
    try:
        logger.info(f"Background task {task_id}: Starting AI analysis.")
        # This still calls the function that currently only runs Claude
        analysis_data = get_multi_model_analysis(
            market_data=market_data,
            trend_info=trend_info,
            structure_points=structure_points
        )
        logger.info(f"Background task {task_id}: AI analysis completed.")
        task_results[task_id] = {'status': 'completed', 'result': analysis_data}
    except Exception as e:
        logger.error(f"Background task {task_id}: Error during analysis: {str(e)}", exc_info=True)
        task_results[task_id] = {'status': 'error', 'error': str(e)}


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
    try:
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

        task_id = str(uuid.uuid4())
        task_results[task_id] = {'status': 'pending'} # Store initial status

        logger.info(f"Starting background thread for task_id: {task_id}")
        thread = threading.Thread(
            target=run_analysis_background,
            args=(task_id, market_data, trend_info, mock_structure_points)
        )
        thread.daemon = True # Allows app to exit even if threads are running (less critical here)
        thread.start()

        # Immediately return the task ID
        return jsonify({'task_id': task_id, 'status': 'started'}), 202 # 202 Accepted status

    except Exception as e:
        logger.error(f"Error starting analysis task: {str(e)}", exc_info=True)
        return jsonify({'error': f'Failed to start analysis: {str(e)}'}), 500


@bp.route('/results/<task_id>', methods=['GET'])
def get_analysis_results(task_id: str):
    """Polls for the results of a previously started analysis task."""
    logger.debug(f"Received request for results of task_id: {task_id}")
    if task_id not in task_results:
        logger.warning(f"Task ID {task_id} not found.")
        return jsonify({'status': 'error', 'error': 'Task ID not found'}), 404

    task_info = task_results.get(task_id)

    if task_info['status'] == 'completed':
        logger.info(f"Task {task_id} completed. Returning results.")
        # Optionally remove completed task from memory after retrieval?
        # del task_results[task_id]
        return jsonify({'status': 'completed', 'data': task_info['result']})
    elif task_info['status'] == 'pending':
        logger.debug(f"Task {task_id} is still pending.")
        return jsonify({'status': 'pending'})
    elif task_info['status'] == 'error':
        logger.error(f"Task {task_id} failed. Returning error.")
        # Optionally remove failed task from memory?
        # del task_results[task_id]
        return jsonify({'status': 'error', 'error': task_info.get('error', 'Unknown error')}), 500
    else:
        # Should not happen
        logger.error(f"Task {task_id} has unknown status: {task_info.get('status')}")
        return jsonify({'status': 'error', 'error': 'Unknown task status'}), 500