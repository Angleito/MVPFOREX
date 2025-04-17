"""Security tests for the MVPFOREX application."""
import pytest
import jwt
import json
from datetime import datetime, timedelta
from unittest.mock import patch

def test_api_key_protection(client):
    """Test that API keys are properly protected."""
    
    # Test that API keys are not exposed in responses
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_data(as_text=True)
    
    sensitive_keys = [
        'OANDA_API_KEY',
        'OPENAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'PERPLEXITY_API_KEY',
        'FLASK_SECRET_KEY'
    ]
    
    for key in sensitive_keys:
        assert key not in data
        # Test that even the test values are not exposed
        assert f'test_{key.lower()}' not in data

def test_request_validation(client):
    """Test input validation and sanitization."""
    
    # Test SQL injection prevention
    malicious_inputs = [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "); DELETE FROM users; --"
    ]
    
    for bad_input in malicious_inputs:
        response = client.post('/analyze', json={
            'timeframe': bad_input
        })
        assert response.status_code in [400, 422]  # Either bad request or unprocessable entity

    # Test XSS prevention
    xss_payloads = [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        '<img src="x" onerror="alert(\'xss\')">'
    ]
    
    for payload in xss_payloads:
        response = client.post('/analyze', json={
            'timeframe': payload
        })
        assert response.status_code in [400, 422]
        
        # Check that the payload is not reflected in the response
        assert payload not in response.get_data(as_text=True)

def test_rate_limiting(client):
    """Test that rate limiting is working."""
    
    # Make rapid requests to trigger rate limiting
    responses = []
    for _ in range(50):  # Adjust number based on your rate limit
        responses.append(client.post('/analyze', json={'timeframe': 'H1'}))
    
    # Verify that some requests were rate limited
    assert any(r.status_code == 429 for r in responses)

@patch('app.routes.main.verify_api_key')
def test_api_authentication(mock_verify, client):
    """Test API authentication and authorization."""
    
    # Test without API key
    response = client.post('/analyze')
    assert response.status_code == 401
    
    # Test with invalid API key
    response = client.post('/analyze', headers={'X-API-Key': 'invalid_key'})
    assert response.status_code == 401
    
    # Test with valid API key
    mock_verify.return_value = True
    response = client.post('/analyze', 
                          headers={'X-API-Key': 'valid_key'},
                          json={'timeframe': 'H1'})
    assert response.status_code == 200

def test_content_security_policy(client):
    """Test Content Security Policy headers."""
    
    response = client.get('/')
    headers = response.headers
    
    # Verify CSP headers are present
    assert 'Content-Security-Policy' in headers
    csp = headers['Content-Security-Policy']
    
    # Check essential CSP directives
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp
    
    # Test that inline scripts are blocked
    assert "'unsafe-inline'" not in csp

def test_secure_headers(client):
    """Test security-related HTTP headers."""
    
    response = client.get('/')
    headers = response.headers
    
    # Check security headers
    assert headers.get('X-Content-Type-Options') == 'nosniff'
    assert headers.get('X-Frame-Options') == 'DENY'
    assert headers.get('X-XSS-Protection') == '1; mode=block'
    assert 'Strict-Transport-Security' in headers
    
    # Verify that sensitive headers are not exposed
    assert 'Server' not in headers
    assert 'X-Powered-By' not in headers