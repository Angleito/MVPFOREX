"""
Utility functions for fetching and processing market data from OANDA.
"""

from datetime import datetime, timedelta
import logging
from app.db import SessionLocal
from app.utils.candles_db import get_candles_from_db
from app.models import Candlestick

logger = logging.getLogger(__name__)

def get_latest_market_data(oanda_client, instrument, granularity, count):
    """
    Fetch candlestick data from Supabase (Postgres) or directly from OANDA if DB data is unavailable.
    """
    session = SessionLocal()
    try:
        # Determine time range for candles
        end = datetime.utcnow()
        # OANDA granularity to minutes
        gran_map = {'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30, 'H1': 60, 'H4': 240, 'D': 1440}
        minutes = gran_map.get(granularity, 60)
        start = end - timedelta(minutes=minutes * count)

        try:
            # 1. Try DB first
            logger.info(f"Fetching candles from DB for {instrument} {granularity}")
            candles = get_candles_from_db(session, instrument, granularity, start, end)
            
            if candles and len(candles) >= 5:  # At least 5 candles to make analysis meaningful
                logger.info(f"Found {len(candles)} candles in DB")
                data = [
                    {
                        'instrument': c.instrument,
                        'granularity': c.granularity,
                        'timestamp': c.timestamp.isoformat(),
                        'open': c.open,
                        'high': c.high,
                        'low': c.low,
                        'close': c.close,
                        'volume': c.volume
                    } for c in candles[-count:]
                ]
                # Simple trend detection based on most recent candles
                close_prices = [c.close for c in candles[-5:]]
                if close_prices[-1] > close_prices[0]:
                    trend_direction = "Bullish"
                elif close_prices[-1] < close_prices[0]:
                    trend_direction = "Bearish"
                else:
                    trend_direction = "Sideways"
                
                trend_info = {
                    'direction': trend_direction, 
                    'strength': 'Moderate', 
                    'current_price': data[-1]['close']
                }
                
                # Placeholder for structure points
                structure_points = {'swing_highs': [], 'swing_lows': []}
                
                return {
                    'data': data,
                    'trend_info': trend_info,
                    'structure_points': structure_points
                }
            
            # 2. If DB doesn't have enough data, try OANDA API
            if oanda_client:
                logger.info(f"Insufficient data in DB, fetching from OANDA API")
                
                # Get candles from OANDA
                params = {
                    "count": count,
                    "granularity": granularity,
                    "price": "M"  # Midpoint candles
                }
                
                response = oanda_client.get_candles(instrument, params)
                if 'candles' in response:
                    logger.info(f"Got {len(response['candles'])} candles from OANDA")
                    data = []
                    for c in response['candles']:
                        if c['complete']:  # Only use complete candles
                            data.append({
                                'instrument': instrument,
                                'granularity': granularity,
                                'timestamp': c['time'],
                                'open': float(c['mid']['o']),
                                'high': float(c['mid']['h']),
                                'low': float(c['mid']['l']),
                                'close': float(c['mid']['c']),
                                'volume': c['volume']
                            })
                    
                    if data:
                        # Simple trend detection based on most recent candles
                        close_prices = [d['close'] for d in data[-5:]]
                        if len(close_prices) >= 2:
                            if close_prices[-1] > close_prices[0]:
                                trend_direction = "Bullish"
                            elif close_prices[-1] < close_prices[0]:
                                trend_direction = "Bearish"
                            else:
                                trend_direction = "Sideways"
                        else:
                            trend_direction = "Unknown"
                        
                        trend_info = {
                            'direction': trend_direction, 
                            'strength': 'Moderate', 
                            'current_price': data[-1]['close'] if data else 0
                        }
                        
                        # Placeholder for structure points
                        structure_points = {'swing_highs': [], 'swing_lows': []}
                        
                        return {
                            'data': data,
                            'trend_info': trend_info,
                            'structure_points': structure_points
                        }
        except Exception as e:
            logger.error(f"Error fetching market data: {str(e)}", exc_info=True)
        
        # Fallback: Return mock data if everything else fails
        logger.warning("All data fetch methods failed, using fallback mock data")
        mock_price = 2300.00  # Default for XAU_USD
        mock_data = [{'close': mock_price}]
        trend_info = {'direction': 'N/A', 'strength': 'N/A', 'current_price': mock_price}
        structure_points = {'swing_highs': [], 'swing_lows': []}
        
        return {
            'data': mock_data,
            'trend_info': trend_info,
            'structure_points': structure_points
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_latest_market_data: {str(e)}", exc_info=True)
        return {'error': str(e)}
    finally:
        session.close()

