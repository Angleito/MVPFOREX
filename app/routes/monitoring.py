"""Monitoring routes for the application."""
from flask import Blueprint, jsonify
from app.utils.monitoring import get_system_health, get_application_metrics
from functools import wraps
import os

bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')

def require_admin_key(f):
    """Decorator to check for admin API key."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-Admin-Key')
        if not api_key or api_key != os.environ.get('ADMIN_API_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/health')
@require_admin_key
def health():
    """Get system health metrics."""
    return jsonify(get_system_health())

@bp.route('/metrics')
@require_admin_key
def metrics():
    """Get application performance metrics."""
    return jsonify(get_application_metrics())

@bp.route('/status')
def basic_status():
    """Get basic application status (no authentication required)."""
    return jsonify({
        'status': 'healthy',
        'version': os.environ.get('APP_VERSION', '1.0.0'),
        'environment': os.environ.get('FLASK_ENV', 'production')
    })