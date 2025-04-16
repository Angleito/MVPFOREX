"""Test configuration and fixtures."""
import os
import pytest
from app import create_app

@pytest.fixture(autouse=True)
def mock_env_vars():
    """Set up mock environment variables for testing."""
    os.environ['OANDA_API_KEY'] = 'test_oanda_key'
    os.environ['OANDA_ACCOUNT_ID'] = 'test_account_id'
    os.environ['OPENAI_API_KEY'] = 'test_openai_key'
    os.environ['ANTHROPIC_API_KEY'] = 'test_anthropic_key'
    os.environ['FLASK_SECRET_KEY'] = 'test_secret_key'
    yield
    # Clean up environment variables after tests
    for key in ['OANDA_API_KEY', 'OANDA_ACCOUNT_ID', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'FLASK_SECRET_KEY']:
        os.environ.pop(key, None)

@pytest.fixture
def app():
    """Create and configure a test Flask application instance."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'DEBUG': False
    })
    return app

@pytest.fixture
def client(app):
    """Create a test client for the Flask application."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test CLI runner for the Flask application."""
    return app.test_cli_runner()