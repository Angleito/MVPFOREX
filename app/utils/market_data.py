"""
Utility functions for fetching and processing market data from OANDA.
"""

from datetime import datetime, timedelta
from app.db import SessionLocal
from app.utils.candles_db import get_candles_from_db
from app.models import Candlestick

def get_latest_market_data(_oanda_client_unused, instrument, granularity, count):
    """
    Fetch candlestick data from Supabase (Postgres) only. If missing, return an empty list.
    """
    session = SessionLocal()
    try:
        # Determine time range for candles
        end = datetime.utcnow()
        # OANDA granularity to minutes
        gran_map = {'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30, 'H1': 60, 'H4': 240, 'D': 1440}
        minutes = gran_map.get(granularity, 60)
        start = end - timedelta(minutes=minutes * count)

        # 1. Try DB first
        candles = get_candles_from_db(session, instrument, granularity, start, end)
        if candles and len(candles) >= count:
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
            # Placeholder trend/structure logic
            trend_info = {'direction': 'N/A', 'strength': 'N/A', 'current_price': data[-1]['close']}
            structure_points = {'swing_highs': [], 'swing_lows': []}
            return {
                'data': data,
                'trend_info': trend_info,
                'structure_points': structure_points
            }
        # No fallback: Just return what we have (may be empty)
        return []
    except Exception as e:
        return {'error': str(e)}
    finally:
        session.close()

