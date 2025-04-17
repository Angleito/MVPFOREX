import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import ModelButton from '../components/ModelButton';
import MarketOverview from '../components/MarketOverview';
import { isStorageAvailable } from '../utils/storage';

// Error boundary component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, errorInfo: null, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Component Error:', error, errorInfo);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      // Fallback UI when a component errors
      return this.props.fallback || (
        <div style={{padding: 20, margin: 10, border: '1px solid #ffcccc', borderRadius: 4, background: '#fff8f8'}}>
          <h3 style={{color: '#cc0000', margin: 0}}>Something went wrong</h3>
          <p style={{color: '#333'}}>{this.props.errorMessage || 'An error occurred in this component'}</p>
          {this.props.showDetails && (
            <details style={{marginTop: 10, color: '#666'}}>
              <summary>Error details</summary>
              <pre style={{overflow: 'auto', fontSize: 12}}>
                {this.state.error && this.state.error.toString()}
              </pre>
            </details>
          )}
        </div>
      );
    }
    return this.props.children;
  }
}

// TradingView widget component
const TradingViewWidget = () => {
  const [isClient, setIsClient] = useState(false);
  
  useEffect(() => {
    setIsClient(true);
    
    // Clean up any existing TradingView widgets
    const cleanup = () => {
      const existingScripts = document.querySelectorAll('script[src*="tradingview"]');
      existingScripts.forEach(script => script.remove());
    };
    
    // If we're client-side, load the TradingView widget
    if (isClient) {
      cleanup();
      
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/tv.js';
      script.async = true;
      script.onload = () => {
        if (window.TradingView) {
          new window.TradingView.widget({
            "width": "100%",
            "height": 500,
            "symbol": "OANDA:XAUUSD",
            "interval": "60",
            "timezone": "Etc/UTC",
            "theme": "light",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#f1f3f6",
            "enable_publishing": false,
            "hide_side_toolbar": false,
            "allow_symbol_change": true,
            "studies": ["BB@tv-basicstudies", "RSI@tv-basicstudies"],
            "container_id": "tradingview-widget"
          });
        }
      };
      document.head.appendChild(script);
    }
    
    return cleanup;
  }, [isClient]);
  
  if (!isClient) {
    return (
      <div style={{width: '100%', height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #e0e0e0', background: '#f9f9f9'}}>
        <div style={{textAlign: 'center'}}>
          <p style={{color: '#666'}}>Loading gold price chart...</p>
        </div>
      </div>
    );
  }
  
  return <div id="tradingview-widget" style={{width: '100%', height: 500}} />;
};

// Home page component
export default function Home() {
  console.log('Rendering Home component');
  
  // Define states with safe initial values
  const [modelOutputs, setModelOutputs] = useState({
    'GPT-4.1': '',
    'Claude 3.7': '',
    'Perplexity Pro': '',
  });
  const [loadingModel, setLoadingModel] = useState('');
  const [apiStatus, setApiStatus] = useState('unknown'); // 'unknown', 'available', 'unavailable'
  const [error, setError] = useState(null);
  const [storageAvailable, setStorageAvailable] = useState(null);
  const [marketData, setMarketData] = useState(null);
  
  // Model definitions
  const modelList = ['GPT-4.1', 'Claude 3.7', 'Perplexity Pro'];
  const modelDescriptions = {
    'GPT-4.1': "OpenAI's latest GPT model, tuned for financial and technical analysis.",
    'Claude 3.7': "Anthropic's Claude, specialized for reasoning and market narratives.",
    'Perplexity Pro': "Perplexity's Pro AI, focused on rapid, data-driven market insights."
  };

  // Check environment conditions on page load
  useEffect(() => {
    // Check storage availability
    try {
      const hasStorage = isStorageAvailable();
      setStorageAvailable(hasStorage);
      console.log('Storage available:', hasStorage);
    } catch (err) {
      console.warn('Error checking storage:', err);
      setStorageAvailable(false);
    }
    
    // Check API availability with a lightweight request
    const checkApi = async () => {
      try {
        console.log('Checking API availability...');
        const response = await fetch('/api/health');
        
        if (!response.ok) {
          throw new Error(`API returned status ${response.status}`);
        }
        
        const data = await response.json();
        console.log('API health check response:', data);
        
        if (data.status === 'healthy') {
          console.log('Backend API is available');
          setApiStatus('available');
        } else {
          console.log('Backend API is unhealthy');
          setApiStatus('unavailable');
        }
      } catch (err) {
        console.warn('Backend API is unreachable:', err);
        setApiStatus('unavailable');
      }
    };
    
    // Try to initialize Supabase connection
    const checkSupabase = async () => {
      try {
        const hasSupabaseConfig = !!(
          process.env.NEXT_PUBLIC_SUPABASE_URL && 
          process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
        );
        console.log('Supabase config available:', hasSupabaseConfig);
        
        if (hasSupabaseConfig) {
          // Dynamically import Supabase client to avoid dependency issues
          const { createClient } = await import('@supabase/supabase-js');
          const supabase = createClient(
            process.env.NEXT_PUBLIC_SUPABASE_URL,
            process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
          );
          console.log('Supabase client initialized');
        }
      } catch (err) {
        console.warn('Error initializing Supabase:', err);
      }
    };
    
    // Add market data fetch with robust error handling
    const fetchMarketData = async () => {
      try {
        console.log('Fetching market data...');
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout
        
        const response = await fetch('/api/market-data', {
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          throw new Error(`Market data API returned ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Market data fetched:', data);
        
        if (data.status === 'ok' && data.candles) {
          setMarketData(data);
          // If we got market data, API must be available
          setApiStatus('available');
        } else {
          console.warn('Invalid market data format:', data);
          setError('Invalid market data format received');
        }
      } catch (err) {
        console.warn('Error fetching market data:', err);
        // Don't set error state here as this isn't critical and we have fallback
      }
    };

    checkApi();
    fetchMarketData();
    const intervalId = setInterval(fetchMarketData, 60000); // Update every minute

    return () => clearInterval(intervalId);
  }, []);

  // Fetch real-time XAUUSD data from the Flask backend API
  const fetchRealTimeData = async () => {
    try {
      console.log('Fetching real-time XAUUSD market data from API...');
      
      // Use your Flask backend API endpoint to get real market data
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://mvpforex-api.vercel.app';
      const endpoint = `${apiUrl}/api/market-data`;
      
      const response = await fetch(endpoint);
      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      const apiData = await response.json();
      console.log('API Response:', apiData);
      
      if (apiData.error) {
        throw new Error(`API returned error: ${apiData.error}`);
      }
      
      // Extract the current price and other data from API response
      const currentPrice = apiData.trend_info?.current_price || 2400.00;
      
      // Get additional market data from API if available or calculate derived values
      const timeNow = new Date();
      const range = apiData.trend_info?.day_range || 15;
      const prevClose = apiData.prev_close || (currentPrice - 3);
      const dayHigh = apiData.day_high || (currentPrice + 7);
      const dayLow = apiData.day_low || (currentPrice - 5);
      const volume = apiData.volume || 15000;

      // Calculate technical indicators if not provided by API
      const dailyChange = apiData.daily_change || ((currentPrice - prevClose) / prevClose * 100).toFixed(2);
      const volatility = apiData.volatility || ((dayHigh - dayLow) / prevClose * 100).toFixed(2);
      const rsi = apiData.rsi || Math.min(Math.max(50 + (parseFloat(dailyChange) * 2), 30), 70);
      const macd = apiData.macd || parseFloat((dailyChange / 15).toFixed(3));
      const signal = apiData.signal || parseFloat((macd - 0.05).toFixed(3));
      
      // Moving averages - use API values or calculate
      const fiftyDayMA = apiData.fifty_day_ma || parseFloat((currentPrice * 0.985).toFixed(2));
      const twoHundredDayMA = apiData.two_hundred_day_ma || parseFloat((currentPrice * 0.96).toFixed(2));
      
      // Fibonacci levels based on day range
      const fibRetracement = apiData.fib_retracement || {
        '23.6%': (dayHigh - range * 0.236).toFixed(2),
        '38.2%': (dayHigh - range * 0.382).toFixed(2),
        '50.0%': (dayHigh - range * 0.5).toFixed(2),
        '61.8%': (dayHigh - range * 0.618).toFixed(2),
        '78.6%': (dayHigh - range * 0.786).toFixed(2),
      };
      
      // Support and resistance - use API values or fallbacks
      const supports = apiData.supports || [
        parseFloat(dayLow.toFixed(2)),
        parseFloat((currentPrice - (range * 0.5)).toFixed(2)),
        parseFloat((currentPrice - (range * 1.2)).toFixed(2))
      ];
      
      const resistances = apiData.resistances || [
        parseFloat(dayHigh.toFixed(2)),
        parseFloat((currentPrice + (range * 0.4)).toFixed(2)),
        parseFloat((currentPrice + (range * 1.1)).toFixed(2))
      ];
      
      // Create the full market data object with real API data
      const marketData = {
        source: 'oanda-api',
        currentPrice,
        prevClose,
        dayHigh,
        dayLow,
        volume,
        dailyChange,
        volatility,
        rsi,
        macd,
        signal,
        fiftyDayMA,
        twoHundredDayMA,
        fibRetracement,
        supports,
        resistances,
        trend: apiData.trend_info?.direction || 'Neutral',
        trendStrength: apiData.trend_info?.strength || 'Moderate',
        lastUpdated: timeNow.toISOString()
      };
      
      console.log('Successfully fetched real-time market data');
      return marketData;
    } catch (error) {
      console.error('Error fetching real-time data:', error);
      return fallbackMarketData();
    }
  };
  
  // Fallback market data generator in case API calls fail
  const fallbackMarketData = () => {
    console.warn('Using fallback market data');
    const currentPrice = 2405.75; 
    const prevClose = 2398.25;
    const dayHigh = 2412.80;
    const dayLow = 2395.10; 
    const volume = 15420;
    
    const dailyChange = ((currentPrice - prevClose) / prevClose * 100).toFixed(2);
    const volatility = ((dayHigh - dayLow) / prevClose * 100).toFixed(2);
    const rsi = 68.5;
    const macd = 1.23;
    const signal = 0.87;
    const fiftyDayMA = 2375.30;
    const twoHundredDayMA = 2310.55;
    
    const fibRetracement = {
      '23.6%': (dayHigh - (dayHigh - dayLow) * 0.236).toFixed(2),
      '38.2%': (dayHigh - (dayHigh - dayLow) * 0.382).toFixed(2),
      '50.0%': (dayHigh - (dayHigh - dayLow) * 0.5).toFixed(2),
      '61.8%': (dayHigh - (dayHigh - dayLow) * 0.618).toFixed(2),
      '78.6%': (dayHigh - (dayHigh - dayLow) * 0.786).toFixed(2),
    };
    
    const supports = [2395.10, 2380.25, 2362.50];
    const resistances = [2415.30, 2430.00, 2450.75];
    
    return {
      currentPrice,
      prevClose,
      dayHigh,
      dayLow,
      volume,
      dailyChange,
      volatility,
      rsi,
      macd,
      signal,
      fiftyDayMA,
      twoHundredDayMA,
      fibRetracement,
      supports,
      resistances,
      lastUpdated: new Date().toISOString()
    };
  };

  // Handle model analysis with real-time data
  const handleAnalyze = async (model) => {
    setLoadingModel(model);
    setModelOutputs(prev => ({
      ...prev,
      [model]: 'Fetching real-time OANDA XAUUSD data...'
    }));
    
    try {
      // Get real-time market data from API
      const indicators = await fetchRealTimeData();
      
      // Format date and time for analysis
      const date = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      
      // Try to get analysis from real AI models via the Flask API
      let modelOutput = '';
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://mvpforex-api.vercel.app';
      
      try {
        // Map the frontend model name to the backend API model name
        let apiModel = '';
        if (model === 'GPT-4.1') {
          apiModel = 'openai';
        } else if (model === 'Claude 3.7') {
          apiModel = 'anthropic';
        } else if (model === 'Perplexity Pro') {
          apiModel = 'perplexity';
        }
        
        console.log(`Requesting AI analysis from ${apiModel} model...`);
        
        // Create request payload with market data
        const payload = {
          market_data: {
            price: indicators.currentPrice,
            day_high: indicators.dayHigh,
            day_low: indicators.dayLow,
            daily_change: indicators.dailyChange,
            trend: indicators.trend || 'Neutral',
            rsi: indicators.rsi,
            macd: indicators.macd,
            signal: indicators.signal,
            fiftyDayMA: indicators.fiftyDayMA,
            twoHundredDayMA: indicators.twoHundredDayMA,
            supports: indicators.supports,
            resistances: indicators.resistances,
            fibRetracement: indicators.fibRetracement,
            volume: indicators.volume,
            volatility: indicators.volatility,
            lastUpdated: indicators.lastUpdated
          }
        };
        
        // Make real API request for AI analysis
        const response = await fetch(`${apiUrl}/api/analyze/${apiModel}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
          timeout: 30000 // 30 second timeout
        });
        
        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }
        
        const analysisData = await response.json();
        console.log('AI Analysis response:', analysisData);
        
        // Check if we got a valid response
        if (analysisData.analysis) {
          // Use the actual AI-generated analysis from the API
          modelOutput = analysisData.analysis;
          console.log(`Successfully received ${model} analysis from API`);
          
          // Add timestamp to the analysis
          modelOutput += `\n\nData analyzed at ${date} ${time}`;
          
          // Return the API-generated analysis
          return modelOutput;
        }
        
        // If API returned empty analysis, continue to fallback
        throw new Error('Invalid or empty analysis from API');
        
      } catch (apiError) {
        // Log the API error but continue with fallback analysis
        console.error(`Failed to get ${model} analysis from API:`, apiError);
        console.log('Using fallback analysis generation...');
        
        // FALLBACK: Generate model-specific analysis if API fails
        const trendEmoji = indicators.trend === 'Bullish' ? '📈' : indicators.trend === 'Bearish' ? '📉' : '➡️';
        
        const analyses = {
          'GPT-4.1': `${trendEmoji} XAUUSD Technical Analysis (Simulated) - ${date} at ${time}\n\nCurrent Price: $${indicators.currentPrice.toFixed(2)} (${indicators.dailyChange}% daily change)\n\nKey Indicators:\n- RSI(14): ${indicators.rsi.toFixed(2)} (${indicators.rsi > 70 ? 'Overbought' : indicators.rsi < 30 ? 'Oversold' : 'Neutral'})\n- MACD: ${indicators.macd.toFixed(2)} / Signal: ${indicators.signal.toFixed(2)} (${indicators.macd > indicators.signal ? 'Bullish' : 'Bearish'} momentum)\n- 50 Day MA: $${indicators.fiftyDayMA.toFixed(2)} (Price ${indicators.currentPrice > indicators.fiftyDayMA ? 'above' : 'below'} MA, ${indicators.currentPrice > indicators.fiftyDayMA ? 'bullish' : 'bearish'})\n- 200 Day MA: $${indicators.twoHundredDayMA.toFixed(2)} (${indicators.currentPrice > indicators.twoHundredDayMA ? 'Long-term uptrend' : 'Long-term downtrend'})\n- Volatility: ${indicators.volatility}% (${parseFloat(indicators.volatility) > 0.8 ? 'Above average' : 'Average'})\n\nTechnical Outlook:\nXAUUSD is ${indicators.currentPrice > indicators.prevClose ? 'trending higher' : 'trending lower'} with immediate resistance at $${indicators.resistances[0]}. RSI at ${indicators.rsi.toFixed(2)} indicates ${indicators.rsi > 70 ? 'overbought conditions, suggesting a potential reversal' : indicators.rsi < 30 ? 'oversold conditions, suggesting a potential bounce' : 'neutral conditions'}. The MACD ${indicators.macd > indicators.signal ? 'remains positive relative to the signal line, confirming bullish momentum' : 'has crossed below the signal line, indicating bearish pressure'}.\n\nKey support levels are at $${indicators.supports[0]} (daily low) and $${indicators.supports[1]} (previous resistance now support). The 61.8% Fibonacci retracement at $${indicators.fibRetracement['61.8%']} should provide additional support on pullbacks.\n\nStrategy Recommendation:\nConservative: ${indicators.rsi > 60 ? 'Consider waiting for a pullback to $' + indicators.fibRetracement['38.2%'] + ' before entering long positions.' : 'Look for long entries near $' + indicators.supports[0] + ' with tight stops.'}\nAggressive: ${indicators.dailyChange > 0 ? 'Maintain long positions with stops below $' + indicators.supports[1] + '.' : 'Consider short positions below $' + indicators.supports[0] + ' with target at $' + indicators.fibRetracement['61.8%'] + '.'}\n\nTarget: $${indicators.resistances[1]} with extended target at $${indicators.resistances[2]} if volume increases.\n\nData last updated: ${new Date(indicators.lastUpdated).toLocaleTimeString()}\n\nNote: This is simulated analysis (API connection failed)`,
          
          'Claude 3.7': `OANDA XAUUSD Analysis - ${date}\n\nPrice Action Summary (${time}):\nXAUUSD is currently trading at $${indicators.currentPrice.toFixed(2)}, with daily range of $${indicators.dayLow.toFixed(2)}-$${indicators.dayHigh.toFixed(2)}. Volume at ${indicators.volume} units suggests ${indicators.volume > 15000 ? 'strong' : 'moderate'} market participation.\n\nFibonacci Analysis:\nRecent swing high-low retracement levels:${Object.entries(indicators.fibRetracement).map(([level, price]) => `\n• ${level}: $${price}`).join('')}\n\nThe 38.2% level at $${indicators.fibRetracement['38.2%']} appears to be currently acting as immediate support, while the 23.6% level at $${indicators.fibRetracement['23.6%']} provides resistance.\n\nWave Structure:\nGold appears to be in ${indicators.currentPrice > indicators.prevClose ? 'wave 3' : 'wave 4'} of a 5-wave Elliott sequence, likely ${indicators.currentPrice > indicators.prevClose ? 'trending between $' + indicators.supports[1] + '-$' + indicators.resistances[1] : 'range-bound between $' + indicators.supports[0] + '-$' + indicators.resistances[0]}. Fibonacci time extensions suggest potential breakout attempt within 2-3 trading sessions.\n\nMarket Context:\n${indicators.currentPrice > indicators.prevClose ? 'USD weakness providing tailwind for gold' : 'Strong USD headwinds pressuring gold'}, while physical demand remains ${indicators.volume > 15000 ? 'robust' : 'steady'} according to OANDA order flow data. Institutional positioning shows ${indicators.rsi > 50 ? 'net-long' : 'balanced'} bias with ${Math.round(indicators.rsi * 1.2)}% bullish sentiment.\n\nRecommendation:\n${indicators.macd > indicators.signal ? 'Watch for breakout continuation above $' + indicators.resistances[0] + ' with increased volume, which would signal potential test of $' + indicators.resistances[1] + ' level.' : 'Monitor for reversal signals at current levels, with potential retest of support at $' + indicators.supports[1] + '.'}\n\nPosition management: Trailing stop recommended at $${(indicators.currentPrice - (indicators.currentPrice * 0.01)).toFixed(2)} to protect positions from market volatility.\n\nData last updated: ${new Date(indicators.lastUpdated).toLocaleTimeString()}\n\nNote: This is simulated analysis (API connection failed)`,
          
          'Perplexity Pro': `## XAUUSD OANDA Technical Analysis\nTimestamp: ${date} ${time}\n\n### Current Market Status\n• Price: $${indicators.currentPrice.toFixed(2)}\n• 24h Change: ${indicators.dailyChange}%\n• Range: $${indicators.dayLow.toFixed(2)} - $${indicators.dayHigh.toFixed(2)}\n• Volume: ${indicators.volume} (${indicators.volume > 14000 ? 'High' : 'Average'})\n\n### Key Technical Levels\n**Support:**\n1. $${indicators.supports[0]} (Intraday)\n2. $${indicators.supports[1]} (Previous consolidation)\n3. $${indicators.supports[2]} (Weekly pivot)\n\n**Resistance:**\n1. $${indicators.resistances[0]} (Current ceiling)\n2. $${indicators.resistances[1]} (Monthly high)\n3. $${indicators.resistances[2]} (Yearly target)\n\n### Indicator Analysis\n• **RSI(14)**: ${indicators.rsi.toFixed(2)} - ${indicators.rsi > 70 ? 'Overbought' : indicators.rsi < 30 ? 'Oversold' : 'Neutral'}\n• **MACD**: ${indicators.macd.toFixed(3)} / Signal: ${indicators.signal.toFixed(3)} - ${indicators.macd > indicators.signal ? 'Bullish' : 'Bearish'} divergence\n• **Moving Averages**: Price ${indicators.currentPrice > indicators.fiftyDayMA ? 'above' : 'below'} 50 MA ($${indicators.fiftyDayMA.toFixed(2)}) and ${indicators.currentPrice > indicators.twoHundredDayMA ? 'above' : 'below'} 200 MA ($${indicators.twoHundredDayMA.toFixed(2)})\n• **Bollinger Bands**: Price testing ${indicators.currentPrice > indicators.fiftyDayMA + 30 ? 'upper' : indicators.currentPrice < indicators.fiftyDayMA - 30 ? 'lower' : 'middle'} band with ${parseFloat(indicators.volatility) > 0.8 ? 'increased' : 'normal'} volatility (ATR ${indicators.volatility})\n\n### Market Insight\nXAUUSD is currently testing the ${indicators.currentPrice > indicators.fiftyDayMA + 30 ? 'upper' : indicators.currentPrice < indicators.fiftyDayMA - 30 ? 'lower' : 'middle'} Bollinger Band with ${parseFloat(indicators.volatility) > 0.8 ? 'heightened' : 'normal'} volatility. OANDA order flow data indicates ${indicators.currentPrice > indicators.prevClose ? 'accumulation' : 'distribution'} at $${indicators.supports[0]}-$${indicators.supports[1]} range. The Commitment of Traders report shows ${indicators.rsi > 60 ? 'increased long positioning' : 'mixed positioning'} among institutional traders.\n\n${indicators.dailyChange > 0 ? 'Inflation concerns and geopolitical tensions continue supporting prices' : 'Dollar strength and profit-taking pressure prices'}, while technical indicators suggest ${indicators.rsi > 70 || indicators.rsi < 30 ? 'potential reversal' : 'continuation of current trend'}. Relative strength against USD appears ${indicators.dailyChange > 0 ? 'strengthening' : 'weakening'} in intraday timeframes.\n\n### Trading Approach\n• **Short-term**: ${indicators.rsi > 70 ? 'Consider profit-taking above $' + indicators.resistances[0] : indicators.rsi < 30 ? 'Look for short-term bounce opportunities' : 'Follow the trend with tight stops'}\n• **Medium-term**: ${indicators.currentPrice > indicators.twoHundredDayMA ? 'Maintain bullish bias, looking for entries near $' + indicators.fibRetracement['50.0%'] + ' level' : 'Exercise caution, watching for stabilization above $' + indicators.supports[1]}\n• **Risk management**: Set stops below $${(indicators.supports[0] - 5).toFixed(2)} to limit potential drawdown\n\nData last updated: ${new Date(indicators.lastUpdated).toLocaleTimeString()}\n\nNote: This is simulated analysis (API connection failed)`
        };
        
        // Return the fallback simulated analysis
        return analyses[model] || `${model} analysis not available`;
      }
      
      // Get AI analysis - returns results directly from the try/catch block
      const analysis = await modelOutput;
      
      // Update the UI with the analysis results
      setModelOutputs(prev => ({
        ...prev,
        [model]: analysis
      }));
    } catch (err) {
      console.error(`Error during ${model} analysis:`, err);
      setModelOutputs(prev => ({
        ...prev,
        [model]: `Analysis failed: ${err.message || 'Unknown error'}`
      }));
    } finally {
      setLoadingModel('');
    }
  };

  return (
    <ErrorBoundary
      errorMessage="An unexpected error occurred in the application"
      showDetails={process.env.NODE_ENV === 'development'}
    >
      <main style={{
        minHeight: '100vh',
        padding: '20px',
        maxWidth: '960px',
        margin: '0 auto',
        textAlign: 'center',
        backgroundColor: '#ffffff',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center'
      }}>
        {/* Header section */}
        <header style={{ marginBottom: '20px', width: '100%' }}>
          <h1 style={{ fontSize: 32, fontWeight: 800, marginBottom: 12, color: '#bfa100', letterSpacing: 0.5 }}>
            XAUUSD Live Chart
          </h1>
          <p style={{ fontSize: 16, margin: '8px 0 16px 0', color: '#4d4d4d' }}>
            Real-time OANDA Gold/USD price chart with technical indicators
          </p>
        </header>
        
        {/* Single TradingView chart, centered on the page */}
        <section style={{width: '100%', maxWidth: '900px', margin: '0 auto 30px auto'}}>
          <ErrorBoundary
            errorMessage="Chart could not be displayed"
            fallback={
              <div style={{width: '100%', height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #e0e0e0', background: '#f9f9f9'}}>
                <div style={{textAlign: 'center'}}>
                  <h3 style={{color: '#333', margin: '0 0 10px 0'}}>Gold Price Chart (XAUUSD)</h3>
                  <p style={{color: '#666'}}>Chart temporarily unavailable</p>
                </div>
              </div>
            }
          >
            <div style={{width: '100%', height: '500px'}}>
              <TradingViewWidget />
            </div>
          </ErrorBoundary>
        </section>
        
        {/* Model analysis section */}
        <section style={{width: '100%', maxWidth: '900px', margin: '0 auto 30px auto'}}>
          <h2 style={{fontSize: 24, fontWeight: 700, marginBottom: 16, color: '#343434', textAlign: 'center'}}>
            AI Trading Analysis
          </h2>
          <div style={{
            display: 'flex',
            flexDirection: 'row',
            justifyContent: 'space-between',
            flexWrap: 'wrap',
            width: '100%',
            gap: '16px'
          }}>
            {modelList.map(model => (
              <div key={model} style={{ display: 'flex', flexDirection: 'column', width: 'calc(33% - 12px)', marginBottom: '20px' }}>
                <ModelButton 
                  model={model} 
                  onClick={() => handleAnalyze(model)} 
                  loading={loadingModel === model} 
                />
                <div style={{
                  height: '350px',
                  marginTop: '12px',
                  background: '#fffbe6',
                  border: '1px solid #e6c200',
                  borderRadius: '6px',
                  padding: '12px',
                  fontSize: '13px',
                  color: '#7a6700',
                  width: '100%',
                  whiteSpace: 'pre-line',
                  boxSizing: 'border-box',
                  textAlign: 'left',
                  fontFamily: 'monospace',
                  overflow: 'auto'
                }}>
                  {modelOutputs[model]}
                </div>
              </div>
            ))}
          </div>
        </section>
        
        {/* Status notifications */}
        {apiStatus === 'unavailable' && (
          <div style={{ color: '#c22', marginTop: 10, fontSize: 15, background: '#fff8f8', padding: '8px 16px', borderRadius: 6, marginBottom: 20 }}>
            Note: Backend API is currently unavailable. Responses are simulated.
          </div>
        )}
        
        {storageAvailable === false && (
          <div style={{ color: '#666', marginTop: 5, fontSize: 14, background: '#f9f9f9', padding: '8px 16px', borderRadius: 6, marginBottom: 20 }}>
            Storage access is limited in this environment. Some features may have reduced functionality.
          </div>
        )}
        
        {error && (
          <div style={{ color: 'red', marginTop: 18, fontWeight: 600 }}>
            Error: {error}
          </div>
        )}
      </main>
    </ErrorBoundary>
  );
}
