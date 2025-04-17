"""
Utility functions for fetching and processing market data from OANDA.
"""

from datetime import datetime, timedelta
import logging
import pandas as pd
from typing import Dict, Any, Optional
from oandapyV20 import API
from oandapyV20.endpoints.instruments import InstrumentsCandles
from oandapyV20.exceptions import V20Error
from app.db import SessionLocal
from app.utils.candles_db import get_candles_from_db
from app.models import Candlestick
from app.utils.api_helpers import get_api_key, get_oanda_account_id
from app.utils.market_analysis import identify_trend, find_structure_points
from config.settings import OANDA_ENVIRONMENT, DEFAULT_TIMEFRAME, DEFAULT_COUNT

# Configure logging
logger = logging.getLogger(__name__)

def fetch_oanda_data(timeframe: str = DEFAULT_TIMEFRAME, count: int = DEFAULT_COUNT) -> pd.DataFrame:
    """
    Fetch recent XAUUSD candle data from OANDA API.
    
    Args:
        timeframe: The granularity of the candles (e.g., 'M5', 'H1')
        count: Number of candles to retrieve
        
    Returns:
        DataFrame with columns: time, open, high, low, close, volume
        
    Raises:
        ValueError: If API credentials are missing or invalid
        RuntimeError: If there's an error fetching data from OANDA
    """
    logger.info(f"Fetching {count} XAUUSD candles with {timeframe} timeframe")
    
    # Get API credentials
    api_key = get_api_key('oanda')
    if not api_key:
        logger.error("Missing OANDA API key")
        raise ValueError("Missing OANDA API key. Please check your environment variables.")
    
    try:
        # Initialize OANDA API client
        client = API(access_token=api_key, environment=OANDA_ENVIRONMENT)
        
        # Set up parameters for the request
        params = {
            "count": count,
            "granularity": timeframe,
            "price": "M"  # 'M' for midpoint prices
        }
        
        # Create and send the request
        request = InstrumentsCandles(instrument="XAU_USD", params=params)
        client.request(request)
        
        # Process the response
        candles = request.response['candles']
        data = []
        
        for candle in candles:
            # Only include complete candles
            if candle.get('complete', False):
                data.append({
                    'time': candle['time'],
                    'open': float(candle['mid']['o']),
                    'high': float(candle['mid']['h']),
                    'low': float(candle['mid']['l']),
                    'close': float(candle['mid']['c']),
                    'volume': int(candle['volume'])
                })
        
        # Create pandas DataFrame
        df = pd.DataFrame(data)
        
        # Convert time to datetime for easier manipulation
        if 'time' in df.columns and not df.empty:
            df['time'] = pd.to_datetime(df['time'])
        
        logger.info(f"Successfully retrieved {len(df)} candles of XAUUSD data")
        return df
        
    except V20Error as e:
        error_msg = f"OANDA API error: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Error fetching OANDA data: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def get_latest_market_data(
    oanda_client = None,
    instrument: str = "XAU_USD",
    timeframe: str = DEFAULT_TIMEFRAME,
    count: int = DEFAULT_COUNT
) -> Dict[str, Any]:
    """
    Get the latest market data and perform preliminary analysis.
    
    Args:
        oanda_client: Optional OandaClient instance
        instrument: The instrument to fetch data for (e.g., 'XAU_USD')
        timeframe: The granularity of the candles (e.g., 'M5', 'H1')
        count: Number of candles to retrieve
        
    Returns:
        Dictionary containing market data, trend information, and structure points
    """
    session = SessionLocal()
    try:
        # Determine time range for candles
        end = datetime.utcnow()
        # OANDA granularity to minutes
        gran_map = {'M1': 1, 'M5': 5, 'M15': 15, 'M30': 30, 'H1': 60, 'H4': 240, 'D': 1440}
        minutes = gran_map.get(timeframe, 60)
        start = end - timedelta(minutes=minutes * count)

        # 1. Try DB first
        logger.info(f"Fetching candles from DB for {instrument} {timeframe}")
        db_candles = get_candles_from_db(session, instrument, timeframe, start, end)
        
        if db_candles and len(db_candles) >= 5:  # At least 5 candles to make analysis meaningful
            logger.info(f"Found {len(db_candles)} candles in DB")
            data = [
                {
                    'time': c.timestamp,
                    'open': c.open,
                    'high': c.high,
                    'low': c.low,
                    'close': c.close,
                    'volume': c.volume
                } for c in db_candles[-count:]
            ]
            # Convert to DataFrame
            market_data = pd.DataFrame(data)
        else:
            # 2. If DB doesn't have enough data, use fetch_oanda_data
            logger.info(f"Insufficient data in DB, using fetch_oanda_data()")
            market_data = fetch_oanda_data(timeframe, count)

            # Save new candles to DB
            try:
                from app.models import Candlestick
                from app.utils.candles_db import save_candles_to_db
                candles_to_save = []
                for _, row in market_data.iterrows():
                    c = Candlestick(
                        instrument=instrument,
                        granularity=timeframe,
                        timestamp=row['time'].to_pydatetime() if hasattr(row['time'], 'to_pydatetime') else row['time'],
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row['volume']
                    )
                    candles_to_save.append(c)
                if candles_to_save:
                    save_candles_to_db(session, candles_to_save)
                    logger.info(f"Saved {len(candles_to_save)} new candles to DB for {instrument} {timeframe}")
            except Exception as db_exc:
                logger.error(f"Failed to save fetched OANDA candles to DB: {db_exc}")
        
        # Use the new market structure analysis functions
        try:
            # Identify trend
            trend_info = identify_trend(market_data)
            logger.info(f"Trend identified: {trend_info['direction']} ({trend_info['strength']})")
            
            # Find structure points
            structure_points = find_structure_points(market_data)
            logger.info(f"Found {len(structure_points['swing_highs'])} swing highs and {len(structure_points['swing_lows'])} swing lows")
            
        except Exception as e:
            logger.error(f"Error in market structure analysis: {str(e)}", exc_info=True)
            # Fallback with basic trend info if analysis fails
            if not market_data.empty:
                close_prices = market_data['close'].tolist()[-5:]
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
                    'current_price': market_data['close'].iloc[-1] if not market_data.empty else None,
                    'sma20': None,
                    'sma50': None,
                }
                
                # Empty structure points
                structure_points = {
                    'swing_highs': [],
                    'swing_lows': []
                }
            else:
                # Fallback with mock data
                logger.warning("No data retrieved, using fallback mock data")
                mock_price = 2300.00  # Default for XAU_USD
                trend_info = {
                    'direction': 'N/A', 
                    'strength': 'N/A', 
                    'current_price': mock_price,
                    'sma20': None,
                    'sma50': None,
                }
                
                # Empty structure points
                structure_points = {
                    'swing_highs': [],
                    'swing_lows': []
                }
        
        return {
            'data': market_data,
            'trend_info': trend_info,
            'structure_points': structure_points
        }
        
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}", exc_info=True)
        return {'error': str(e)}
    finally:
        session.close()

