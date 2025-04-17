"""End-to-end tests for the MVPFOREX application."""
import pytest
from unittest.mock import patch
import json
import time

def test_complete_analysis_workflow(client, mock_market_data):
    """Test the complete workflow from market data fetching to analysis generation."""
    
    with patch('app.routes.main.get_latest_market_data') as mock_market_data_fn, \
         patch('app.routes.main.get_multi_model_analysis') as mock_analysis:
        
        # Mock the market data response
        mock_market_data_fn.return_value = mock_market_data
        
        # Mock the analysis response
        mock_analysis.return_value = {
            'gpt': {'analysis': 'GPT analysis', 'latency': 1.2},
            'claude': {'analysis': 'Claude analysis', 'latency': 1.1},
            'perplexity': {'analysis': 'Perplexity analysis', 'latency': 0.9}
        }

        # 1. Test health check
        health_response = client.get('/health')
        assert health_response.status_code == 200
        assert json.loads(health_response.data)["status"] == "healthy"

        # 2. Test market data fetching
        start = time.time()
        response = client.get('/market-data')
        end = time.time()
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'candles' in data
        assert end - start < 2.0  # Response time under 2 seconds

        # 3. Test full analysis with all models
        response = client.post('/analyze', json={'timeframe': 'H1'})
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify response structure
        assert 'gpt' in data
        assert 'claude' in data
        assert 'perplexity' in data
        
        # Check analysis content
        for model in ['gpt', 'claude', 'perplexity']:
            assert 'analysis' in data[model]
            assert 'latency' in data[model]
            assert isinstance(data[model]['latency'], (int, float))

        # 4. Test individual model analysis
        for endpoint in ['/analyze/gpt', '/analyze/claude', '/analyze/perplexity']:
            response = client.post(endpoint, json={'timeframe': 'H1'})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'analysis' in data
            assert 'latency' in data

        # 5. Test metrics dashboard data
        response = client.get('/metrics')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verify metrics structure
        assert 'patternRecognition' in data
        assert 'nlpMetrics' in data
        assert 'latency' in data
        assert 'backtest' in data
        assert 'feedback' in data

def test_error_handling(client):
    """Test error handling in the application."""
    
    # Test invalid timeframe
    response = client.post('/analyze', json={'timeframe': 'invalid'})
    assert response.status_code == 400
    
    # Test missing timeframe
    response = client.post('/analyze', json={})
    assert response.status_code == 400
    
    # Test invalid model endpoint
    response = client.post('/analyze/invalid_model')
    assert response.status_code == 404
    
    # Test invalid JSON
    response = client.post('/analyze', data='invalid json')
    assert response.status_code == 400

def test_performance_under_load(client):
    """Test application performance under multiple concurrent requests."""
    import threading
    import queue
    
    results = queue.Queue()
    num_requests = 10
    
    def make_request():
        start = time.time()
        response = client.post('/analyze', json={'timeframe': 'H1'})
        end = time.time()
        results.put({
            'status_code': response.status_code,
            'response_time': end - start
        })
    
    threads = []
    for _ in range(num_requests):
        thread = threading.Thread(target=make_request)
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()
    
    # Analyze results
    response_times = []
    while not results.empty():
        result = results.get()
        assert result['status_code'] == 200
        response_times.append(result['response_time'])
    
    # Check performance metrics
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    
    assert avg_response_time < 5.0  # Average response time under 5 seconds
    assert max_response_time < 10.0  # Max response time under 10 seconds