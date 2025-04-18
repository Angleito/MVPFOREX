from sqlalchemy.orm import Session
from app.models import Candlestick
from datetime import datetime

def get_candles_from_db(session: Session, instrument: str, granularity: str, start: datetime, end: datetime):
    """Fetch candles from DB in the given range."""
    return session.query(Candlestick).filter(
        Candlestick.instrument == instrument,
        Candlestick.granularity == granularity,
        Candlestick.timestamp >= start,
        Candlestick.timestamp <= end
    ).order_by(Candlestick.timestamp).all()

def save_candles_to_db(session: Session, candles: list):
    """Bulk insert candlestick objects."""
    session.bulk_save_objects(candles)
    session.commit()
