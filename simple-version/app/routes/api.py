"""API routes for the application with /api prefix."""
import logging
import json
from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
from app.utils.market_data import get_latest_market_data
from app.utils.ai_analysis import generate_strategy_analysis
from app.utils.ai_analysis_claude import generate_strategy_analysis_claude
from app.utils.ai_analysis_perplexity import generate_strategy_analysis_perplexity
from app.utils.validators import validate_analysis_request, rate_limit

# Configure logging
logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__, url_prefix='/api')

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
            oanda_client = OandaClient()
            logger.info("OandaClient initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OandaClient: {str(e)}", exc_info=True)
            # Return None instead of assigning to global variable
            return None
    return oanda_client

@api_bp.route('/market-data', methods=['GET'])
@cross_origin()
def market_data():
    """Get the latest market data for XAUUSD."""
    try:
        logger.info("API: Fetching latest market data for XAUUSD")
        
        # Initialize OANDA client
        client = get_oanda_client()
        if not client:
            logger.error("OANDA client initialization failed")
            return jsonify({
                "status": "error",
                "error": "Failed to initialize OANDA client"
            }), 500
            
        # Get market data
        instrument = "XAU_USD"
        granularity = "M5"  # 5-minute candles
        count = 50  # Get 50 candles
        
        market_data_result = get_latest_market_data(client, instrument, granularity, count)
        
        if market_data_result.get("error"):
            logger.error(f"Error fetching market data: {market_data_result['error']}")
            return jsonify({
                "status": "error",
                "error": f"Failed to fetch market data: {market_data_result['error']}"
            }), 500
            
        # Properly convert data to JSON serializable format
        import pandas as pd
        import numpy as np
        
        # Function to convert DataFrame to serializable format
        def convert_to_serializable(obj):
            if isinstance(obj, pd.DataFrame):
                return obj.to_dict(orient='records')
            elif isinstance(obj, pd.Series):
                return obj.to_dict()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, (np.int64, np.int32, np.float64, np.float32)):
                return float(obj) if np.issubdtype(obj.dtype, np.floating) else int(obj)
            elif isinstance(obj, dict):
                return {k: convert_to_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_serializable(i) for i in obj]
            else:
                return obj
        
        # Convert data to serializable format
        candles = convert_to_serializable(market_data_result["data"][-10:])  # Last 10 candles
        trend_info = convert_to_serializable(market_data_result["trend_info"])
        structure_points = convert_to_serializable(market_data_result["structure_points"])
        
        # Create response data
        response_data = {
            "status": "ok",
            "candles": candles,
            "trend_info": trend_info,
            "structure_points": structure_points
        }
        
        logger.info("API: Market data fetched successfully")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"An error occurred: {str(e)}"
        }), 500

@api_bp.route('/analyze/openai', methods=['POST'])
@cross_origin()
@rate_limit
def analyze_openai():
    """Generate trading strategy analysis using GPT-4.1."""
    try:
        logger.info("API: Received request for OpenAI analysis")
        
        # Extract data from request
        request_data = request.get_json()
        if not request_data:
            return jsonify({"status": "error", "error": "No data provided"}), 400
            
        market_data = request_data.get('market_data', {})
        if not market_data:
            return jsonify({"status": "error", "error": "No market data provided"}), 400
            
        # Generate analysis using simplified implementation
        logger.info("API: Generating GPT-4.1 analysis using simplified implementation")
        from app.utils.simplified_ai import generate_openai_analysis
        analysis = generate_openai_analysis(market_data)
        
        return jsonify({
            "status": "ok",
            "analysis": analysis
        })
        
    except Exception as e:
        logger.error(f"Error generating OpenAI analysis: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"An error occurred: {str(e)}",
            "analysis": "Failed to generate analysis due to an error."
        }), 500

@api_bp.route('/analyze/anthropic', methods=['POST'])
@cross_origin()
@rate_limit
def analyze_anthropic():
    """Generate trading strategy analysis using Claude 3.7."""
    try:
        logger.info("API: Received request for Anthropic/Claude analysis")
        
        # Extract data from request
        request_data = request.get_json()
        if not request_data:
            return jsonify({"status": "error", "error": "No data provided"}), 400
            
        market_data = request_data.get('market_data', {})
        if not market_data:
            return jsonify({"status": "error", "error": "No market data provided"}), 400
        
        # Generate analysis using simplified implementation
        logger.info("API: Generating Claude 3.7 analysis using simplified implementation")
        from app.utils.simplified_ai import generate_claude_analysis
        analysis = generate_claude_analysis(market_data)
        
        return jsonify({
            "status": "ok",
            "analysis": analysis
        })
        
    except Exception as e:
        logger.error(f"Error generating Claude analysis: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"An error occurred: {str(e)}",
            "analysis": "Failed to generate Claude 3.7 analysis due to an error."
        }), 500

@api_bp.route('/analyze/perplexity', methods=['POST'])
@cross_origin()
@rate_limit
def analyze_perplexity():
    """Generate trading strategy analysis using Perplexity Pro."""
    try:
        logger.info("API: Received request for Perplexity analysis")
        
        # Extract data from request
        request_data = request.get_json()
        if not request_data:
            logger.error("API: No data provided in request for Perplexity analysis")
            return jsonify({"status": "error", "error": "No data provided"}), 400
            
        market_data = request_data.get('market_data', {})
        logger.info(f"API: Received market data for Perplexity analysis: {market_data}")
        
        if not market_data:
            logger.error("API: Empty market_data provided for Perplexity analysis")
            return jsonify({"status": "error", "error": "No market data provided"}), 400
        
        # Generate analysis using simplified implementation
        logger.info("API: Generating Perplexity Pro analysis using simplified implementation")
        
        # Import with more robust error handling
        try:
            from app.utils.simplified_ai import generate_perplexity_analysis
            logger.info("API: Successfully imported generate_perplexity_analysis function")
        except ImportError as ie:
            logger.error(f"API: Failed to import generate_perplexity_analysis: {str(ie)}", exc_info=True)
            return jsonify({"status": "error", "error": f"Import error: {str(ie)}"}), 500
        
        try:
            logger.info("API: Calling generate_perplexity_analysis function")
            analysis = generate_perplexity_analysis(market_data)
            logger.info(f"API: Successfully generated Perplexity analysis ({len(analysis)} chars)")
        except Exception as func_error:
            logger.error(f"API: Error in generate_perplexity_analysis: {str(func_error)}", exc_info=True)
            return jsonify({
                "status": "error", 
                "error": f"Analysis generation error: {str(func_error)}",
                "analysis": "Technical difficulties encountered during analysis generation."
            }), 500
        
        return jsonify({
            "status": "ok",
            "analysis": analysis
        })
        
    except Exception as e:
        logger.error(f"Error generating Perplexity analysis: {str(e)}", exc_info=True)
        
        # More detailed error response with stack trace in development
        error_details = {
            "status": "error",
            "error": f"An error occurred: {str(e)}",
            "analysis": "Failed to generate Perplexity Pro analysis due to an error.",
            "error_type": str(type(e).__name__),
        }
        
        if os.environ.get("FLASK_ENV") == "development":
            import traceback
            error_details["traceback"] = traceback.format_exc()
            
        return jsonify(error_details), 500
