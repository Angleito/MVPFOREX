"""Test module for Perplexity Vision analysis functionality."""
import os
import pytest
from unittest.mock import patch, MagicMock
from app.utils.ai_analysis_perplexity import (
    get_api_key,
    initialize_perplexity_client,
    construct_perplexity_strategy_prompt,
    generate_strategy_analysis_perplexity,
    encode_image_to_base64
)

# Test data
MOCK_TREND_INFO = {
    'direction': 'Bullish',
    'strength': 'Strong',
    'current_price': 2250.45,
    'sma20': 2240.15,
    'sma50': 2225.80
}

MOCK_STRUCTURE_POINTS = {
    'swing_highs': [
        {'price': 2260.75, 'time': '2025-04-14 10:30'},
        {'price': 2255.30, 'time': '2025-04-14 12:45'},
        {'price': 2252.80, 'time': '2025-04-15 09:15'}
    ],
    'swing_lows': [
        {'price': 2235.60, 'time': '2025-04-14 11:15'},
        {'price': 2240.25, 'time': '2025-04-15 08:00'},
        {'price': 2242.70, 'time': '2025-04-15 14:30'}
    ]
}

MOCK_OTE_ZONE = {
    'entry_price': 2245.60,
    'stop_loss': 2235.25,
    'take_profit1': 2265.30,
    'take_profit2': 2280.15,
    'ote_zone': {
        'start': 2244.50,
        'end': 2246.75
    }
}

def test_get_api_key():
    """Test retrieving API key from environment variables."""
    with patch.dict(os.environ, {'PERPLEXITY_API_KEY': 'test-key'}):
        assert get_api_key('perplexity') == 'test-key'
    
    with patch.dict(os.environ, {'PERPLEXITY_API_KEY': ''}):
        with patch.dict(os.environ, {'ROUTER_API_KEY': 'router-key'}):
            assert get_api_key('perplexity') == 'router-key'
    
    with patch.dict(os.environ, {'PERPLEXITY_API_KEY': '', 'ROUTER_API_KEY': ''}):
        assert get_api_key('perplexity') is None

def test_initialize_perplexity_client():
    """Test initialization of the Perplexity client."""
    with patch('app.utils.ai_analysis_perplexity.get_api_key', return_value='test-key'):
        with patch('openai.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            client = initialize_perplexity_client()
            assert client == mock_client
            mock_openai.assert_called_once_with(
                api_key='test-key',
                base_url="https://api.perplexity.ai"
            )
    
    with patch('app.utils.ai_analysis_perplexity.get_api_key', return_value=None):
        with pytest.raises(ValueError):
            initialize_perplexity_client()

def test_construct_perplexity_strategy_prompt():
    """Test construction of the prompt for Perplexity."""
    prompt = construct_perplexity_strategy_prompt(MOCK_TREND_INFO, MOCK_STRUCTURE_POINTS, MOCK_OTE_ZONE)
    
    # Check for key components in the prompt
    assert "XAUUSD (Gold)" in prompt
    assert f"Current Price: ${MOCK_TREND_INFO['current_price']}" in prompt
    assert f"Trend Direction: {MOCK_TREND_INFO['direction']}" in prompt
    assert "Swing Highs" in prompt
    assert "Swing Lows" in prompt
    assert "Fibonacci Levels" in prompt
    assert f"Recommended Entry Price: ${MOCK_OTE_ZONE['entry_price']}" in prompt
    assert "Trade recommendation" in prompt

def test_encode_image_to_base64():
    """Test encoding an image to base64."""
    # Create a temporary test image
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_image:
        temp_image.write(b'test image content')
        temp_image_path = temp_image.name
    
    try:
        # Test with a valid file
        encoded = encode_image_to_base64(temp_image_path)
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        
        # Test with a non-existent file
        with pytest.raises(FileNotFoundError):
            encode_image_to_base64("nonexistent_file.jpg")
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_image_path):
            os.unlink(temp_image_path)

