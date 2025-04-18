from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Candlestick(Base):
    __tablename__ = 'candlesticks'
    id = Column(Integer, primary_key=True)
    instrument = Column(String(20), nullable=False)
    granularity = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=True)
    __table_args__ = (
        UniqueConstraint('instrument', 'granularity', 'timestamp', name='_candle_uc'),
    )
