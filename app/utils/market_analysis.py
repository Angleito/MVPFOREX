"""
Market structure analysis functions for Fibonacci trading strategy.

This module contains functions for identifying market trends
and structure points (swing highs and lows) for Fibonacci analysis.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

# Configure logging
logger = logging.getLogger(__name__)

def identify_trend(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Identifies the trend direction and strength based on price action and moving averages.
    
    Args:
        data: DataFrame with OHLC price data
        
    Returns:
        Dictionary containing trend direction, strength, current price, and SMAs
        
    Raises:
        ValueError: If data is empty or doesn't contain required columns
    """
    if data.empty:
        logger.error("Cannot identify trend: Empty dataframe provided")
        raise ValueError("Empty dataframe provided")
    
    required_columns = ['close', 'high', 'low']
    if not all(col in data.columns for col in required_columns):
        logger.error(f"DataFrame is missing required columns: {required_columns}")
        raise ValueError(f"DataFrame must contain columns: {required_columns}")
    
    # Calculate SMAs
    try:
        data = data.copy()  # Create copy to avoid SettingWithCopyWarning
        
        # Handle the case where we have insufficient data for moving averages
        sma20_value = None
        sma50_value = None
        
        if len(data) >= 20:
            data['sma20'] = data['close'].rolling(window=20).mean()
            sma20_value = data['sma20'].iloc[-1]
            
        if len(data) >= 50:
            data['sma50'] = data['close'].rolling(window=50).mean()
            sma50_value = data['sma50'].iloc[-1]
        
        # Get the current price
        current_price = data['close'].iloc[-1]
        
        # Identify recent highs and lows (last 30 candles or all if less)
        lookback = min(30, len(data))
        recent_data = data.iloc[-lookback:]
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        
        # Default values
        trend_direction = "Neutral"
        trend_strength = "Weak"
        
        # Check for SMA crossovers and price position relative to SMAs
        if sma20_value is not None and sma50_value is not None:
            # Full analysis with both SMAs
            if sma20_value > sma50_value:
                # Potential bullish trend
                if current_price > sma20_value:
                    trend_direction = "Bullish"
                    
                    # Check if we have higher highs in recent data
                    # Compare last 5 candles with previous 5 candles
                    if len(highs) >= 10:
                        if (highs[-5:] > highs[-10:-5]).sum() >= 3:
                            trend_strength = "Strong"
            
            elif sma20_value < sma50_value:
                # Potential bearish trend
                if current_price < sma20_value:
                    trend_direction = "Bearish"
                    
                    # Check if we have lower lows in recent data
                    if len(lows) >= 10:
                        if (lows[-5:] < lows[-10:-5]).sum() >= 3:
                            trend_strength = "Strong"
            
            # If SMAs are very close, check the slope
            elif abs(sma20_value - sma50_value) < (current_price * 0.0005):  # Within 0.05%
                # Calculate slope of SMA20 over last 5 candles
                if len(data) >= 25:  # Need 5 more candles for slope
                    sma20_slope = data['sma20'].iloc[-1] - data['sma20'].iloc[-5]
                    if sma20_slope > 0:
                        trend_direction = "Bullish"
                        trend_strength = "Weak"  # Weakly bullish during crossover
                    elif sma20_slope < 0:
                        trend_direction = "Bearish"
                        trend_strength = "Weak"  # Weakly bearish during crossover
        
        elif sma20_value is not None:
            # Only SMA20 is available (20-49 candles)
            close_prices = data['close'].values
            price_change = close_prices[-1] - close_prices[-min(20, len(close_prices))]
            
            if current_price > sma20_value:
                trend_direction = "Bullish"
            elif current_price < sma20_value:
                trend_direction = "Bearish"
            
            # Simple strength measure based on price volatility
            recent_range = (data['high'] - data['low']).mean()
            if abs(price_change) > (recent_range * 2):
                trend_strength = "Strong"
        
        else:
            # Not enough data even for SMA20, use simplified trend detection
            if len(data) >= 5:  # At least need 5 candles for basic trend
                close_prices = data['close'].values
                price_change = close_prices[-1] - close_prices[0]
                if price_change > 0:
                    trend_direction = "Bullish"
                elif price_change < 0:
                    trend_direction = "Bearish"
                
                # Simple strength measure based on recent volatility
                recent_range = (data['high'] - data['low']).mean()
                if abs(price_change) > (recent_range * 2):
                    trend_strength = "Strong"
        
        result = {
            "direction": trend_direction,
            "strength": trend_strength,
            "current_price": current_price,
            "sma20": sma20_value,
            "sma50": sma50_value
        }
        
        logger.info(f"Trend identified: {trend_direction} ({trend_strength})")
        return result
        
    except Exception as e:
        logger.error(f"Error in trend identification: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to identify trend: {str(e)}")


