"""Test the OANDA data collection module."""
import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
from app.utils.market_data import fetch_oanda_data

class TestOandaDataCollection(unittest.TestCase):
    """Test cases for OANDA data collection module."""

    @patch('app.utils.market_data.API')
    def test_fetch_oanda_data_success(self, mock_api):
        """Test successful data fetching from OANDA."""
        # Mock OANDA API response
        mock_response = {
            'candles': [
                {
                    'time': '2025-04-15T00:00:00.000000000Z',
                    'complete': True,
                    'mid': {'o': '2300.00', 'h': '2305.50', 'l': '2298.75', 'c': '2303.25'},
                    'volume': 1000
                },
                {
                    'time': '2025-04-15T00:05:00.000000000Z',
                    'complete': True,
                    'mid': {'o': '2303.25', 'h': '2307.00', 'l': '2302.00', 'c': '2306.50'},
                    'volume': 1200
                },
                {
                    'time': '2025-04-15T00:10:00.000000000Z',
                    'complete': False,  # This one should be skipped
                    'mid': {'o': '2306.50', 'h': '2308.25', 'l': '2305.75', 'c': '2307.00'},
                    'volume': 800
                }
            ]
        }
        
        # Setup the mock API client
        mock_instance = MagicMock()
        mock_api.return_value = mock_instance
        
        # Configure the mock request
        mock_request = MagicMock()
        mock_request.response = mock_response
        mock_instance.request.return_value = None
        
        # Patch InstrumentsCandles to return our mock request
        with patch('app.utils.market_data.InstrumentsCandles', return_value=mock_request):
            with patch('app.utils.market_data.get_api_key', return_value='test_api_key'):
                # Call the function
                result = fetch_oanda_data(timeframe='M5', count=3)
                
                # Verify the result is a DataFrame with the expected structure
                self.assertIsInstance(result, pd.DataFrame)
                self.assertEqual(len(result), 2)  # Only 2 complete candles
                self.assertIn('time', result.columns)
                self.assertIn('open', result.columns)
                self.assertIn('high', result.columns)
                self.assertIn('low', result.columns)
                self.assertIn('close', result.columns)
                self.assertIn('volume', result.columns)
                
                # Verify data is correctly parsed
                self.assertEqual(result['open'][0], 2300.00)
                self.assertEqual(result['high'][0], 2305.50)
                self.assertEqual(result['close'][1], 2306.50)

    @patch('app.utils.market_data.API')
    def test_fetch_oanda_data_api_error(self, mock_api):
        """Test error handling when OANDA API returns an error."""
        # Setup the mock to raise an exception
        mock_instance = MagicMock()
        mock_api.return_value = mock_instance
        
        # Create a simplified mock error instead of using V20Error directly
        class MockV20Error(Exception):
            pass
        
        # Patch the actual V20Error with our mock
        with patch('app.utils.market_data.V20Error', MockV20Error):
            # Make the request raise our mocked exception
            mock_instance.request.side_effect = MockV20Error('API error')
            
            # Patch InstrumentsCandles and get_api_key
            with patch('app.utils.market_data.InstrumentsCandles'):
                with patch('app.utils.market_data.get_api_key', return_value='test_api_key'):
                    # Call the function and verify it raises the expected exception
                    with self.assertRaises(RuntimeError):
                        fetch_oanda_data()

    def test_fetch_oanda_data_missing_credentials(self):
        """Test error handling when API credentials are missing."""
        # Patch get_api_key to return None (missing credentials)
        with patch('app.utils.market_data.get_api_key', return_value=None):
            # Call the function and verify it raises the expected exception
            with self.assertRaises(ValueError):
                fetch_oanda_data()

if __name__ == '__main__':
    unittest.main()