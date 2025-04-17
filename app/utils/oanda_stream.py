"""
OANDA real-time streaming API integration for MVPFOREX.
This module handles the WebSocket connection to OANDA's streaming API
and forwards real-time price updates to connected clients.
"""
import os
import json
import time
import logging
import threading
from typing import Dict, List, Any, Optional, Callable
import requests
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class OandaStreamManager:
    """Manages streaming connections to OANDA's API and broadcasts to WebSocket clients."""
    
    def __init__(self, socketio: SocketIO):
        """Initialize the stream manager.
        
        Args:
            socketio: Flask-SocketIO instance for broadcasting to clients
        """
        self.socketio = socketio
        self.api_key = os.environ.get('OANDA_API_KEY')
        self.account_id = os.environ.get('OANDA_ACCOUNT_ID')
        self.streaming_url = os.environ.get('OANDA_STREAMING_URL', 'https://stream-fxtrade.oanda.com')
        self.base_url = os.environ.get('OANDA_API_URL', 'https://api-fxtrade.oanda.com')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        self.active_streams = {}  # type: Dict[str, Dict[str, Any]]
        self.connected_clients = {}  # type: Dict[str, List[str]]
        self.stream_lock = threading.Lock()
        self.is_running = True
        
        # Verify credentials
        if not self.api_key or not self.account_id:
            logger.error("OANDA API credentials not found in environment variables")
            raise ValueError("OANDA API credentials missing")
            
        logger.info("OandaStreamManager initialized successfully")
            
    def start_price_stream(self, instrument: str) -> bool:
        """Start a price stream for the specified instrument.
        
        Args:
            instrument: The instrument to stream (e.g., 'XAU_USD')
            
        Returns:
            bool: True if stream started successfully, False otherwise
        """
        with self.stream_lock:
            if instrument in self.active_streams:
                logger.info(f"Stream for {instrument} already active")
                return True
                
            logger.info(f"Starting price stream for {instrument}")
            
            # Create a thread for streaming
            stream_thread = threading.Thread(
                target=self._stream_prices,
                args=(instrument,),
                daemon=True
            )
            
            # Initialize stream data
            self.active_streams[instrument] = {
                'thread': stream_thread,
                'last_heartbeat': time.time(),
                'last_tick': None,
                'is_active': True
            }
            
            # Start the streaming thread
            stream_thread.start()
            logger.info(f"Stream thread started for {instrument}")
            return True
            
    def stop_price_stream(self, instrument: str) -> bool:
        """Stop the price stream for the specified instrument.
        
        Args:
            instrument: The instrument to stop streaming
            
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        with self.stream_lock:
            if instrument not in self.active_streams:
                logger.warning(f"No active stream found for {instrument}")
                return False
                
            logger.info(f"Stopping price stream for {instrument}")
            self.active_streams[instrument]['is_active'] = False
            
            # Remove from active streams
            del self.active_streams[instrument]
            return True
            
    def register_client(self, client_id: str, instrument: str) -> None:
        """Register a client for streaming updates.
        
        Args:
            client_id: Unique client identifier
            instrument: Instrument the client is interested in
        """
        with self.stream_lock:
            if instrument not in self.connected_clients:
                self.connected_clients[instrument] = []
                
            if client_id not in self.connected_clients[instrument]:
                self.connected_clients[instrument].append(client_id)
                logger.info(f"Client {client_id} registered for {instrument} updates")
                
            # Ensure stream is active for this instrument
            if instrument not in self.active_streams:
                self.start_price_stream(instrument)
                
    def unregister_client(self, client_id: str, instrument: Optional[str] = None) -> None:
        """Unregister a client from streaming updates.
        
        Args:
            client_id: Unique client identifier
            instrument: Optional instrument to unregister from. If None, unregister from all.
        """
        with self.stream_lock:
            if instrument:
                # Unregister from specific instrument
                if instrument in self.connected_clients and client_id in self.connected_clients[instrument]:
                    self.connected_clients[instrument].remove(client_id)
                    logger.info(f"Client {client_id} unregistered from {instrument} updates")
                    
                    # If no clients left, stop the stream
                    if not self.connected_clients[instrument]:
                        self.stop_price_stream(instrument)
                        del self.connected_clients[instrument]
            else:
                # Unregister from all instruments
                for instr in list(self.connected_clients.keys()):
                    if client_id in self.connected_clients[instr]:
                        self.connected_clients[instr].remove(client_id)
                        logger.info(f"Client {client_id} unregistered from {instr} updates")
                        
                        # If no clients left, stop the stream
                        if not self.connected_clients[instr]:
                            self.stop_price_stream(instr)
                            del self.connected_clients[instr]
    
    def _stream_prices(self, instrument: str) -> None:
        """Internal method to handle the price streaming from OANDA.
        
        Args:
            instrument: The instrument to stream prices for
        """
        url = f"{self.streaming_url}/v3/accounts/{self.account_id}/pricing/stream"
        params = {
            "instruments": instrument,
            "snapshot": "true"
        }
        
        logger.info(f"Connecting to OANDA streaming API for {instrument}")
        
        try:
            response = requests.get(
                url,
                headers=self.headers,
                params=params,
                stream=True
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to connect to OANDA streaming API: {response.status_code} {response.text}")
                with self.stream_lock:
                    if instrument in self.active_streams:
                        self.active_streams[instrument]['is_active'] = False
                return
                
            logger.info(f"Connected to OANDA streaming API for {instrument}")
            
            # Process the streaming data
            for line in response.iter_lines():
                # Check if stream should still be active
                with self.stream_lock:
                    if instrument not in self.active_streams or not self.active_streams[instrument]['is_active']:
                        logger.info(f"Stopping stream for {instrument} as requested")
                        break
                
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    
                    # Handle heartbeats
                    if 'type' in data and data['type'] == 'HEARTBEAT':
                        with self.stream_lock:
                            if instrument in self.active_streams:
                                self.active_streams[instrument]['last_heartbeat'] = time.time()
                        continue
                        
                    # Handle price updates
                    if 'type' in data and data['type'] == 'PRICE':
                        self._process_price_update(instrument, data)
                        
                except json.JSONDecodeError:
                    logger.warning(f"Failed to decode JSON from stream: {line}")
                except Exception as e:
                    logger.error(f"Error processing stream data: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Error in price stream for {instrument}: {str(e)}")
            
        finally:
            logger.info(f"Price stream for {instrument} has ended")
            with self.stream_lock:
                if instrument in self.active_streams:
                    self.active_streams[instrument]['is_active'] = False
    
    def _process_price_update(self, instrument: str, data: Dict[str, Any]) -> None:
        """Process a price update from the stream.
        
        Args:
            instrument: The instrument the update is for
            data: The price data received from OANDA
        """
        try:
            # Extract relevant price information
            if 'price' not in data or 'instrument' not in data['price']:
                return
                
            price_data = data['price']
            recv_instrument = price_data['instrument']
            
            # Ensure this is for the correct instrument
            if recv_instrument != instrument:
                return
                
            # Format the price data for clients
            client_data = {
                'instrument': recv_instrument,
                'time': price_data.get('time'),
                'bid': float(price_data.get('bids', [{'price': '0'}])[0]['price']),
                'ask': float(price_data.get('asks', [{'price': '0'}])[0]['price']),
                'spread': None,  # Will be calculated below
                'status': 'streaming'
            }
            
            # Calculate the spread
            if client_data['bid'] > 0 and client_data['ask'] > 0:
                if instrument.startswith('XAU_'):
                    # For gold, spread is in cents
                    client_data['spread'] = round((client_data['ask'] - client_data['bid']) * 100, 1)
                else:
                    # For forex, spread is in pips
                    client_data['spread'] = round((client_data['ask'] - client_data['bid']) * 10000, 1)
            
            # Store the last tick
            with self.stream_lock:
                if instrument in self.active_streams:
                    self.active_streams[instrument]['last_tick'] = client_data
            
            # Broadcast to connected clients
            self._broadcast_price_update(instrument, client_data)
            
        except Exception as e:
            logger.error(f"Error processing price update: {str(e)}")
    
    def _broadcast_price_update(self, instrument: str, data: Dict[str, Any]) -> None:
        """Broadcast price updates to connected clients.
        
        Args:
            instrument: The instrument the update is for
            data: The formatted price data to broadcast
        """
        try:
            # Only broadcast if there are clients registered for this instrument
            with self.stream_lock:
                if instrument not in self.connected_clients or not self.connected_clients[instrument]:
                    return
            
            # Broadcast the update
            self.socketio.emit('price_update', data, room=instrument)
            
        except Exception as e:
            logger.error(f"Error broadcasting price update: {str(e)}")
    
    def get_latest_tick(self, instrument: str) -> Optional[Dict[str, Any]]:
        """Get the latest tick data for an instrument.
        
        Args:
            instrument: The instrument to get data for
            
        Returns:
            Optional[Dict[str, Any]]: The latest tick data or None if not available
        """
        with self.stream_lock:
            if instrument in self.active_streams and self.active_streams[instrument]['last_tick']:
                return self.active_streams[instrument]['last_tick']
        return None
        
    def shutdown(self) -> None:
        """Shutdown all streams and clean up resources."""
        logger.info("Shutting down OandaStreamManager")
        self.is_running = False
        
        # Stop all active streams
        with self.stream_lock:
            for instrument in list(self.active_streams.keys()):
                self.stop_price_stream(instrument)
        
        logger.info("OandaStreamManager shutdown complete")

# Singleton instance to be initialized by the application
stream_manager = None  # type: Optional[OandaStreamManager]

def init_stream_manager(socketio: SocketIO) -> OandaStreamManager:
    """Initialize the stream manager singleton.
    
    Args:
        socketio: Flask-SocketIO instance
        
    Returns:
        OandaStreamManager: The initialized stream manager instance
    """
    global stream_manager
    if stream_manager is None:
        stream_manager = OandaStreamManager(socketio)
    return stream_manager

def get_stream_manager() -> Optional[OandaStreamManager]:
    """Get the stream manager singleton instance.
    
    Returns:
        Optional[OandaStreamManager]: The stream manager instance or None if not initialized
    """
    return stream_manager
