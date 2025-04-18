"""Request validation utilities for the Flask application."""
from functools import wraps
import time
from typing import Dict, Any, Optional
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

REQUESTS = {}
WINDOW_SIZE = 60  # 1 minute window
MAX_REQUESTS = 10  # 10 requests per minute

def validate_analysis_request(request_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Validate the analysis request data.
    
    Args:
        request_data: The JSON data from the request
        
    Returns:
        None if valid, or dict with error message if invalid
    """
    if not request_data:
        return {"error": "No data provided in request"}
        
    # Validate instrument
    instrument = request_data.get('instrument')
    if not instrument:
        return {"error": "No instrument specified"}
    if instrument != 'XAU_USD':  # Currently only supporting XAUUSD
        return {"error": "Invalid instrument. Only XAU_USD is supported"}
        
    # Validate granularity
    granularity = request_data.get('granularity')
    if not granularity:
        return {"error": "No granularity specified"}
    if granularity not in ['M5', 'M15', 'M30', 'H1', 'H4', 'D']:
        return {"error": "Invalid granularity. Must be one of: M5, M15, M30, H1, H4, D"}
        
    # Optional count validation
    count = request_data.get('count')
    if count is not None:
        try:
            count = int(count)
            if count < 1 or count > 5000:
                return {"error": "Count must be between 1 and 5000"}
        except (ValueError, TypeError):
            return {"error": "Invalid count value"}
            
    return None

def rate_limit(f):
    """Decorator to implement rate limiting."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip rate limiting in testing mode
        if current_app.config.get('TESTING'):
            return f(*args, **kwargs)
            
        # Get client IP
        if request.headers.getlist("X-Forwarded-For"):
            ip = request.headers.getlist("X-Forwarded-For")[0]
        else:
            ip = request.remote_addr
            
        current_time = time.time()
        
        # Initialize or clean up requests for this IP
        if ip not in REQUESTS:
            REQUESTS[ip] = []
        REQUESTS[ip] = [req_time for req_time in REQUESTS[ip] 
                       if current_time - req_time < WINDOW_SIZE]
        
        # Check if rate limit is exceeded
        if len(REQUESTS[ip]) >= MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP: {ip}")
            return jsonify({
                "status": "error",
                "error": "Rate limit exceeded. Please wait before trying again."
            }), 429
            
        # Add current request
        REQUESTS[ip].append(current_time)
        
        return f(*args, **kwargs)
    return decorated_function