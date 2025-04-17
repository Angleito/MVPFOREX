"""Tests for the Flask web application."""
import pytest
import os
import json
from unittest.mock import patch, MagicMock
from app import create_app
from config.settings import MODELS

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app(serverless=True)
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def mock_market_data():
    """Mock market data for testing."""
    return {
        "data": {
            "candles": [
                {
                    "time": "2025-04-15T10:00:00Z",
                    "o": "2240.50",
                    "h": "2245.75",
                    "l": "2238.25",
                    "c": "2242.80",
                    "volume": "1000"
                }
            ]
        },
        "trend_info": {
            "direction": "Bullish",
            "strength": "Strong",
            "current_price": 2242.80,
            "sma20": 2235.50,
            "sma50": 2230.25
        },
        "structure_points": {
            "swing_highs": [
                {"price": 2245.75, "time": "2025-04-15T10:00:00Z"}
            ],
            "swing_lows": [
                {"price": 2238.25, "time": "2025-04-15T09:45:00Z"}
            ]
        }
    }

def test_index_route(client):
    """Test the index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'XAUUSD Analysis' in response.data

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert data["serverless"] is True

@patch('app.routes.main.get_latest_market_data')
@patch('app.routes.main.get_multi_model_analysis')
def test_analyze_all_models(mock_analysis, mock_market_data_fn, client, mock_market_data):
    """Test the /analyze endpoint for all models."""
    # Mock market data response
    mock_market_data_fn.return_value = mock_market_data
    
    # Mock analysis response
    mock_analysis.return_value = {
        "gpt4": {
            "analysis": "Test GPT-4 analysis",
            "model": "gpt-4-vision",
            "elapsed_time": 2.5
        },
        "claude": {
            "analysis": "Test Claude analysis",
            "model": "claude-3-sonnet",
            "elapsed_time": 2.8
        },
        "perplexity": {
            "analysis": "Test Perplexity analysis",
            "model": "perplexity/sonar",
            "elapsed_time": 2.1
        }
    }
    
    response = client.post('/analyze', json={
        "instrument": "XAU_USD",
        "granularity": "M5",
        "count": 100
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "completed"
    assert "data" in data
    assert all(model in data["data"] for model in ["gpt4", "claude", "perplexity"])

@patch('app.routes.main.get_latest_market_data')
@patch('app.utils.ai_analysis_claude.generate_strategy_analysis_claude')  # Fixed import path
def test_analyze_claude(mock_claude, mock_market_data_fn, client, mock_market_data):
    """Test the /analyze/claude endpoint."""
    # Mock market data response
    mock_market_data_fn.return_value = mock_market_data
    
    # Mock Claude response
    mock_claude.return_value = {
        "status": "success",
        "analysis": "Test Claude analysis",
        "model": "claude-3-sonnet",
        "elapsed_time": 2.8
    }
    
    response = client.post('/analyze/claude', json={
        "instrument": "XAU_USD",
        "granularity": "M5",
        "count": 100
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["analysis"] == "Test Claude analysis"
    assert data["data"]["model"] == "claude-3-sonnet"

@patch('app.routes.main.get_latest_market_data')
@patch('app.utils.ai_analysis_perplexity.generate_strategy_analysis_perplexity')  # Fixed import path
def test_analyze_perplexity(mock_perplexity, mock_market_data_fn, client, mock_market_data):
    """Test the /analyze/perplexity endpoint."""
    # Mock market data response
    mock_market_data_fn.return_value = mock_market_data
    
    # Mock Perplexity response
    mock_perplexity.return_value = {
        "status": "success",
        "analysis": "Test Perplexity analysis",
        "model": "perplexity/sonar",
        "elapsed_time": 2.1
    }
    
    response = client.post('/analyze/perplexity', json={
        "instrument": "XAU_USD",
        "granularity": "M5",
        "count": 100
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["analysis"] == "Test Perplexity analysis"
    assert data["data"]["model"] == "perplexity/sonar"

@patch('app.routes.main.get_latest_market_data')
@patch('app.routes.main.generate_strategy_analysis')
def test_analyze_chatgpt(mock_chatgpt, mock_market_data_fn, client, mock_market_data):
    """Test the /analyze/chatgpt41 endpoint."""
    # Mock market data response
    mock_market_data_fn.return_value = mock_market_data
    
    # Mock ChatGPT response
    mock_chatgpt.return_value = {
        "status": "success",
        "analysis": "Test ChatGPT analysis",
        "model": "gpt-4-vision",
        "elapsed_time": 2.5
    }
    
    response = client.post('/analyze/chatgpt41', json={
        "instrument": "XAU_USD",
        "granularity": "M5",
        "count": 100
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "data" in data
    assert data["data"]["analysis"] == "Test ChatGPT analysis"
    assert data["data"]["model"] == "gpt-4-vision"

def test_invalid_request_validation(client):
    """Test request validation for invalid inputs."""
    # Test missing instrument
    response = client.post('/analyze', json={
        "granularity": "M5"
    })
    assert response.status_code == 400
    assert "No instrument specified" in response.data.decode()
    
    # Test invalid instrument
    response = client.post('/analyze', json={
        "instrument": "INVALID",
        "granularity": "M5"
    })
    assert response.status_code == 400
    assert "Invalid instrument" in response.data.decode()
    
    # Test invalid granularity
    response = client.post('/analyze', json={
        "instrument": "XAU_USD",
        "granularity": "INVALID"
    })
    assert response.status_code == 400
    assert "Invalid granularity" in response.data.decode()
    
    # Test invalid count
    response = client.post('/analyze', json={
        "instrument": "XAU_USD",
        "granularity": "M5",
        "count": "invalid"
    })
    assert response.status_code == 400
    assert "Invalid count value" in response.data.decode()

@patch('app.routes.main.get_latest_market_data')
def test_market_data_error_handling(mock_market_data_fn, client):
    """Test error handling when market data fetch fails."""
    mock_market_data_fn.return_value = {"error": "Failed to fetch market data"}
    
    response = client.post('/analyze', json={
        "instrument": "XAU_USD",
        "granularity": "M5"
    })
    
    assert response.status_code == 500
    data = json.loads(response.data)
    assert data["status"] == "error"
    assert "Failed to fetch market data" in data["error"]

def test_rate_limiting(client):
    """Test rate limiting functionality."""
    # Temporarily disable testing mode to test rate limiting
    client.application.config['TESTING'] = False
    
    try:
        # Make multiple requests quickly
        for i in range(12):  # Exceeding our 10 requests per minute limit
            response = client.post('/analyze', json={
                "instrument": "XAU_USD",
                "granularity": "M5"
            })
            if i >= 10:  # After 10 requests
                assert response.status_code == 429
                data = json.loads(response.data)
                assert data["status"] == "error"
                assert "Rate limit exceeded" in data["error"]
                break
    finally:
        # Re-enable testing mode
        client.application.config['TESTING'] = True

@patch('app.routes.main.get_oanda_client')
@patch('app.routes.main.get_latest_market_data')
def test_get_candles(mock_market_data_fn, mock_oanda_client, client, mock_market_data):
    """Test the /api/candles endpoint."""
    # Mock OANDA client
    mock_oanda_client.return_value = MagicMock()
    
    # Mock market data response
    mock_market_data_fn.return_value = mock_market_data
    
    response = client.post('/api/candles', json={
        "instrument": "XAU_USD",
        "granularity": "H1",
        "count": 100
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "ok"
    assert "candles" in data
    assert len(data["candles"]) > 0
    assert all(key in data["candles"][0] for key in ["timestamp", "open", "high", "low", "close"])

@patch('app.routes.main.get_oanda_client')
def test_get_candles_validation(mock_oanda_client, client):
    """Test validation for the /api/candles endpoint."""
    # Mock OANDA client
    mock_oanda_client.return_value = MagicMock()
    
    # Test missing instrument
    response = client.post('/api/candles', json={
        "granularity": "H1"
    })
    assert response.status_code == 400
    assert "No instrument specified" in response.data.decode()
    
    # Test invalid granularity
    response = client.post('/api/candles', json={
        "instrument": "XAU_USD",
        "granularity": "INVALID"
    })
    assert response.status_code == 400
    assert "Invalid granularity" in response.data.decode()
    
    # Test invalid count
    response = client.post('/api/candles', json={
        "instrument": "XAU_USD",
        "granularity": "H1",
        "count": "invalid"
    })
    assert response.status_code == 400
    assert "Invalid count value" in response.data.decode()
    
    # Test count out of range
    response = client.post('/api/candles', json={
        "instrument": "XAU_USD",
        "granularity": "H1",
        "count": 6000
    })
    assert response.status_code == 400
    assert "Count must be between 1 and 5000" in response.data.decode()