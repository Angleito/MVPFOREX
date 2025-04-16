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
    app.logger.info(f"KV_URL type from env: {type(kv_url)}") # Log type

    if kv_url:
        app.logger.info(f"KV_URL found. Starts with: {kv_url[:10]}...") # Log start of URL
        redis_client_instance = None
        try:
            # Attempt connection setup
            app.logger.info("Attempting redis.from_url(kv_url)...")
            redis_client_instance = redis.from_url(kv_url)
            app.logger.info("redis.from_url call successful.")

            try:
                # Attempt to verify connection with PING
                app.logger.info("Attempting redis_client_instance.ping()...")
                redis_client_instance.ping()
                app.logger.info("Redis ping successful.")
                app.redis_client = redis_client_instance # Attach client to app only after successful ping
                app.logger.info("Successfully connected to Vercel KV (Redis) and attached to app.")

            except redis.exceptions.ConnectionError as ping_err:
                app.logger.error(f"Redis ping() failed after connection setup: {ping_err}")
                app.redis_client = None # Set to None on ping failure
            except Exception as ping_ex:
                 app.logger.error(f"Unexpected error during Redis ping(): {ping_ex}", exc_info=True)
                 app.redis_client = None # Set to None on ping failure

        except redis.exceptions.ConnectionError as conn_err: # Catch errors during from_url
            app.logger.error(f"Vercel KV connection error during redis.from_url (Check KV_URL syntax/network): {conn_err}")
            app.redis_client = None # Set to None on connection failure
        except ValueError as val_err: # Catch URL parsing errors
            app.logger.error(f"Error parsing KV_URL (invalid format?): {val_err}")
            app.redis_client = None
        except Exception as e: # Catch other unexpected errors during setup
            app.logger.error(f"Failed to initialize Vercel KV connection during setup: {e}", exc_info=True)
            app.redis_client = None # Set to None on general failure
    else:
        app.logger.warning("KV_URL environment variable not set or empty. Vercel KV integration disabled.")
        app.redis_client = None # Set to None if URL not found

    # Ensure app.redis_client exists, even if None
    if not hasattr(app, 'redis_client'):
         app.logger.warning("Attribute 'redis_client' was not set, setting to None.")
         app.redis_client = None
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