def test_generate_strategy_analysis_perplexity():
    """Test generating analysis using Perplexity Vision."""
    # Mock successful response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Test analysis from Perplexity"
    mock_response.choices = [mock_choice]
    
    with patch('app.utils.ai_analysis_perplexity.initialize_perplexity_client') as mock_init_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_init_client.return_value = mock_client
        
        with patch('app.utils.ai_analysis_perplexity.construct_perplexity_strategy_prompt', return_value="Test prompt"):
            result = generate_strategy_analysis_perplexity(MOCK_TREND_INFO, MOCK_STRUCTURE_POINTS, MOCK_OTE_ZONE)
            
            assert result['status'] == 'success'
            assert result['analysis'] == "Test analysis from Perplexity"
            assert 'elapsed_time' in result
            
            # Verify client was called with correct parameters
            mock_client.chat.completions.create.assert_called_once()
            call_args = mock_client.chat.completions.create.call_args[1]
            assert 'model' in call_args
            assert 'temperature' in call_args
            assert 'messages' in call_args

def test_generate_strategy_analysis_perplexity_with_image():
    """Test generating analysis with an image using Perplexity Vision."""
    # Mock successful response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "Test analysis with image from Perplexity"
    mock_response.choices = [mock_choice]
    
    # Create a temporary test image file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_image:
        temp_image.write(b'test image content')
        temp_image_path = temp_image.name
    
    try:
        with patch('app.utils.ai_analysis_perplexity.initialize_perplexity_client') as mock_init_client:
            mock_client = MagicMock()
            mock_client.chat.completions.create.return_value = mock_response
            mock_init_client.return_value = mock_client
            
            with patch('app.utils.ai_analysis_perplexity.construct_perplexity_strategy_prompt', return_value="Test prompt"):
                result = generate_strategy_analysis_perplexity(
                    MOCK_TREND_INFO, 
                    MOCK_STRUCTURE_POINTS, 
                    MOCK_OTE_ZONE,
                    chart_image_path=temp_image_path
                )
                
                assert result['status'] == 'success'
                assert result['analysis'] == "Test analysis with image from Perplexity"
                assert 'elapsed_time' in result
                
                # Verify client was called with correct parameters including image
                mock_client.chat.completions.create.assert_called_once()
                call_args = mock_client.chat.completions.create.call_args[1]
                
                # Check that messages contain image content
                messages = call_args['messages']
                user_message = messages[0]  # Only user message is present
                assert user_message['role'] == 'user'
                assert isinstance(user_message['content'], list)
                assert len(user_message['content']) == 2
                assert user_message['content'][0]['type'] == 'text'
                assert user_message['content'][1]['type'] == 'image_url'
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_image_path):
            os.unlink(temp_image_path)

def test_generate_strategy_analysis_perplexity_error_handling():
    """Test error handling in Perplexity analysis generation."""
    with patch('app.utils.ai_analysis_perplexity.initialize_perplexity_client') as mock_init_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Test error")
        mock_init_client.return_value = mock_client
        
        result = generate_strategy_analysis_perplexity(MOCK_TREND_INFO, MOCK_STRUCTURE_POINTS)
        
        assert result['status'] == 'error'
        assert 'Test error' in result['analysis']
        assert 'elapsed_time' in result

def test_generate_strategy_analysis_perplexity_empty_response():
    """Test handling empty response from Perplexity API."""
    # Mock empty response
    mock_response = MagicMock()
    mock_response.choices = []
    
    with patch('app.utils.ai_analysis_perplexity.initialize_perplexity_client') as mock_init_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_init_client.return_value = mock_client
        
        result = generate_strategy_analysis_perplexity(MOCK_TREND_INFO, MOCK_STRUCTURE_POINTS)
        
        assert result['status'] == 'error'
        assert 'No response received' in result['analysis']
        assert 'elapsed_time' in result