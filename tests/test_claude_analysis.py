"""Test module for Claude 3.7 analysis functionality."""
import os
import pytest
from unittest.mock import patch, MagicMock
from app.utils.ai_analysis_claude import (
    get_api_key,
    initialize_anthropic_client,
    construct_claude_strategy_prompt,
    generate_strategy_analysis_claude
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
    with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
        assert get_api_key('anthropic') == 'test-key'
    
    with patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
        assert get_api_key('anthropic') is None
    
    with patch.dict(os.environ, {'ANTHROPIC_API_KEY': '', 'ANTHROPIC_API_KEY': 'fallback-key'}):
        assert get_api_key('anthropic') == 'fallback-key'

def test_initialize_anthropic_client():
    """Test initialization of the Anthropic client."""
    with patch('app.utils.ai_analysis_claude.get_api_key', return_value='test-key'):
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            client = initialize_anthropic_client()
            assert client == mock_client
            mock_anthropic.assert_called_once_with(api_key='test-key')
    
    with patch('app.utils.ai_analysis_claude.get_api_key', return_value=None):
        with pytest.raises(ValueError):
            initialize_anthropic_client()

def test_construct_claude_strategy_prompt():
    """Test construction of the prompt for Claude."""
    prompt = construct_claude_strategy_prompt(MOCK_TREND_INFO, MOCK_STRUCTURE_POINTS, MOCK_OTE_ZONE)
    
    # Check for key components in the prompt
    assert "XAUUSD (Gold)" in prompt
    assert f"Current Price: ${MOCK_TREND_INFO['current_price']}" in prompt
    assert f"Trend Direction: {MOCK_TREND_INFO['direction']}" in prompt
    assert "Swing Highs:" in prompt
    assert "Swing Lows:" in prompt
    assert "Pre-calculated Fibonacci Levels" in prompt
    assert f"Suggested Entry Price: ${MOCK_OTE_ZONE['entry_price']}" in prompt
    assert "Strategy Rules" in prompt
    assert "Analysis Request" in prompt

def test_generate_strategy_analysis_claude():
    """Test generating analysis using Claude 3.7."""
    # Mock successful response
    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.type = "text"
    mock_content_block.text = "Test analysis"
    mock_response.content = [mock_content_block]
    
    with patch('app.utils.ai_analysis_claude.initialize_anthropic_client') as mock_init_client:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = mock_response
        mock_init_client.return_value = mock_client
        
        with patch('app.utils.ai_analysis_claude.construct_claude_strategy_prompt', return_value="Test prompt"):
            result = generate_strategy_analysis_claude(MOCK_TREND_INFO, MOCK_STRUCTURE_POINTS, MOCK_OTE_ZONE)
            
            assert result['status'] == 'success'
            assert result['analysis'] == "Test analysis"
            assert 'elapsed_time' in result
            
            # Verify client was called with correct parameters
            mock_client.messages.create.assert_called_once()
            call_args = mock_client.messages.create.call_args[1]
            assert 'model' in call_args
            assert 'temperature' in call_args
            assert 'messages' in call_args

def test_generate_strategy_analysis_claude_with_image():
    """Test generating analysis with an image using Claude 3.7."""
    # Mock successful response
    mock_response = MagicMock()
    mock_content_block = MagicMock()
    mock_content_block.type = "text"
    mock_content_block.text = "Test analysis with image"
    mock_response.content = [mock_content_block]
    
    # Create a temporary test image file
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_image:
        temp_image.write(b'test image content')
        temp_image_path = temp_image.name
    
    try:
        with patch('app.utils.ai_analysis_claude.initialize_anthropic_client') as mock_init_client:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_response
            mock_init_client.return_value = mock_client
            
            with patch('app.utils.ai_analysis_claude.construct_claude_strategy_prompt', return_value="Test prompt"):
                result = generate_strategy_analysis_claude(
                    MOCK_TREND_INFO, 
                    MOCK_STRUCTURE_POINTS, 
                    MOCK_OTE_ZONE,
                    chart_image_path=temp_image_path
                )
                
                assert result['status'] == 'success'
                assert result['analysis'] == "Test analysis with image"
                assert 'elapsed_time' in result
                
                # Verify client was called with correct parameters including image
                mock_client.messages.create.assert_called_once()
                call_args = mock_client.messages.create.call_args[1]
                
                # Check that messages contain image content
                messages = call_args['messages']
                user_message = messages[1]  # System is 0, user is 1
                assert user_message['role'] == 'user'
                assert isinstance(user_message['content'], list)
                assert len(user_message['content']) == 2
                assert user_message['content'][0]['type'] == 'text'
                assert user_message['content'][1]['type'] == 'image'
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_image_path):
            os.unlink(temp_image_path)

def test_generate_strategy_analysis_claude_error_handling():
    """Test error handling in Claude analysis generation."""
    with patch('app.utils.ai_analysis_claude.initialize_anthropic_client') as mock_init_client:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("Test error")
        mock_init_client.return_value = mock_client
        
        result = generate_strategy_analysis_claude(MOCK_TREND_INFO, MOCK_STRUCTURE_POINTS)
        
        assert result['status'] == 'error'
        assert 'Test error' in result['analysis']
        assert 'elapsed_time' in result