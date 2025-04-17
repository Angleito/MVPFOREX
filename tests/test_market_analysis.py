"""Test the market structure analysis module."""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.utils.market_analysis import (
    identify_trend, 
    find_structure_points,
    calculate_fibonacci_levels,
    calculate_ote_zone
)

class TestMarketAnalysis(unittest.TestCase):
    """Test cases for market structure analysis functions."""

    def create_sample_data(self, trend_type="bullish", volatility=0.01, candles=100):
        """Create sample OHLC data for testing with different trend types."""
        now = datetime.now()
        dates = [now - timedelta(minutes=i) for i in range(candles, 0, -1)]
        
        # Base price and basic trend
        if trend_type == "bullish":
            base = 2000.0
            price_trend = np.linspace(0, 1, candles) * 50  # Upward trend
        elif trend_type == "bearish":
            base = 2050.0
            price_trend = np.linspace(0, 1, candles) * -50  # Downward trend
        elif trend_type == "sideways":
            base = 2025.0
            price_trend = np.zeros(candles)  # Flat trend
        else:
            raise ValueError(f"Invalid trend type: {trend_type}")
        
        # Add some randomness
        np.random.seed(42)  # For reproducibility
        noise = np.random.normal(0, volatility, candles)
        
        # Create price components
        close_prices = base + price_trend + noise.cumsum()
        open_prices = close_prices - np.random.normal(0, volatility, candles)
        high_prices = np.maximum(close_prices, open_prices) + abs(np.random.normal(0, volatility, candles))
        low_prices = np.minimum(close_prices, open_prices) - abs(np.random.normal(0, volatility, candles))
        
        # Create DataFrame
        df = pd.DataFrame({
            'time': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': np.random.randint(100, 1000, candles)
        })
        
        return df

    def test_identify_trend_bullish(self):
        """Test trend identification with bullish data."""
        # Create sample bullish data
        df = self.create_sample_data(trend_type="bullish", candles=100)
        
        # Call identify_trend function
        result = identify_trend(df)
        
        # Assertions
        self.assertEqual(result["direction"], "Bullish")
        self.assertIn(result["strength"], ["Weak", "Strong"])
        self.assertIsNotNone(result["current_price"])
        self.assertIsNotNone(result["sma20"])
        self.assertIsNotNone(result["sma50"])

    def test_identify_trend_bearish(self):
        """Test trend identification with bearish data."""
        # Create sample bearish data
        df = self.create_sample_data(trend_type="bearish", candles=100)
        
        # Call identify_trend function
        result = identify_trend(df)
        
        # Assertions
        self.assertEqual(result["direction"], "Bearish")
        self.assertIn(result["strength"], ["Weak", "Strong"])
        self.assertIsNotNone(result["current_price"])
        self.assertIsNotNone(result["sma20"])
        self.assertIsNotNone(result["sma50"])

    def test_identify_trend_sideways(self):
        """Test trend identification with sideways data."""
        # Create sample sideways data
        df = self.create_sample_data(trend_type="sideways", candles=100)
        
        # Call identify_trend function
        result = identify_trend(df)
        
        # In sideways data, the trend might be identified as weak bullish, weak bearish, or neutral
        self.assertIn(result["direction"], ["Bullish", "Bearish", "Neutral"])
        # With sideways data, the trend should not be strong
        if result["direction"] != "Neutral":
            self.assertEqual(result["strength"], "Weak")
        
        self.assertIsNotNone(result["current_price"])
        self.assertIsNotNone(result["sma20"])
        self.assertIsNotNone(result["sma50"])

    def test_identify_trend_insufficient_data(self):
        """Test trend identification with insufficient data."""
        # Create sample data with only 10 candles (not enough for SMA50)
        df = self.create_sample_data(trend_type="bullish", candles=10)
        
        # Call identify_trend function
        result = identify_trend(df)
        
        # Assertions - should still get a result but with None for both SMAs
        self.assertIn(result["direction"], ["Bullish", "Bearish", "Neutral"])
        self.assertIn(result["strength"], ["Weak", "Strong"])
        self.assertIsNotNone(result["current_price"])
        self.assertIsNone(result["sma20"])  # Not enough data for SMA20
        self.assertIsNone(result["sma50"])  # Not enough data for SMA50

    def test_identify_trend_empty_data(self):
        """Test trend identification with empty data."""
        # Create empty DataFrame
        df = pd.DataFrame(columns=['time', 'open', 'high', 'low', 'close', 'volume'])
        
        # Call identify_trend function and expect ValueError
        with self.assertRaises(ValueError):
            identify_trend(df)

    def test_find_structure_points(self):
        """Test finding structure points in price data."""
        # Create sample data with clear highs and lows
        df = self.create_sample_data(trend_type="bullish", volatility=0.02, candles=50)
        
        # Call find_structure_points function
        result = find_structure_points(df)
        
        # Assertions
        self.assertIn('swing_highs', result)
        self.assertIn('swing_lows', result)
        # Number of swing points should be reasonable (at least one, but likely more)
        # The exact number will depend on the random data
        self.assertLessEqual(len(result['swing_highs']), 3)  # Max 3 as specified in the function
        self.assertLessEqual(len(result['swing_lows']), 3)  # Max 3 as specified in the function
        
        # Check structure of each swing point
        if result['swing_highs']:
            high = result['swing_highs'][0]
            self.assertIn('index', high)
            self.assertIn('price', high)
            self.assertIn('time', high)
        
        if result['swing_lows']:
            low = result['swing_lows'][0]
            self.assertIn('index', low)
            self.assertIn('price', low)
            self.assertIn('time', low)

    def test_find_structure_points_insufficient_data(self):
        """Test finding structure points with insufficient data."""
        # Create sample data with only 5 candles (not enough for window=5)
        df = self.create_sample_data(trend_type="bullish", candles=5)
        
        # Call find_structure_points function
        result = find_structure_points(df)
        
        # Assertions - should get empty lists
        self.assertEqual(result['swing_highs'], [])
        self.assertEqual(result['swing_lows'], [])

    def test_calculate_fibonacci_levels(self):
        """Test calculation of Fibonacci levels."""
        # Test with bullish scenario (low to high)
        low_price = 2000.0
        high_price = 2100.0
        
        fib_levels = calculate_fibonacci_levels(low_price, high_price)
        
        # Check key Fibonacci levels
        self.assertEqual(fib_levels["0.0"], low_price)
        self.assertEqual(fib_levels["1.0"], high_price)
        self.assertAlmostEqual(fib_levels["0.618"], low_price + (high_price - low_price) * 0.618)
        self.assertAlmostEqual(fib_levels["0.705"], low_price + (high_price - low_price) * 0.705)
        
        # Test with bearish scenario (high to low)
        fib_levels_bearish = calculate_fibonacci_levels(high_price, low_price)
        
        # Check key Fibonacci levels for bearish
        self.assertEqual(fib_levels_bearish["0.0"], high_price)
        self.assertEqual(fib_levels_bearish["1.0"], low_price)

    def test_calculate_ote_zone(self):
        """Test calculation of OTE (Optimal Trade Entry) zone."""
        # Create structure points for testing
        structure_points = {
            'swing_highs': [{'index': 0, 'price': 2100.0, 'time': datetime.now()}],
            'swing_lows': [{'index': 0, 'price': 2000.0, 'time': datetime.now()}]
        }
        
        # Test bullish trend
        ote_bullish = calculate_ote_zone("Bullish", structure_points)
        
        # Assertions for bullish
        self.assertIsNotNone(ote_bullish["ote_zone"])
        self.assertIsNotNone(ote_bullish["entry_price"])
        self.assertIsNotNone(ote_bullish["stop_loss"])
        self.assertIsNotNone(ote_bullish["take_profit1"])
        self.assertIsNotNone(ote_bullish["take_profit2"])
        
        # Entry should be at 0.705 Fibonacci level
        swing_low = structure_points['swing_lows'][0]['price']
        swing_high = structure_points['swing_highs'][0]['price']
        expected_entry = swing_low + (swing_high - swing_low) * 0.705
        self.assertAlmostEqual(ote_bullish["entry_price"], expected_entry)
        
        # Stop loss should be 3 pips below the swing low
        self.assertAlmostEqual(ote_bullish["stop_loss"], swing_low - 0.0003)
        
        # Test bearish trend
        ote_bearish = calculate_ote_zone("Bearish", structure_points)
        
        # Assertions for bearish
        self.assertIsNotNone(ote_bearish["ote_zone"])
        self.assertIsNotNone(ote_bearish["entry_price"])
        self.assertIsNotNone(ote_bearish["stop_loss"])
        self.assertIsNotNone(ote_bearish["take_profit1"])
        self.assertIsNotNone(ote_bearish["take_profit2"])
        
        # Test neutral trend (should return None values)
        ote_neutral = calculate_ote_zone("Neutral", structure_points)
        self.assertIsNone(ote_neutral["ote_zone"])
        self.assertIsNone(ote_neutral["entry_price"])
        
        # Test with empty structure points
        empty_structure = {'swing_highs': [], 'swing_lows': []}
        ote_empty = calculate_ote_zone("Bullish", empty_structure)
        self.assertIsNone(ote_empty["ote_zone"])
        self.assertIsNone(ote_empty["entry_price"])

if __name__ == '__main__':
    unittest.main()