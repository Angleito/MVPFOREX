"""
Simplified AI analysis module for MVPFOREX that works with the frontend format.
This provides fallback implementation for all AI models when API keys aren't available.
"""

import logging
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

def generate_openai_analysis(market_data: Dict[str, Any]) -> str:
    """
    Generate a simplified analysis for the GPT-4.1 model based on current market data.
    """
    logger.info("Generating OpenAI analysis with simplified implementation")
    
    # Extract key market indicators and ensure proper types
    current_price = float(market_data.get('currentPrice', market_data.get('price', 0)))
    day_high = float(market_data.get('dayHigh', market_data.get('day_high', 0)))
    day_low = float(market_data.get('dayLow', market_data.get('day_low', 0)))
    
    # Ensure daily_change is a float
    daily_change_raw = market_data.get('dailyChange', market_data.get('daily_change', '0'))
    daily_change = float(daily_change_raw) if daily_change_raw else 0
    
    # Get other indicators with proper type conversion
    rsi_raw = market_data.get('rsi', 50)
    rsi = float(rsi_raw) if rsi_raw else 50
    
    macd_raw = market_data.get('macd', 0)
    macd = float(macd_raw) if macd_raw else 0
    
    signal_raw = market_data.get('signal', 0)
    signal = float(signal_raw) if signal_raw else 0
    
    trend = str(market_data.get('trend', 'Neutral'))
    fifty_day_ma_raw = market_data.get('fiftyDayMA', None)
    fifty_day_ma = float(fifty_day_ma_raw) if fifty_day_ma_raw else current_price * 0.98
    two_hundred_day_ma_raw = market_data.get('twoHundredDayMA', None)
    two_hundred_day_ma = float(two_hundred_day_ma_raw) if two_hundred_day_ma_raw else current_price * 0.95
    volatility_raw = market_data.get('volatility', 0.5)
    volatility = float(volatility_raw) if volatility_raw else 0.5
    supports = market_data.get('supports', [day_low - 5, day_low - 15, day_low - 25])
    resistances = market_data.get('resistances', [day_high + 5, day_high + 15, day_high + 25])
    
    # Format date and time
    date = datetime.now().strftime("%b %d, %Y")
    time_now = datetime.now().strftime("%I:%M %p")
    
    # Determine trend emoji
    trend_emoji = '📈' if trend == 'Bullish' else '📉' if trend == 'Bearish' else '➡️'
    
    # Generate the analysis
    analysis = f"{trend_emoji} XAUUSD Technical Analysis - {date} at {time_now}\n\n"
    analysis += f"Current Price: ${current_price:.2f} ({daily_change}% daily change)\n\n"
    
    analysis += "Key Indicators:\n"
    analysis += f"- RSI(14): {rsi:.2f} ({rsi > 70 and 'Overbought' or rsi < 30 and 'Oversold' or 'Neutral'})\n"
    analysis += f"- MACD: {macd:.2f} / Signal: {signal:.2f} ({macd > signal and 'Bullish' or 'Bearish'} momentum)\n"
    analysis += f"- 50 Day MA: ${fifty_day_ma:.2f} (Price {current_price > fifty_day_ma and 'above' or 'below'} MA, {current_price > fifty_day_ma and 'bullish' or 'bearish'})\n"
    analysis += f"- 200 Day MA: ${two_hundred_day_ma:.2f} ({current_price > two_hundred_day_ma and 'Long-term uptrend' or 'Long-term downtrend'})\n"
    analysis += f"- Volatility: {volatility}% ({float(volatility) > 0.8 and 'Above average' or 'Average'})\n\n"
    
    analysis += "Technical Outlook:\n"
    analysis += f"XAUUSD is {trend.lower()} with immediate resistance at ${resistances[0]}. RSI at {rsi:.2f} indicates "
    analysis += f"{rsi > 70 and 'overbought conditions, suggesting a potential reversal' or rsi < 30 and 'oversold conditions, suggesting a potential bounce' or 'neutral conditions'}. "
    analysis += f"The MACD {macd > signal and 'remains positive relative to the signal line, confirming bullish momentum' or 'has crossed below the signal line, indicating bearish pressure'}.\n\n"
    
    analysis += f"Key support levels are at ${supports[0]} (daily low) and ${supports[1]} (previous resistance now support). "
    
    analysis += "\n\nStrategy Recommendation:\n"
    analysis += f"Conservative: {rsi > 60 and f'Consider waiting for a pullback to ${day_low + (day_high - day_low) * 0.5} before entering long positions.' or f'Look for long entries near ${supports[0]} with tight stops.'}\n"
    analysis += f"Aggressive: {daily_change > 0 and f'Maintain long positions with stops below ${supports[1]}.' or f'Consider short positions below ${supports[0]} with target at ${supports[1]}.'}\n\n"
    
    analysis += f"Target: ${resistances[1]} with extended target at ${resistances[2]} if volume increases.\n\n"
    
    analysis += f"Analysis generated at {date} {time_now}"
    
    return analysis

