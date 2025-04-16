"""
Utility functions for fetching and processing market data from OANDA.
"""

def get_latest_market_data(oanda_client, instrument, granularity, count):
    """
    Fetch minimal market data for MVP. Uses get_current_price and returns dummy structure.
    """
    try:
        price_response = oanda_client.get_current_price(instrument)
        # Extract price from response
        price = None
        if price_response and 'prices' in price_response:
            price = float(price_response['prices'][0]['asks'][0]['price'])
        data = [{"instrument": instrument, "price": price}] if price else []
        trend_info = {"direction": "N/A", "strength": "N/A", "current_price": price}
        structure_points = {"swing_highs": [], "swing_lows": []}
        return {
            "data": data,
            "trend_info": trend_info,
            "structure_points": structure_points
        }
    except Exception as e:
        return {"error": str(e)}
