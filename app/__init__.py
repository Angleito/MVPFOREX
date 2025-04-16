"""Flask application factory."""
import os
import json
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from config.settings import DEBUG, SECRET_KEY

# Load environment variables early
load_dotenv()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))
    
    CORS(app)  # Enable CORS for all routes
    
    # Load configuration
    app.config['DEBUG'] = DEBUG
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # Configure logging FIRST so subsequent logs work
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    app.logger.setLevel(logging.INFO)
    app.logger.info('Flask app created. Initializing components...')

    # --- Log all available environment variables ---
    app.logger.info("--- START VERCEL ENVIRONMENT VARIABLES ---")
    try:
        # Use json.dumps for potentially cleaner multiline output in logs
        env_vars_dict = dict(os.environ)
        # Redact sensitive values before logging if necessary, e.g., KV_URL password
        # For now, let's just log keys to be safer, or the full dict if you're comfortable in dev logs
        # app.logger.info(json.dumps(list(env_vars_dict.keys()), indent=2, sort_keys=True)) # Option 1: Log only keys
        app.logger.info(json.dumps(env_vars_dict, indent=2, sort_keys=True)) # Option 2: Log full dict (check sensitivity)
    except Exception as e:
        app.logger.error(f"Failed to serialize os.environ: {e}") # Fallback if serialization fails
        app.logger.info(str(os.environ)) # Log raw string representation as fallback
    app.logger.info("--- END VERCEL ENVIRONMENT VARIABLES ---")
    # --- End Log Environment Variables ---

    # --- Initialize Vercel KV (Redis) ---
    redis_url_env_var_name = "KV_REDIS_URL" # Define the var name we are looking for
    kv_url = os.getenv(redis_url_env_var_name)
    app.logger.info(f"{redis_url_env_var_name} type from env: {type(kv_url)}") # Log type using the variable name

    if kv_url:
        app.logger.info(f"{redis_url_env_var_name} found. Starts with: {kv_url[:10]}...") # Log start of URL
        redis_client_instance = None
        try:
            # Attempt connection setup
            app.logger.info(f"Attempting redis.from_url({redis_url_env_var_name})...")
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
            app.logger.error(f"Vercel KV connection error during redis.from_url (Check {redis_url_env_var_name} syntax/network): {conn_err}")
            app.redis_client = None # Set to None on connection failure
        except ValueError as val_err: # Catch URL parsing errors
            app.logger.error(f"Error parsing {redis_url_env_var_name} (invalid format?): {val_err}")
            app.redis_client = None
        except Exception as e: # Catch other unexpected errors during setup
            app.logger.error(f"Failed to initialize Vercel KV connection during setup: {e}", exc_info=True)
            app.redis_client = None # Set to None on general failure
    else:
        app.logger.warning(f"{redis_url_env_var_name} environment variable not set or empty. Vercel KV integration disabled.")
        app.redis_client = None # Set to None if URL not found


    # Register blueprints
    try:
        from app.routes import main
        app.logger.info("Successfully imported app.routes.main.")
        app.logger.info(f"Blueprint object: {main.bp}")
        app.register_blueprint(main.bp, url_prefix="/api")
        app.logger.info("Registered main blueprint at /api.")
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        app.logger.error(f"Error registering blueprints: {e}\nTraceback:\n{tb_str}", exc_info=True)
        print(f"Error registering blueprints: {e}\nTraceback:\n{tb_str}")

    app.logger.info("Flask application instance creation complete.")
    return app