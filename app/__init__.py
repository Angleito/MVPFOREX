"""Flask application factory."""
import os
import redis
import logging
from flask import Flask
from dotenv import load_dotenv
from config.settings import DEBUG, SECRET_KEY

# Load environment variables early
load_dotenv()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))
    
    # Load configuration
    app.config['DEBUG'] = DEBUG
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # Configure logging FIRST so subsequent logs work
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask app created. Initializing components...')

    # --- Initialize Vercel KV (Redis) ---
    kv_url = os.getenv("KV_URL")
    if kv_url:
        try:
            # Attempt connection
            redis_client = redis.from_url(kv_url)
            # Perform a simple check like PING to verify connection
            redis_client.ping()
            app.redis_client = redis_client # Attach client to app
            app.logger.info("Successfully connected to Vercel KV (Redis) and attached to app.")
        except redis.exceptions.ConnectionError as e:
            app.logger.error(f"Vercel KV connection error (Check KV_URL and network): {e}")
            app.redis_client = None # Set to None on failure
        except Exception as e:
            app.logger.error(f"Failed to initialize Vercel KV connection: {e}", exc_info=True)
            app.redis_client = None # Set to None on failure
    else:
        app.logger.warning("KV_URL environment variable not set. Vercel KV integration disabled.")
        app.redis_client = None # Set to None if URL not found
    # --- End Redis Init ---

    # Register blueprints
    try:
        from app.routes import main
        app.register_blueprint(main.bp)
        app.logger.info("Registered main blueprint.")
    except Exception as e:
        app.logger.error(f"Error registering blueprints: {e}", exc_info=True)

    app.logger.info("Flask application instance creation complete.")
    return app