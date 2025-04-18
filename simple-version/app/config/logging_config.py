"""Logging configuration for the application."""
import os
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

def setup_logging(app):
    """Configure logging for the application."""
    # Ensure logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Set up file handler for general logs
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))

    # Set up handler for JSON structured logging
    json_handler = RotatingFileHandler(
        'logs/app.json',
        maxBytes=10485760,
        backupCount=10
    )
    json_handler.setLevel(logging.INFO)

    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'module': record.module,
                'message': record.getMessage(),
                'path': record.pathname,
                'line': record.lineno
            }
            if hasattr(record, 'request_id'):
                log_data['request_id'] = record.request_id
            if hasattr(record, 'latency'):
                log_data['latency'] = record.latency
            return json.dumps(log_data)

    json_handler.setFormatter(JSONFormatter())

    # Add handlers to the application logger
    app.logger.addHandler(file_handler)
    app.logger.addHandler(json_handler)
    app.logger.setLevel(logging.INFO)

    # Remove default Flask handler to avoid duplicate logs
    app.logger.removeHandler(app.logger.handlers[0])

    return app.logger

def log_request(logger, request, latency=None):
    """Log an HTTP request with additional context."""
    log_data = {
        'method': request.method,
        'path': request.path,
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string,
        'latency': latency
    }
    logger.info(f"Request processed: {json.dumps(log_data)}")

def log_error(logger, error, request=None):
    """Log an error with full context."""
    log_data = {
        'error_type': type(error).__name__,
        'error_message': str(error)
    }
    if request:
        log_data.update({
            'method': request.method,
            'path': request.path,
            'ip': request.remote_addr
        })
    logger.error(f"Error occurred: {json.dumps(log_data)}")

def log_model_performance(logger, model_name, latency, success):
    """Log model performance metrics."""
    log_data = {
        'model': model_name,
        'latency': latency,
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    logger.info(f"Model performance: {json.dumps(log_data)}")

def log_security_event(logger, event_type, details, request=None):
    """Log security-related events."""
    log_data = {
        'event_type': event_type,
        'details': details,
        'timestamp': datetime.utcnow().isoformat()
    }
    if request:
        log_data.update({
            'ip': request.remote_addr,
            'user_agent': request.user_agent.string
        })
    logger.warning(f"Security event: {json.dumps(log_data)}")