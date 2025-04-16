"""Main application routes."""
from flask import Blueprint, render_template, jsonify, request
from app.utils.oanda_client import oanda_client
from config.settings import MODELS
import logging

# Configure logging
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@bp.route('/test_integration')
def test_integration():
    """Test both OANDA and AI model integrations."""
    try:
        logger.info("Starting integration test...")
        
        # Test OANDA connection first
        logger.info("Testing OANDA connection...")
        account_summary = oanda_client.get_account_summary()
        logger.info(f"Successfully connected to OANDA account {account_summary['account']['id']}")
        
        # Get OANDA candle data
        logger.info("Fetching OANDA candle data...")
        oanda_data = oanda_client.get_candles(
            instrument="XAU_USD",
            timeframe="M5",
            count=10
        )
        logger.info(f"Successfully retrieved {len(oanda_data['candles'])} candles")
        
        # Get current price data
        logger.info("Fetching current price data...")
        current_price = oanda_client.get_current_price("XAU_USD")
        logger.info("Successfully retrieved current price data")
        
        # Extract the latest price info
        latest_candle = oanda_data['candles'][-1]
        trend_info = {
            "direction": "Bullish" if latest_candle['close'] > latest_candle['open'] else "Bearish",
            "strength": "Testing",
            "current_price": latest_candle['close']
        }
        
        # Test AI integration
        logger.info("Testing AI integration...")
        client = get_ai_client()
        ai_response = client.chat.completions.create(
            model=MODELS['gpt4']['id'],
            messages=[
                {
                    "role": "user",
                    "content": f"Analyze this XAUUSD price data briefly: Current price ${latest_candle['close']}, previous close was ${oanda_data['candles'][-2]['close']}. Respond in 2 sentences maximum."
                }
            ],
            max_tokens=100,
            temperature=0.7
        )
        logger.info("Successfully received AI analysis")
        
        response_data = {
            'success': True,
            'oanda_connection': 'successful',
            'account_info': {
                'id': account_summary['account']['id'],
                'currency': account_summary['account']['currency'],
                'balance': float(account_summary['account']['balance'])
            },
            'latest_candle_data': {
                'time': latest_candle['time'],
                'open': latest_candle['open'],
                'high': latest_candle['high'],
                'low': latest_candle['low'],
                'close': latest_candle['close'],
                'volume': latest_candle['volume']
            },
            'current_price_data': current_price['prices'][0] if current_price['prices'] else None,
            'ai_analysis': ai_response.choices[0].message.content if ai_response.choices else "No AI analysis generated"
        }
        
        logger.info("Integration test completed successfully")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Integration test failed: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/test_requesty')
def test_requesty():
    """Test the Requesty API connection."""
    try:
        client = get_ai_client()
        # Using the simplest possible request for testing
        response = client.chat.completions.create(
            model=MODELS['gpt4']['id'],  # Using updated GPT-4.1 Vision model ID
            messages=[
                {
                    "role": "user",
                    "content": "Hi, please respond with just 'Connection successful!'"
                }
            ],
            max_tokens=10,
            temperature=0.1
        )
        
        return jsonify({
            'success': True,
            'message': response.choices[0].message.content if response.choices else "No response"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@bp.route('/analyze')
def analyze():
    """TEMP DEBUG: Analyze market data WITHOUT calling AI models to test timeout."""
    try:
        # Fetch live OANDA data (keep this part)
        logger.info("Fetching live OANDA data for /analyze endpoint...")
        current_price_data = oanda_client.get_current_price("XAU_USD")
        live_price = None
        if current_price_data and 'prices' in current_price_data and current_price_data['prices']:
            # Use the first ask price as the current live price
            live_price = float(current_price_data['prices'][0]['asks'][0]['price'])
            logger.info(f"Successfully fetched live price: {live_price}")
        else:
            logger.warning("Could not fetch live price from OANDA, using placeholder.")
            live_price = 2300.00 # Fallback placeholder if API fails

        # Use live price in trend info (keep other mock data for now)
        trend_info = {
            "direction": "Bullish",  # This might also need live calculation later
            "strength": "Strong",   # This might also need live calculation later
            "current_price": live_price
        }

        # Mock data for structure points (replace with real data fetching later if needed)
        mock_structure_points = {
            "swing_highs": [
                {"price": live_price, "time": "2025-04-16T10:00:00Z"}, # Example using live price
                {"price": round(live_price * 0.998, 2), "time": "2025-04-16T09:45:00Z"}
            ],
            "swing_lows": [
                {"price": round(live_price * 0.995, 2), "time": "2025-04-16T09:30:00Z"},
                {"price": round(live_price * 0.992, 2), "time": "2025-04-16T09:15:00Z"}
            ]
        }
        mock_market_data = {} # Keep market_data empty for now

        # TEMP DEBUG: Construct mock analysis result instead of calling AI
        logger.warning("TEMP DEBUG: Skipping AI analysis call.")
        all_analyses = {
            'claude': {'analysis': 'AI analysis skipped (debug mode)', 'model': 'claude-debug'},
            'gpt4': {'analysis': 'AI analysis skipped (debug mode)', 'model': 'gpt4-debug'},
            'perplexity': {'analysis': 'AI analysis skipped (debug mode)', 'model': 'perplexity-debug'}
        }

        logger.info("Returning mock analysis results (debug mode).")
        return jsonify({
            'trend': trend_info,
            'structure_points': mock_structure_points,
            'analyses': all_analyses
        })

    except Exception as e:
        logger.error(f"Error in /analyze route: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500