"""Flask application factory."""
import os
import json
import logging
import sys
from flask import Flask
from flask_cors import CORS
from flask_compress import Compress
from dotenv import load_dotenv
from config.settings import DEBUG, SECRET_KEY

# Load environment variables early
load_dotenv()

def create_app(serverless=False):
    """Create and configure the Flask application.
    
    Args:
        serverless (bool): Flag indicating if app is running in serverless environment
    """
    # Configure logging FIRST for Vercel environment
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout  # Ensure logs go to stdout for Vercel
    )
    logger = logging.getLogger(__name__)
    logger.info('Starting application initialization...')
    
    # Log platform information
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Serverless mode: {serverless}")
    
    try:
        app = Flask(__name__, 
                    template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                    static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))
        
        # Enable CORS
        CORS(app, supports_credentials=True, origins=["*"], methods=["GET", "POST", "OPTIONS", "PATCH", "DELETE", "PUT"], allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-CSRF-Token", "Accept", "Accept-Version", "Content-Length", "Content-MD5", "Date", "X-Api-Version"])
        
        # Enable compression
        Compress(app)
        
        # Load configuration
        app.config['DEBUG'] = DEBUG
        app.config['SECRET_KEY'] = SECRET_KEY
        app.config['SERVERLESS'] = serverless
        app.config['COMPRESS_MIMETYPES'] = [
            'text/html',
            'text/css',
            'text/xml',
            'application/json',
            'application/javascript',
            'application/x-javascript',
        ]
        app.config['COMPRESS_LEVEL'] = 6  # Higher compression level (1-9)
        app.config['COMPRESS_MIN_SIZE'] = 500  # Only compress responses larger than 500 bytes
        
        # Disable caching for API responses in serverless mode
        if serverless:
            @app.after_request
            def add_header(response):
                """Add headers to disable caching."""
                response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
                return response
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Flask app created. Initializing components...')

        # --- Initialize Redis if in non-serverless environment ---
        is_vercel = os.getenv('VERCEL', '0') == '1' or serverless
        if is_vercel:
            logger.info("Running in Vercel/serverless environment - skipping Redis initialization")
            app.redis_client = None
        else:
            # Import Redis only if not in Vercel environment
            try:
                import redis
                redis_url_env_var_name = "KV_REDIS_URL"
                kv_url = os.getenv(redis_url_env_var_name)
                
                if kv_url:
                    logger.info(f"{redis_url_env_var_name} found. Initializing Redis...")
                    try:
                        redis_client_instance = redis.from_url(kv_url)
                        redis_client_instance.ping()
                        app.redis_client = redis_client_instance
                        logger.info("Successfully connected to Redis")
                    except Exception as e:
                        logger.error(f"Redis connection failed: {str(e)}", exc_info=True)
                        app.redis_client = None
                else:
                    logger.warning(f"{redis_url_env_var_name} not set. Redis disabled.")
                    app.redis_client = None
            except ImportError:
                logger.warning("Redis package not available. Redis functionality disabled.")
                app.redis_client = None

        # Register blueprints
        try:
            from app.routes import main
            app.register_blueprint(main.bp)
            logger.info("Registered main blueprint at root level.")
        except Exception as e:
            logger.error(f"Error registering blueprints: {str(e)}", exc_info=True)
            raise
            
        # Add a basic health check endpoint
        @app.route('/health')
        def health_check():
            """Health check endpoint to verify application is running."""
            from flask import jsonify
            return jsonify({"status": "healthy", "serverless": serverless})

        logger.info("Flask application instance creation complete.")
        return app
        
    except Exception as e:
        logger.critical(f"Fatal error during application initialization: {str(e)}", exc_info=True)
        raise