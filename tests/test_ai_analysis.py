"""Tests for the OpenAI ChatGPT integration for strategy analysis."""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from app.utils.ai_analysis import (
    initialize_openai_client,
    construct_strategy_prompt,
    generate_strategy_analysis
)

class TestOpenAIIntegration(unittest.TestCase):
    """Test cases for OpenAI ChatGPT integration."""
    
    def setUp(self):
        """Set up test data."""
        # Sample trend info
        self.trend_info = {
            'direction': 'Bullish',
            'strength': 'Strong',
            'current_price': 2345.67,
            'sma20': 2340.25,
            'sma50': 2330.15
        }
        
        # Sample structure points
        self.structure_points = {
            'swing_highs': [
                {'index': 0, 'price': 2350.25, 'time': datetime(2025, 4, 15, 10, 0)},
                {'index': 1, 'price': 2345.50, 'time': datetime(2025, 4, 15, 10, 30)}
            ],
            'swing_lows': [
                {'index': 0, 'price': 2330.75, 'time': datetime(2025, 4, 15, 9, 45)},
                {'index': 1, 'price': 2335.25, 'time': datetime(2025, 4, 15, 10, 15)}
            ]
        }
        
        # Sample OTE zone
        self.ote_zone = {
            'ote_zone': {
                'start': 2340.50,
                'end': 2342.75
            },
            'entry_price': 2341.63,
            'stop_loss': 2330.45,
            'take_profit1': 2352.81,
            'take_profit2': 2360.00
        }
    
    @patch('app.utils.ai_analysis.get_api_key')
    def test_initialize_openai_client(self, mock_get_api_key):
        """Test OpenAI client initialization."""
        # Mock the API key
        mock_get_api_key.return_value = 'test-api-key'
        
        # Mock the OpenAI client
        with patch('app.utils.ai_analysis.OpenAI') as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            
            # Call the function
            client = initialize_openai_client()
            
            # Assertions
            mock_get_api_key.assert_called_once_with('openai')
            mock_openai.assert_called_once_with(api_key='test-api-key')
            self.assertEqual(client, mock_client)
    
    @patch('app.utils.ai_analysis.get_api_key')
    def test_initialize_openai_client_missing_key(self, mock_get_api_key):
        """Test error handling when API key is missing."""
        # Mock missing API key
        mock_get_api_key.return_value = None
        
        # Call the function and expect an error
        with self.assertRaises(ValueError):
            initialize_openai_client()
    
    def test_construct_strategy_prompt(self):
        """Test prompt construction."""
        # Call the function
        prompt = construct_strategy_prompt(self.trend_info, self.structure_points, self.ote_zone)
        
        # Assertions
        self.assertIsInstance(prompt, str)
        self.assertIn('Current Market Information', prompt)
        self.assertIn('Bullish (Strong)', prompt)
        self.assertIn('$2345.67', prompt)
        self.assertIn('Recent Structure Points', prompt)
        self.assertIn('$2350.25', prompt)
        self.assertIn('Pre-calculated Fibonacci Levels', prompt)
        self.assertIn('$2341.63', prompt)
        self.assertIn('Strategy Rules', prompt)
    
    @patch('app.utils.ai_analysis.initialize_openai_client')
    def test_generate_strategy_analysis(self, mock_initialize_client):
        """Test generating strategy analysis."""
        # Mock OpenAI client and response
        mock_client = MagicMock()
        mock_initialize_client.return_value = mock_client
        
        # Mock API response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "XAUUSD Analysis: This is a test analysis response."
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call the function
        result = generate_strategy_analysis(self.trend_info, self.structure_points, self.ote_zone)
        
        # Assertions
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['analysis'], "XAUUSD Analysis: This is a test analysis response.")
        self.assertIn('elapsed_time', result)
        self.assertIn('model', result)
        
        # Verify API was called with correct parameters
        mock_client.chat.completions.create.assert_called_once()
        args, kwargs = mock_client.chat.completions.create.call_args
        self.assertIn('messages', kwargs)
        self.assertIn('temperature', kwargs)
        self.assertIn('max_tokens', kwargs)
        self.assertEqual(kwargs['temperature'], 0.2)
        self.assertEqual(kwargs['max_tokens'], 2000)
    
    @patch('app.utils.ai_analysis.initialize_openai_client')
    def test_generate_strategy_analysis_with_image(self, mock_initialize_client):
        """Test generating strategy analysis with a chart image."""
        # Create a temporary test image file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test image data')
            chart_image_path = temp_file.name
        
        try:
            # Mock OpenAI client and response
            mock_client = MagicMock()
            mock_initialize_client.return_value = mock_client
            
            # Mock API response
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "XAUUSD Analysis with chart: Test response."
            mock_client.chat.completions.create.return_value = mock_response
            
            # Call the function with image path
            result = generate_strategy_analysis(
                self.trend_info,
                self.structure_points,
                self.ote_zone,
                chart_image_path=chart_image_path
            )
            
            # Assertions
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['analysis'], "XAUUSD Analysis with chart: Test response.")
            
            # Verify API was called with image content
            args, kwargs = mock_client.chat.completions.create.call_args
            self.assertIn('messages', kwargs)
            messages = kwargs['messages']
            self.assertEqual(len(messages), 2)  # System message and user message
            
            # Check if the user message has content with both text and image
            user_message = messages[1]
            if isinstance(user_message.get('content', []), list):
                content_items = user_message['content']
                self.assertGreaterEqual(len(content_items), 2)  # At least text and image items
                content_types = [item.get('type') for item in content_items if 'type' in item]
                self.assertIn('text', content_types)
                self.assertIn('image_url', content_types)
            
        finally:
            # Clean up the temporary file
            if os.path.exists(chart_image_path):
                os.remove(chart_image_path)
    
    @patch('app.utils.ai_analysis.initialize_openai_client')
    def test_generate_strategy_analysis_api_error(self, mock_initialize_client):
        """Test error handling for API failures."""
        # Mock OpenAI client that raises an exception
        mock_client = MagicMock()
        mock_initialize_client.return_value = mock_client
        
        # Mock API error
        mock_client.chat.completions.create.side_effect = Exception("API connection error")
        
        # Call the function
        result = generate_strategy_analysis(self.trend_info, self.structure_points)
        
        # Assertions
        self.assertEqual(result['status'], 'error')
        self.assertIn('Failed to generate analysis', result['analysis'])
        self.assertIn('API connection error', result['analysis'])
        self.assertIn('elapsed_time', result)
    
    @patch('app.utils.ai_analysis.initialize_openai_client')
    def test_generate_strategy_analysis_empty_response(self, mock_initialize_client):
        """Test handling of empty API response."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_initialize_client.return_value = mock_client
        
        # Mock empty API response
        mock_response = MagicMock()
        mock_response.choices = []
        mock_client.chat.completions.create.return_value = mock_response
        
        # Call the function
        result = generate_strategy_analysis(self.trend_info, self.structure_points)
        
        # Assertions
        self.assertEqual(result['status'], 'error')
        self.assertIn('Empty response', result['analysis'])
        self.assertIn('elapsed_time', result)

if __name__ == '__main__':
    unittest.main()