"""
Vercel Python Serverless Entrypoint for Flask app.
This file is the main entry point for the Vercel serverless function.
"""
import sys
import logging
import os
import traceback
import json

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure logs go to stdout for Vercel
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting serverless function")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")

# Log installed packages (helpful for debugging)
try:
    import pkg_resources
    installed_packages = sorted([f"{pkg.key}=={pkg.version}" for pkg in pkg_resources.working_set])
    logger.info(f"Installed packages ({len(installed_packages)}): {json.dumps(installed_packages)}")
except Exception as e:
    logger.warning(f"Could not list installed packages: {e}")

try:
    # Add the current directory to the path to resolve potential import issues
    sys.path.insert(0, os.getcwd())
    
    # Try to manually resolve Flask-Cors before importing
    try:
        import flask
        logger.info("Flask imported successfully")
    except ImportError as e:
        logger.critical(f"Failed to import flask: {e}")
        raise

    # Try a direct dynamic import approach for flask_cors
    try:
        # Try both naming conventions
        try:
            flask_cors = __import__('flask_cors')
            logger.info("Successfully imported flask_cors")
        except ImportError:
            flask_cors = __import__('flask-cors')
            logger.info("Successfully imported flask-cors (with hyphen)")
    except ImportError as cors_err:
        # If direct import fails, try to install it on the fly
        logger.error(f"Failed to import flask_cors: {cors_err}")
        
        try:
            # Try to pip install flask-cors on the fly (Vercel allows this in the lambda)
            logger.info("Attempting to install flask-cors on the fly...")
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "flask-cors"], 
                capture_output=True, text=True
            )
            logger.info(f"Pip install result: {result.stdout}")
            logger.info(f"Pip install error: {result.stderr}")
            
            # Try importing again after installation
            flask_cors = __import__('flask_cors')
            logger.info("Successfully imported flask_cors after on-the-fly installation")
        except Exception as pip_err:
            logger.critical(f"Failed to install and import flask_cors: {pip_err}")
            # We'll continue and let the application try to import it later
    
    # Set environment variables for the serverless environment
    os.environ['FLASK_ENV'] = 'production'
    os.environ['SERVERLESS'] = 'true'
    
    # Import the Flask app
    from app import create_app
    
    # Create the Flask app with serverless flag
    app = create_app(serverless=True)
    
    logger.info("Flask app created successfully")
    
    # Log available routes
    routes = [f"{rule.rule} [{','.join(rule.methods)}]" for rule in app.url_map.iter_rules()]
    logger.info(f"Available routes: {routes}")
    
except Exception as e:
    error_traceback = traceback.format_exc()
    logger.error(f"Error initializing app: {str(e)}\n{error_traceback}")
    
    # Create a simple error reporting app if the main app fails
    # This allows us to see the error in the browser instead of just in logs
    try:
        from flask import Flask, jsonify
        error_app = Flask(__name__)
        
        @error_app.route('/', defaults={'path': ''})
        @error_app.route('/<path:path>')
        def catch_all(path):
            return jsonify({
                "error": str(e),
                "traceback": error_traceback.split("\n"),
                "python_version": sys.version,
                "working_directory": os.getcwd()
            }), 500
        
        app = error_app
        logger.info("Created error reporting app")
    except Exception as err_app_error:
        logger.critical(f"Failed to create error app: {err_app_error}")
        raise e  # Re-raise the original error
