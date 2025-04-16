"""OANDA API client utilities."""
import os
import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from oandapyV20 import API
from oandapyV20.endpoints import accounts, instruments, pricing
from oandapyV20.exceptions import V20Error
from config.settings import (
    OANDA_API_KEY,
    OANDA_ACCOUNT_ID,
    OANDA_ENVIRONMENT,
    DEFAULT_TIMEFRAME,
    DEFAULT_COUNT
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for OANDA API requests."""
    
    def __init__(self, max_requests: int = 100, time_window: int = 1):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def wait_if_needed(self):
        """Check if we need to wait before making another request."""
        now = time.time()
        
        # Remove old requests from tracking
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            # Wait until we can make another request
            sleep_time = self.requests[0] + self.time_window - now
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
            
            # Clean up old requests again after waiting
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
        
        self.requests.append(now)

class OandaClient:
    """OANDA API client wrapper."""
    
    ENVIRONMENTS = {
        'practice': {
            'rest': 'https://api-fxpractice.oanda.com',  # Removed /v3 as it's handled by the client
            'stream': 'https://stream-fxpractice.oanda.com'
        },
        'live': {
            'rest': 'https://api-fxtrade.oanda.com',
            'stream': 'https://stream-fxtrade.oanda.com'
        }
    }
    
    def __init__(self):
        """Initialize OANDA client with configuration."""
        if not OANDA_API_KEY or not OANDA_ACCOUNT_ID:
            raise ValueError("Missing OANDA credentials. Check OANDA_API_KEY and OANDA_ACCOUNT_ID in .env")
            
        # Initialize OANDA API client
        try:
            self.client = API(
                access_token=OANDA_API_KEY,
                environment=OANDA_ENVIRONMENT
            )
            self.account_id = OANDA_ACCOUNT_ID
            
            # Test connection
            self.get_account_summary()
            logger.info("Successfully connected to OANDA API")
            
        except Exception as e:
            logger.error(f"Failed to initialize OANDA client: {str(e)}")
            raise

    def get_account_summary(self) -> Dict:
        """Get account summary information."""
        try:
            r = accounts.AccountSummary(self.account_id)
            response = self.client.request(r)
            logger.info("Successfully retrieved account summary")
            return response
            
        except V20Error as e:
            logger.error(f"OANDA API error getting account summary: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting account summary: {str(e)}")
            raise

    def get_candles(
        self,
        instrument: str = "XAU_USD",
        timeframe: str = DEFAULT_TIMEFRAME,
        count: int = DEFAULT_COUNT
    ) -> Dict:
        """Fetch candlestick data for a given instrument."""
        try:
            params = {
                "count": count,
                "granularity": timeframe,
                "price": "MBA"  # Get mid, bid, and ask prices
            }
            
            request = instruments.InstrumentsCandles(
                instrument=instrument,
                params=params
            )
            
            response = self.client.request(request)
            logger.info(f"Successfully retrieved {len(response['candles'])} candles for {instrument}")
            return self._format_candle_response(response)
            
        except V20Error as e:
            logger.error(f"OANDA API error getting candles for {instrument}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting candles for {instrument}: {str(e)}")
            raise

    def get_current_price(self, instrument: str = "XAU_USD") -> Dict:
        """Get current price for an instrument."""
        try:
            params = {"instruments": instrument}
            request = pricing.PricingInfo(
                accountID=self.account_id,
                params=params
            )
            
            response = self.client.request(request)
            logger.info(f"Successfully retrieved current price for {instrument}")
            return response
            
        except V20Error as e:
            logger.error(f"OANDA API error getting price for {instrument}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting price for {instrument}: {str(e)}")
            raise
    
    def _format_candle_response(self, response: Dict) -> Dict:
        """Format the OANDA candle response into a more usable structure."""
        try:
            candles = response.get('candles', [])
            formatted_candles = []
            
            for candle in candles:
                if not candle.get('complete', False):
                    continue  # Skip incomplete candles
                    
                formatted_candles.append({
                    'time': candle['time'],
                    'open': float(candle['mid']['o']),
                    'high': float(candle['mid']['h']),
                    'low': float(candle['mid']['l']),
                    'close': float(candle['mid']['c']),
                    'volume': int(candle['volume'])
                })
            
            return {
                'instrument': response['instrument'],
                'granularity': response['granularity'],
                'candles': formatted_candles
            }
            
        except Exception as e:
            logger.error(f"Error formatting candle response: {str(e)}")
            raise

# Create singleton instance
oanda_client = OandaClient()