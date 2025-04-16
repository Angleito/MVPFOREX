"""Flask application factory."""
import os
from flask import Flask
from config.settings import DEBUG, SECRET_KEY

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates'),
                static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static'))
    
    # Load configuration
    app.config['DEBUG'] = DEBUG
    app.config['SECRET_KEY'] = SECRET_KEY
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main.bp)
    
    return app