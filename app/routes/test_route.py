"""
Test route for direct API access verification.
"""
import json
import logging
import os
from flask import Blueprint, jsonify, request, current_app

# Configure logging
logger = logging.getLogger(__name__)

# Create blueprint
test_bp = Blueprint('test', __name__)

@test_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping/pong test endpoint for connectivity verification."""
    logger.info("TEST API: Ping received")
    return jsonify({"status": "ok", "message": "pong"})

@test_bp.route('/echo', methods=['POST'])
def echo():
    """Echo endpoint that returns whatever JSON is sent to it."""
    logger.info("TEST API: Echo request received")
    
    try:
        # Get request data
        request_data = request.get_json()
        if not request_data:
            logger.warning("TEST API: No data provided in echo request")
            return jsonify({"status": "error", "error": "No data provided"}), 400
            
        logger.info(f"TEST API: Echo data: {json.dumps(request_data)}")
        
        # Echo back the data with status
        return jsonify({
            "status": "ok",
            "message": "Echo successful",
            "data": request_data
        })
        
    except Exception as e:
        logger.error(f"TEST API: Error in echo endpoint: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "error": f"An error occurred: {str(e)}"
        }), 500
