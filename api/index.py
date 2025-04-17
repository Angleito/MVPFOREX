"""
Vercel Python Serverless Entrypoint for Flask app.
This file is the main entry point for the Vercel serverless function.
"""
import sys
import logging
import os

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info("Starting serverless function")
logger.info(f"Python version: {sys.version}")
logger.info(f"Current directory: {os.getcwd()}")

try:
    # Import the Flask app
    from app import create_app
    
    # Create the Flask app
    app = create_app()
    
    logger.info("Flask app created successfully")
    
    # Log available routes
    routes = [f"{rule.rule} [{','.join(rule.methods)}]" for rule in app.url_map.iter_rules()]
    logger.info(f"Available routes: {routes}")
    
except Exception as e:
    logger.error(f"Error initializing app: {str(e)}", exc_info=True)
    # Re-raise to let Vercel know there was an error
    raise
