"""Monitoring utilities for the application."""
import time
import psutil
import threading
from datetime import datetime, timedelta
from collections import deque
from functools import wraps
from flask import request, g

# Store metrics in memory with a fixed size
_request_times = deque(maxlen=1000)
_error_counts = {}
_model_latencies = {
    'gpt': deque(maxlen=100),
    'claude': deque(maxlen=100),
    'perplexity': deque(maxlen=100)
}
_last_errors = deque(maxlen=50)

def track_request_time(f):
    """Decorator to track request processing time."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        response = f(*args, **kwargs)
        duration = time.time() - start_time
        _request_times.append(duration)
        return response
    return decorated_function

def track_model_latency(model_name, latency):
    """Record latency for a specific model."""
    if model_name in _model_latencies:
        _model_latencies[model_name].append(latency)

def log_error(error_type, error_message):
    """Log an error occurrence."""
    _error_counts[error_type] = _error_counts.get(error_type, 0) + 1
    _last_errors.append({
        'type': error_type,
        'message': error_message,
        'timestamp': datetime.utcnow().isoformat()
    })

def get_system_health():
    """Get system health metrics."""
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu_usage': cpu_percent,
        'memory_usage': memory.percent,
        'disk_usage': disk.percent,
        'process_threads': threading.active_count()
    }

def get_application_metrics():
    """Get application performance metrics."""
    now = datetime.utcnow()
    last_minute = now - timedelta(minutes=1)
    last_hour = now - timedelta(hours=1)
    
    # Calculate request statistics
    recent_requests = list(_request_times)
    avg_response_time = sum(recent_requests) / len(recent_requests) if recent_requests else 0
    
    # Calculate model latencies
    model_stats = {}
    for model, latencies in _model_latencies.items():
        if latencies:
            model_stats[model] = {
                'avg_latency': sum(latencies) / len(latencies),
                'max_latency': max(latencies),
                'min_latency': min(latencies)
            }
    
    return {
        'request_metrics': {
            'average_response_time': avg_response_time,
            'requests_per_minute': len([t for t in recent_requests if t > last_minute.timestamp()]),
            'requests_per_hour': len([t for t in recent_requests if t > last_hour.timestamp()]),
            'total_requests': len(recent_requests)
        },
        'error_metrics': {
            'error_counts': dict(_error_counts),
            'recent_errors': list(_last_errors)
        },
        'model_performance': model_stats
    }

def reset_metrics():
    """Reset all metrics (useful for testing)."""
    _request_times.clear()
    _error_counts.clear()
    for model_latencies in _model_latencies.values():
        model_latencies.clear()
    _last_errors.clear()