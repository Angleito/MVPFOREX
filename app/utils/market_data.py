"""
Utility functions for fetching and processing market data from OANDA.
"""

from datetime import datetime, timedelta
from app.db import SessionLocal
from app.utils.candles_db import get_candles_from_db, save_candles_to_db
from app.models import Candlestick

def get_latest_market_data(oanda_client, instrument, granularity, count):
    """
    Fetch candlestick data from Supabase (Postgres). If missing, fetch from OANDA, store, and return.
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
        if len(candles) >= count:
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
        # 2. Fetch from OANDA if not enough candles
        oanda_candles = oanda_client.get_candles(instrument, granularity, count)
        # Convert to DB objects
        new_candles = []
        for c in oanda_candles['candles']:
            if not c['complete']:
                continue
            new_candles.append(Candlestick(
                instrument=instrument,
                granularity=granularity,
                timestamp=datetime.fromisoformat(c['time'].replace('Z', '+00:00')),
                open=float(c['mid']['o']),
                high=float(c['mid']['h']),
                low=float(c['mid']['l']),
                close=float(c['mid']['c']),
                volume=float(c['volume'])
            ))
        save_candles_to_db(session, new_candles)
        # Return the latest candles
        return get_latest_market_data(oanda_client, instrument, granularity, count)
    except Exception as e:
        return {'error': str(e)}
    finally:
        session.close()