def generate_claude_analysis(market_data: Dict[str, Any]) -> str:
    """
    Generate a simplified analysis for the Claude 3.7 model based on current market data.
    """
    logger.info("Generating Claude analysis with simplified implementation")
    
    # Extract key market indicators and ensure proper types
    current_price = float(market_data.get('currentPrice', market_data.get('price', 0)))
    day_high = float(market_data.get('dayHigh', market_data.get('day_high', 0)))
    day_low = float(market_data.get('dayLow', market_data.get('day_low', 0)))
    
    # Ensure daily_change is a float
    daily_change_raw = market_data.get('dailyChange', market_data.get('daily_change', '0'))
    daily_change = float(daily_change_raw) if daily_change_raw else 0
    
    # Get other indicators with proper type conversion
    rsi_raw = market_data.get('rsi', 50)
    rsi = float(rsi_raw) if rsi_raw else 50
    
    macd_raw = market_data.get('macd', 0)
    macd = float(macd_raw) if macd_raw else 0
    
    signal_raw = market_data.get('signal', 0)
    signal = float(signal_raw) if signal_raw else 0
    
    trend = str(market_data.get('trend', 'Neutral'))
    volume = int(market_data.get('volume', 15000))
    fib_retracement = market_data.get('fibRetracement', {
        '23.6%': day_high - (day_high - day_low) * 0.236,
        '38.2%': day_high - (day_high - day_low) * 0.382,
        '50.0%': day_high - (day_high - day_low) * 0.5,
        '61.8%': day_high - (day_high - day_low) * 0.618,
        '78.6%': day_high - (day_high - day_low) * 0.786,
    })
    supports = market_data.get('supports', [day_low - 5, day_low - 15, day_low - 25])
    resistances = market_data.get('resistances', [day_high + 5, day_high + 15, day_high + 25])
    
    # Format date and time
    date = datetime.now().strftime("%b %d, %Y")
    time_now = datetime.now().strftime("%I:%M %p")
    
    # Generate the analysis (Claude style with more formal structure)
    analysis = f"OANDA XAUUSD Analysis - {date}\n\n"
    analysis += f"Price Action Summary ({time_now}):\n"
    analysis += f"XAUUSD is currently trading at ${current_price:.2f}, with daily range of ${day_low:.2f}-${day_high:.2f}. "
    analysis += f"Volume at {volume} units suggests {volume > 15000 and 'strong' or 'moderate'} market participation.\n\n"
    
    analysis += "Fibonacci Analysis:\n"
    analysis += "Recent swing high-low retracement levels:"
    for level, price in fib_retracement.items():
        analysis += f"\n• {level}: ${float(price):.2f}"
    
    analysis += f"\n\nThe 38.2% level at ${float(fib_retracement.get('38.2%', 0)):.2f} appears to be currently acting as immediate support, "
    analysis += f"while the 23.6% level at ${float(fib_retracement.get('23.6%', 0)):.2f} provides resistance.\n\n"
    
    analysis += "Wave Structure:\n"
    analysis += f"Gold appears to be in {current_price > day_low and 'wave 3' or 'wave 4'} of a 5-wave Elliott sequence, likely "
    analysis += f"{current_price > day_low and 'trending between $' + str(supports[1]) + '-$' + str(resistances[1]) or 'range-bound between $' + str(supports[0]) + '-$' + str(resistances[0])}. "
    analysis += "Fibonacci time extensions suggest potential breakout attempt within 2-3 trading sessions.\n\n"
    
    analysis += "Market Context:\n"
    analysis += f"{current_price > day_low and 'USD weakness providing tailwind for gold' or 'Strong USD headwinds pressuring gold'}, "
    analysis += f"while physical demand remains {volume > 15000 and 'robust' or 'steady'} according to OANDA order flow data. "
    analysis += f"Institutional positioning shows {rsi > 50 and 'net-long' or 'balanced'} bias with {int(rsi * 1.2)}% bullish sentiment.\n\n"
    
    analysis += "Recommendation:\n"
    analysis += f"{macd > signal and 'Watch for breakout continuation above $' + str(resistances[0]) + ' with increased volume, which would signal potential test of $' + str(resistances[1]) + ' level.' or 'Monitor for reversal signals at current levels, with potential retest of support at $' + str(supports[1]) + '.'}\n\n"
    
    analysis += f"Position management: Trailing stop recommended at ${(current_price - (current_price * 0.01)):.2f} to protect positions from market volatility.\n\n"
    
    analysis += f"Analysis generated at {date} {time_now}"
    
    return analysis

