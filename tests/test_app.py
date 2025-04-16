"""Test the Flask application."""

def test_index_page(client):
    """Test that the index page loads successfully."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'XAUUSD Fibonacci Strategy Advisor' in response.data

def test_app_configuration(app):
    """Test that the application is configured correctly."""
    assert app.testing
    assert not app.debug