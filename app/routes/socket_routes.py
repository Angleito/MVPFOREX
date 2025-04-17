"""
WebSocket routes for real-time data streaming in MVPFOREX application.
"""
import logging
import uuid
import json
from typing import Dict, Any
from flask import request, session
from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)

def register_socket_routes(socketio):
    """Register all WebSocket event handlers with the SocketIO instance.
    
    Args:
        socketio: The SocketIO instance to register routes with
    """
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection to WebSocket."""
        sid = request.sid
        client_id = str(uuid.uuid4())
        session['client_id'] = client_id
        logger.info(f"Client connected: {sid} with ID {client_id}")
        emit('connection_established', {'client_id': client_id, 'status': 'connected'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection from WebSocket."""
        sid = request.sid
        client_id = session.get('client_id', 'unknown')
        logger.info(f"Client disconnected: {sid} with ID {client_id}")
        
        # Unregister client from all price streams
        try:
            from app.utils.oanda_stream import get_stream_manager
            stream_manager = get_stream_manager()
            if stream_manager:
                stream_manager.unregister_client(client_id)
        except Exception as e:
            logger.error(f"Error unregistering client {client_id} from streams: {str(e)}")
    
    @socketio.on('subscribe_prices')
    def handle_subscribe_prices(data):
        """Subscribe to real-time price updates for an instrument.
        
        Expected data format:
        {
            "instrument": "XAU_USD"
        }
        """
        sid = request.sid
        client_id = session.get('client_id')
        if not client_id:
            emit('error', {'error': 'Not authenticated'})
            return
        
        try:
            instrument = data.get('instrument', '').upper()
            if not instrument:
                emit('error', {'error': 'No instrument specified'})
                return
            
            logger.info(f"Client {client_id} subscribing to {instrument} price updates")
            
            # Add client to room for this instrument
            join_room(instrument)
            
            # Register client with stream manager
            from app.utils.oanda_stream import get_stream_manager
            stream_manager = get_stream_manager()
            if stream_manager:
                stream_manager.register_client(client_id, instrument)
                
                # Send initial price data if available
                latest_tick = stream_manager.get_latest_tick(instrument)
                if latest_tick:
                    emit('price_update', latest_tick)
                
                emit('subscription_status', {
                    'status': 'subscribed',
                    'instrument': instrument
                })
            else:
                emit('error', {'error': 'Stream manager not initialized'})
        except Exception as e:
            logger.error(f"Error subscribing to prices: {str(e)}")
            emit('error', {'error': f'Failed to subscribe: {str(e)}'})
    
    @socketio.on('unsubscribe_prices')
    def handle_unsubscribe_prices(data):
        """Unsubscribe from price updates for an instrument.
        
        Expected data format:
        {
            "instrument": "XAU_USD"
        }
        """
        sid = request.sid
        client_id = session.get('client_id')
        if not client_id:
            return
        
        try:
            instrument = data.get('instrument', '').upper()
            if not instrument:
                return
            
            logger.info(f"Client {client_id} unsubscribing from {instrument} price updates")
            
            # Remove client from room
            leave_room(instrument)
            
            # Unregister client from stream
            from app.utils.oanda_stream import get_stream_manager
            stream_manager = get_stream_manager()
            if stream_manager:
                stream_manager.unregister_client(client_id, instrument)
                
            emit('subscription_status', {
                'status': 'unsubscribed',
                'instrument': instrument
            })
        except Exception as e:
            logger.error(f"Error unsubscribing from prices: {str(e)}")
    
    @socketio.on('get_price_snapshot')
    def handle_get_price_snapshot(data):
        """Get a snapshot of the latest price for an instrument.
        
        Expected data format:
        {
            "instrument": "XAU_USD"
        }
        """
        try:
            instrument = data.get('instrument', '').upper()
            if not instrument:
                emit('error', {'error': 'No instrument specified'})
                return
            
            from app.utils.oanda_stream import get_stream_manager
            stream_manager = get_stream_manager()
            if stream_manager:
                latest_tick = stream_manager.get_latest_tick(instrument)
                if latest_tick:
                    emit('price_snapshot', latest_tick)
                else:
                    emit('error', {'error': f'No price data available for {instrument}'})
            else:
                emit('error', {'error': 'Stream manager not initialized'})
        except Exception as e:
            logger.error(f"Error getting price snapshot: {str(e)}")
            emit('error', {'error': f'Failed to get price snapshot: {str(e)}'})
    
    logger.info("WebSocket routes registered successfully")