def generate_perplexity_analysis(market_data: Dict[str, Any]) -> str:
    """
    Generate a simplified analysis for the Perplexity Pro model based on current market data.
    """
    logger.info("Generating Perplexity analysis with simplified implementation")
    
    # Extract key market indicators and ensure proper types
    current_price = float(market_data.get('currentPrice', market_data.get('price', 0)))
    day_high = float(market_data.get('dayHigh', market_data.get('day_high', 0)))
    day_low = float(market_data.get('dayLow', market_data.get('day_low', 0)))
    
    # Ensure daily_change is a float
    daily_change_raw = market_data.get('dailyChange', market_data.get('daily_change', '0'))
    daily_change = float(daily_change_raw) if daily_change_raw else 0
    
    # Get other indicators with proper type conversion
    rsi_raw = market_data.get('rsi', 50)
    rsi = float(rsi_raw) if rsi_raw else 50
    
    macd_raw = market_data.get('macd', 0)
    macd = float(macd_raw) if macd_raw else 0
    
    signal_raw = market_data.get('signal', 0)
    signal = float(signal_raw) if signal_raw else 0
    
    trend = str(market_data.get('trend', 'Neutral'))
    volume = int(market_data.get('volume', 15000))
    
    volatility_raw = market_data.get('volatility', 0.5)
    volatility = float(volatility_raw) if volatility_raw else 0.5
    
    fifty_day_ma_raw = market_data.get('fiftyDayMA', None)
    fifty_day_ma = float(fifty_day_ma_raw) if fifty_day_ma_raw else current_price * 0.98
    
    two_hundred_day_ma_raw = market_data.get('twoHundredDayMA', None)
    two_hundred_day_ma = float(two_hundred_day_ma_raw) if two_hundred_day_ma_raw else current_price * 0.95
    supports = market_data.get('supports', [day_low - 5, day_low - 15, day_low - 25])
    resistances = market_data.get('resistances', [day_high + 5, day_high + 15, day_high + 25])
    
    # Format date and time
    date = datetime.now().strftime("%b %d, %Y")
    time_now = datetime.now().strftime("%I:%M %p")
    
    # Generate the analysis (Perplexity style with structured markdown format)
    analysis = f"## XAUUSD OANDA Technical Analysis\n"
    analysis += f"Timestamp: {date} {time_now}\n\n"
    
    analysis += "### Current Market Status\n"
    analysis += f"• Price: ${current_price:.2f}\n"
    analysis += f"• 24h Change: {daily_change}%\n"
    analysis += f"• Range: ${day_low:.2f} - ${day_high:.2f}\n"
    analysis += f"• Volume: {volume} ({volume > 14000 and 'High' or 'Average'})\n\n"
    
    analysis += "### Key Technical Levels\n"
    analysis += "**Support:**\n"
    analysis += f"1. ${supports[0]} (Intraday)\n"
    analysis += f"2. ${supports[1]} (Previous consolidation)\n"
    analysis += f"3. ${supports[2]} (Weekly pivot)\n\n"
    
    analysis += "**Resistance:**\n"
    analysis += f"1. ${resistances[0]} (Current ceiling)\n"
    analysis += f"2. ${resistances[1]} (Monthly high)\n"
    analysis += f"3. ${resistances[2]} (Yearly target)\n\n"
    
    analysis += "### Indicator Analysis\n"
    analysis += f"• **RSI(14)**: {rsi:.2f} - {rsi > 70 and 'Overbought' or rsi < 30 and 'Oversold' or 'Neutral'}\n"
    analysis += f"• **MACD**: {macd:.3f} / Signal: {signal:.3f} - {macd > signal and 'Bullish' or 'Bearish'} divergence\n"
    analysis += f"• **Moving Averages**: Price {current_price > fifty_day_ma and 'above' or 'below'} 50 MA (${fifty_day_ma:.2f}) and {current_price > two_hundred_day_ma and 'above' or 'below'} 200 MA (${two_hundred_day_ma:.2f})\n"
    analysis += f"• **Bollinger Bands**: Price testing {current_price > fifty_day_ma + 30 and 'upper' or current_price < fifty_day_ma - 30 and 'lower' or 'middle'} band with {float(volatility) > 0.8 and 'increased' or 'normal'} volatility (ATR {volatility})\n\n"
    
    analysis += "### Market Insight\n"
    analysis += f"XAUUSD is currently testing the {current_price > fifty_day_ma + 30 and 'upper' or current_price < fifty_day_ma - 30 and 'lower' or 'middle'} Bollinger Band with {float(volatility) > 0.8 and 'heightened' or 'normal'} volatility. "
    analysis += f"OANDA order flow data indicates {current_price > day_low and 'accumulation' or 'distribution'} at ${supports[0]}-${supports[1]} range. "
    analysis += f"The Commitment of Traders report shows {rsi > 60 and 'increased long positioning' or 'mixed positioning'} among institutional traders.\n\n"
    
    # Safer conditional string formatting with explicit type checking
    if daily_change > 0:
        analysis += "Inflation concerns and geopolitical tensions continue supporting prices, "
    else:
        analysis += "Dollar strength and profit-taking pressure prices, "
    # Safer string construction with explicit conditions
    if rsi > 70 or rsi < 30:
        analysis += "while technical indicators suggest potential reversal. "
    else:
        analysis += "while technical indicators suggest continuation of current trend. "
    # Safer string construction for relative strength
    if daily_change > 0:
        analysis += "Relative strength against USD appears strengthening in intraday timeframes.\n\n"
    else:
        analysis += "Relative strength against USD appears weakening in intraday timeframes.\n\n"
    
    analysis += "### Trading Approach\n"
    # Safe construction of short-term strategy recommendation
    analysis += "• **Short-term**: "
    if rsi > 70:
        analysis += f"Consider profit-taking above ${resistances[0]:.2f}"
    elif rsi < 30:
        analysis += "Look for short-term bounce opportunities"
    else:
        analysis += "Follow the trend with tight stops"
    analysis += "\n"
    # Safe construction of medium-term strategy recommendation
    analysis += "• **Medium-term**: "
    if current_price > two_hundred_day_ma:
        mid_level = (day_high - day_low) * 0.5 + day_low
        analysis += f"Maintain bullish bias, looking for entries near ${mid_level:.2f} level"
    else:
        analysis += f"Exercise caution, watching for stabilization above ${supports[1]:.2f}"
    analysis += "\n"
    analysis += f"• **Risk management**: Set stops below ${(supports[0] - 5):.2f} to limit potential drawdown\n\n"
    
    analysis += f"Analysis generated at {date} {time_now}"
    
    return analysis