def find_structure_points(data: pd.DataFrame, window: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """
    Identifies potential swing highs and lows for Fibonacci analysis.
    
    Args:
        data: DataFrame with OHLC price data
        window: Number of candles to look before and after for local extrema (default: 5)
        
    Returns:
        Dictionary with lists of swing highs and swing lows
        
    Raises:
        ValueError: If data is empty or doesn't contain required columns
    """
    if data.empty:
        logger.error("Cannot find structure points: Empty dataframe provided")
        raise ValueError("Empty dataframe provided")
    
    required_columns = ['high', 'low', 'time']
    if not all(col in data.columns for col in required_columns):
        logger.error(f"DataFrame is missing required columns: {required_columns}")
        raise ValueError(f"DataFrame must contain columns: {required_columns}")
    
    highs = []
    lows = []
    
    try:
        # Need enough data points for the analysis
        if len(data) < (2 * window + 1):
            logger.warning(f"Not enough data points for window size {window}. Need at least {2*window+1}, got {len(data)}")
            # Return empty lists if not enough data
            return {'swing_highs': [], 'swing_lows': []}
        
        for i in range(window, len(data) - window):
            # Check if this is a local maximum (swing high)
            window_highs = data['high'].iloc[i-window:i+window+1]
            if data['high'].iloc[i] == window_highs.max():
                highs.append({
                    'index': i,
                    'price': data['high'].iloc[i],
                    'time': data['time'].iloc[i]
                })
            
            # Check if this is a local minimum (swing low)
            window_lows = data['low'].iloc[i-window:i+window+1]
            if data['low'].iloc[i] == window_lows.min():
                lows.append({
                    'index': i,
                    'price': data['low'].iloc[i],
                    'time': data['time'].iloc[i]
                })
        
        # Return only the most recent 3 swing points (or fewer if we found fewer)
        recent_highs = highs[-3:] if highs else []
        recent_lows = lows[-3:] if lows else []
        
        logger.info(f"Found {len(recent_highs)} recent swing highs and {len(recent_lows)} recent swing lows")
        
        return {
            'swing_highs': recent_highs,
            'swing_lows': recent_lows
        }
    
    except Exception as e:
        logger.error(f"Error finding structure points: {str(e)}", exc_info=True)
        raise RuntimeError(f"Failed to find structure points: {str(e)}")


def calculate_fibonacci_levels(start_price: float, end_price: float) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement levels between two price points.
    
    Args:
        start_price: Starting price level (0% level)
        end_price: Ending price level (100% level)
        
    Returns:
        Dictionary with Fibonacci levels
    """
    # Calculate the price range
    price_range = end_price - start_price
    
    # Key Fibonacci levels
    fib_levels = {
        "0.0": start_price,
        "0.236": start_price + (price_range * 0.236),
        "0.382": start_price + (price_range * 0.382),
        "0.5": start_price + (price_range * 0.5),
        "0.618": start_price + (price_range * 0.618),
        "0.705": start_price + (price_range * 0.705),  # OTE specific level
        "0.786": start_price + (price_range * 0.786),
        "1.0": end_price,
        "1.272": start_price + (price_range * 1.272),
        "1.618": start_price + (price_range * 1.618)
    }
    
    return fib_levels


def calculate_ote_zone(
    trend_direction: str, 
    structure_points: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, Any]:
    """
    Calculate the Optimal Trading Entry (OTE) zone based on Fibonacci levels.
    
    Args:
        trend_direction: "Bullish" or "Bearish"
        structure_points: Dictionary with swing highs and lows
        
    Returns:
        Dictionary with OTE zone details and Fibonacci levels
    """
    if not structure_points['swing_highs'] or not structure_points['swing_lows']:
        logger.warning("Cannot calculate OTE zone: No structure points available")
        return {
            "ote_zone": None,
            "fib_levels": None,
            "entry_price": None,
            "stop_loss": None,
            "take_profit1": None,
            "take_profit2": None
        }
    
    try:
        # For bullish trend, we measure from low to high
        if trend_direction == "Bullish":
            # Get the last swing low and swing high
            swing_low = structure_points['swing_lows'][-1]['price']
            swing_high = structure_points['swing_highs'][-1]['price']
            
            # Calculate Fibonacci levels
            fib_levels = calculate_fibonacci_levels(swing_low, swing_high)
            
            # OTE zone is between 0.618 and 0.786
            ote_zone = {
                "start": fib_levels["0.618"],
                "end": fib_levels["0.786"]
            }
            
            # Entry price at 0.705 Fibonacci level
            entry_price = fib_levels["0.705"]
            
            # Stop loss 3 pips below the swing low
            stop_loss = swing_low - 0.0003  # 3 pips in gold
            
            # TP1 at 1:1 risk-reward ratio
            risk = entry_price - stop_loss
            take_profit1 = entry_price + risk
            
            # TP2 at the 0% Fibonacci level (the recent swing high)
            take_profit2 = swing_high
            
        # For bearish trend, we measure from high to low
        elif trend_direction == "Bearish":
            # Get the last swing high and swing low
            swing_high = structure_points['swing_highs'][-1]['price']
            swing_low = structure_points['swing_lows'][-1]['price']
            
            # Calculate Fibonacci levels (reversed direction)
            fib_levels = calculate_fibonacci_levels(swing_high, swing_low)
            
            # OTE zone is between 0.618 and 0.786
            ote_zone = {
                "start": fib_levels["0.618"],
                "end": fib_levels["0.786"]
            }
            
            # Entry price at 0.705 Fibonacci level
            entry_price = fib_levels["0.705"]
            
            # Stop loss 3 pips above the swing high
            stop_loss = swing_high + 0.0003  # 3 pips in gold
            
            # TP1 at 1:1 risk-reward ratio
            risk = abs(entry_price - stop_loss)
            take_profit1 = entry_price - risk
            
            # TP2 at the 0% Fibonacci level (the recent swing low)
            take_profit2 = swing_low
            
        else:
            # Neutral trend, no clear OTE zone
            logger.warning(f"Cannot calculate OTE zone for {trend_direction} trend")
            return {
                "ote_zone": None,
                "fib_levels": None,
                "entry_price": None,
                "stop_loss": None,
                "take_profit1": None,
                "take_profit2": None
            }
        
        return {
            "ote_zone": ote_zone,
            "fib_levels": fib_levels,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit1": take_profit1,
            "take_profit2": take_profit2
        }
    
    except Exception as e:
        logger.error(f"Error calculating OTE zone: {str(e)}", exc_info=True)
        return {
            "ote_zone": None,
            "fib_levels": None,
            "entry_price": None,
            "stop_loss": None,
            "take_profit1": None,
            "take_profit2": None
        }