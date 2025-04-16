"""
Utility functions for fetching and processing market data from OANDA.
"""

def get_latest_market_data(oanda_client, instrument, granularity, count):
    """
    Fetch latest market data and return structure for analysis.
    Returns a dict with keys: data, trend_info, structure_points, error (optional).
    """
    try:
        # Fetch candlestick data from OANDA
        candles = oanda_client.get_candles(
            instrument=instrument,
            granularity=granularity,
            count=count
        )
        # Structure the data for analysis (simplified)
        data = candles if candles else []
        # Dummy trend_info and structure_points for now
        trend_info = {"direction": "N/A", "strength": "N/A", "current_price": data[-1]["close"] if data else None}
        structure_points = {"swing_highs": [], "swing_lows": []}
        return {
            "data": data,
            "trend_info": trend_info,
            "structure_points": structure_points
        }
    except Exception as e:
        return {"error": str(e)}
