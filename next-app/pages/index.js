import React, { useState, useEffect, useRef } from 'react';
import dynamic from 'next/dynamic';
import ModelButton from '../components/ModelButton';
import MarketOverview from '../components/MarketOverview';
import { isStorageAvailable } from '../utils/storage';
import { useMarketDataStream } from '../lib/socketClient';

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
  const [isUsingWebSocket, setIsUsingWebSocket] = useState(false);
  
  // Socket.IO connection for real-time market data
  const {
    isConnected: wsConnected,
    priceData: wsMarketData,
    error: wsError,
    reconnect: wsReconnect
  } = useMarketDataStream('XAU_USD');
  
  // Model definitions
  const modelList = ['GPT-4.1', 'Claude 3.7', 'Perplexity Pro'];
  const modelDescriptions = {
    'GPT-4.1': "OpenAI's latest GPT model, tuned for financial and technical analysis.",
    'Claude 3.7': "Anthropic's Claude, specialized for reasoning and market narratives.",
    'Perplexity Pro': "Perplexity's Pro AI, focused on rapid, data-driven market insights."
  };

  // Function to check API availability
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
        return true;
      } else {
        console.log('Backend API is unhealthy');
        return false;
      }
    } catch (err) {
      console.warn('Backend API is unreachable:', err);
      return false;
    }
  };
  
  // Check environment conditions and initialize data fetching
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
    
    // Check API and set up data fetching
    console.log('Starting API availability check...');
    checkApi()
      .then(isAvailable => {
        setApiStatus(isAvailable ? 'available' : 'unavailable');
        console.log('API status:', isAvailable ? 'available' : 'unavailable');

        // If API unavailable, use fallback data
        if (!isAvailable) {
          setMarketData(fallbackMarketData());
          return;
        }

        // Then initiate the market data fetch as a backup
        fetchRealTimeData();
        
        // Start the data refresh interval (every 20 seconds) as a backup to WebSockets
        const interval = setInterval(() => {
          if (!isUsingWebSocket) {
            console.log('Refreshing market data via HTTP...');
            fetchRealTimeData();
          }
        }, 20000);
        
        return () => clearInterval(interval);
      })
      .catch(err => {
        console.error('Error during API check:', err);
        setApiStatus('unavailable');
        setMarketData(fallbackMarketData());
      });
  }, [isUsingWebSocket]);
  
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
  }, []);
  
  // Update market data from WebSocket stream
  useEffect(() => {
    if (wsMarketData) {
      console.log('Received real-time WebSocket data:', wsMarketData);
      setIsUsingWebSocket(true);
      
      // Calculate average of bid and ask for the current price
      const currentPrice = wsMarketData.bid && wsMarketData.ask ? 
        (wsMarketData.bid + wsMarketData.ask) / 2 : 
        (wsMarketData.midPrice || wsMarketData.bid || wsMarketData.ask || 0);
      
      // Create a standardized data structure from WebSocket data
      const processedData = {
        currentPrice: Number(currentPrice.toFixed(2)) || 0,
        dayHigh: marketData?.dayHigh || currentPrice + 2,
        dayLow: marketData?.dayLow || currentPrice - 2,
        dailyChange: marketData?.dailyChange || 0.1,
        open: marketData?.open || currentPrice - 0.5,
        previousClose: marketData?.previousClose || currentPrice - 0.7,
        volume: marketData?.volume || 15000,
        rsi: marketData?.rsi || 50,
        macd: marketData?.macd || 0,
        signal: marketData?.signal || 0,
        trend: marketData?.trend || 'Neutral',
        volatility: marketData?.volatility || 0.5,
        fiftyDayMA: marketData?.fiftyDayMA || currentPrice - 5,
        twoHundredDayMA: marketData?.twoHundredDayMA || currentPrice - 10,
        supports: marketData?.supports || [currentPrice - 5, currentPrice - 10, currentPrice - 15],
        resistances: marketData?.resistances || [currentPrice + 5, currentPrice + 10, currentPrice + 15],
        // WebSocket specific data
        spread: wsMarketData.spread || 0,
        bid: wsMarketData.bid || 0,
        ask: wsMarketData.ask || 0,
        lastUpdated: new Date().toLocaleTimeString(),
        isRealtime: true
      };
      
      // Update state with the processed data
      setMarketData(processedData);
    }
  }, [wsMarketData]);
  
  // Handle WebSocket errors
  useEffect(() => {
    if (wsError) {
      console.error('WebSocket error:', wsError);
      setIsUsingWebSocket(false);
      
      // If we don't have market data yet, fetch it via HTTP
      if (!marketData) {
        fetchRealTimeData();
      }
    }
  }, [wsError]);

  // Connection status effect
  useEffect(() => {
    console.log('WebSocket connection status:', wsConnected ? 'Connected' : 'Disconnected');
    if (wsConnected) {
      setApiStatus('available');
    }
  }, [wsConnected]);

  // Fetch real-time XAUUSD data from the Next.js API proxy (HTTP fallback)
  const fetchRealTimeData = async () => {
    try {
      console.log('Fetching real-time market data via HTTP...');
      const startTime = Date.now();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5050';
      const response = await fetch(`${apiUrl}/api/market-data`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });
      
      // Check if the request was successful
      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }
      
      const responseData = await response.json();
      console.log(`Market data fetch completed in ${Date.now() - startTime}ms`);
      
      // Check if we have valid data
      if (responseData && responseData.status === 'ok') {
        const { current_price, day_high, day_low, daily_change, open, close, volume, market_data } = responseData;
        
        // Calculate indicators from the data
        const indicators = market_data.indicators || {};
        
        // Create a standardized data structure for the UI
        const processedData = {
          currentPrice: Number(current_price) || 0,
          dayHigh: Number(day_high) || 0,
          dayLow: Number(day_low) || 0,
          dailyChange: Number(daily_change) || 0,
          open: Number(open) || 0,
          previousClose: Number(close) || 0,
          volume: Number(volume) || 0,
          rsi: Number(indicators.rsi) || 50,
          macd: Number(indicators.macd) || 0,
          signal: Number(indicators.signal) || 0,
          trend: indicators.trend || 'Neutral',
          volatility: Number(indicators.volatility) || 0.5,
          fiftyDayMA: Number(indicators.ma_50) || 0,
          twoHundredDayMA: Number(indicators.ma_200) || 0,
          supports: indicators.support_levels || [0, 0, 0],
          resistances: indicators.resistance_levels || [0, 0, 0],
          isRealtime: false
        };
        
        // Only update state if we're not using WebSockets
        if (!isUsingWebSocket) {
          setMarketData(processedData);
        }
        return processedData;
      } else {
        console.error('Invalid market data structure:', responseData);
        throw new Error('Invalid market data structure');
      }
    } catch (error) {
      console.error('Error fetching market data via HTTP:', error);
      // Use fallback data if API call fails and we're not using WebSockets
      if (!isUsingWebSocket) {
        const fallbackData = fallbackMarketData();
        setMarketData(fallbackData);
        return fallbackData;
      }
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

  // Create button to load the selected model
  const handleModelSelect = (model) => {
    // First clear old output
    setModelOutputs({});
    setLoadingModel(model);
    handleAnalyze(model);
  };
  
  // Debug function to manually update a model output for testing
  const debugSetOutput = (model, text) => {
    console.log(`Debug setting output for ${model} to: ${text}`);
    setModelOutputs(prev => ({
      ...prev,
      [model]: text
    }));
  };

  // Handle model analysis with real-time data
  const handleAnalyze = async (model) => {
    try {
      console.log(`handleAnalyze called for model: ${model}`);
      
      // Clear previous output and show loading state
      setLoadingModel(model);
      setModelOutputs(prev => {
        const newOutputs = {
          ...prev,
          [model]: 'Fetching real-time OANDA XAUUSD data...'
        };
        console.log('Setting initial loading message:', newOutputs);
        return newOutputs;
      });
      
      // First, get the latest market data
      console.log('Getting latest data for analysis...');
      const latestData = await fetchRealTimeData();
      console.log('Latest market data fetched successfully:', latestData);
      
      // Make sure we have valid market data before proceeding
      if (!latestData || !latestData.currentPrice) {
        console.error('Invalid market data returned from fetchRealTimeData():', latestData);
        throw new Error('Failed to get valid market data for analysis');
      }
      
      // Format date and time for analysis
      const date = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      const time = new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      
      try {
        // Map the frontend model name to the Next.js API endpoint
        let apiModel = '';
        if (model === 'GPT-4.1') {
          apiModel = 'openai';
        } else if (model === 'Claude 3.7') {
          apiModel = 'anthropic';
        } else if (model === 'Perplexity Pro') {
          apiModel = 'perplexity';
        }
        
        console.log(`Requesting AI analysis from ${apiModel} model via Next.js API proxy...`);
        
        // Create request payload with market data - ensure all values are proper types
        const payload = {
          market_data: {
            currentPrice: parseFloat(latestData.currentPrice) || 2300.0,
            dayHigh: parseFloat(latestData.dayHigh) || 2310.0,
            dayLow: parseFloat(latestData.dayLow) || 2290.0,
            dailyChange: parseFloat(latestData.dailyChange) || 0.2,
            open: parseFloat(latestData.open) || 2295.0,
            previousClose: parseFloat(latestData.previousClose) || 2290.0,
            volume: parseInt(latestData.volume || 15000, 10),
            rsi: parseFloat(latestData.indicators?.rsi || 50),
            macd: parseFloat(latestData.indicators?.macd || 0),
            signal: parseFloat(latestData.indicators?.signal || 0),
            trend: String(latestData.indicators?.trend || 'Neutral'),
            volatility: parseFloat(latestData.indicators?.volatility || 0.5),
            fiftyDayMA: parseFloat(latestData.indicators?.fiftyDayMA || (latestData.currentPrice * 0.98)),
            twoHundredDayMA: parseFloat(latestData.indicators?.twoHundredDayMA || (latestData.currentPrice * 0.95)),
            supports: Array.isArray(latestData.indicators?.supports) ? latestData.indicators.supports.map(s => parseFloat(s)) : [
              parseFloat((latestData.dayLow - 5).toFixed(2)),
              parseFloat((latestData.dayLow - 10).toFixed(2)),
              parseFloat((latestData.dayLow - 15).toFixed(2))
            ],
            resistances: Array.isArray(latestData.indicators?.resistances) ? latestData.indicators.resistances.map(r => parseFloat(r)) : [
              parseFloat((latestData.dayHigh + 5).toFixed(2)),
              parseFloat((latestData.dayHigh + 10).toFixed(2)),
              parseFloat((latestData.dayHigh + 15).toFixed(2))
            ]
          }
        };
        
        // Verify payload has valid values
        console.log('Analysis payload created:', JSON.stringify(payload, null, 2));
        
        // Make real API request for AI analysis
        console.log(`Sending ${apiModel} analysis request to local Next.js API: /api/analyze/${apiModel}`);
        
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 30000);
        
        // Use Next.js API routes instead of direct calls to Flask backend
        // This avoids cross-origin issues and handles IPv6/IPv4 differences
        const response = await fetch(`/api/analyze/${apiModel}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          },
          body: JSON.stringify(payload),
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          throw new Error(`API request failed with status ${response.status}`);
        }
        
        const analysisData = await response.json();
        console.log('AI Analysis response:', analysisData);
        
        // Check if we got a valid response
        if (analysisData.analysis) {
          // Use the actual AI-generated analysis from the API
          const modelOutput = analysisData.analysis;
          console.log(`Successfully received ${model} analysis from API`);
          
          // Add timestamp to the analysis
          const formattedOutput = `${modelOutput}\n\nData analyzed at ${date} ${time}`;
          
          // Update the UI with the analysis
          setModelOutputs(prev => ({
            ...prev,
            [model]: formattedOutput
          }));
          
          // Set analyzing state to false
          setLoadingModel('');
          
          return formattedOutput;
        }
        
        // If API returned empty analysis, throw error
        console.warn('API returned empty analysis');
        throw new Error('Invalid or empty analysis from API');
        
      } catch (analysisError) {
        console.error(`[ERROR] Failed to get ${model} analysis from API:`, analysisError);
        console.error(`[ERROR] Error message: ${analysisError.message}`);
        console.error(`[ERROR] Error stack: ${analysisError.stack}`);
        
        // Get detailed error info if available
        let errorMessage = `Error loading ${model} analysis. Please try again.`;
        if (analysisError.response && analysisError.response.data) {
          errorMessage += ` Server message: ${analysisError.response.data.error || 'Unknown error'}`;
        } else {
          errorMessage += ` (${analysisError.message})`;
        }
        
        // Update UI with error and show fallback analysis
        setModelOutputs(prev => ({
          ...prev,
          [model]: errorMessage
        }));
        
        // FALLBACK: Generate model-specific analysis if API fails
        console.log('Using fallback analysis generation...');
        
        // Generate fallback analysis based on model type
        const trendEmoji = latestData.trend === 'Bullish' ? '📈' : latestData.trend === 'Bearish' ? '📉' : '➡️';
        
        let fallbackAnalysis = '';
        if (model === 'GPT-4.1') {
          fallbackAnalysis = `${trendEmoji} XAUUSD Technical Analysis (Simulated) - ${date} at ${time}\n\nCurrent Price: $${latestData.currentPrice.toFixed(2)} (${latestData.dailyChange}% daily change)\n\nKey Indicators:\n- RSI(14): ${latestData.indicators.rsi.toFixed(2)} (${latestData.indicators.rsi > 70 ? 'Overbought' : latestData.indicators.rsi < 30 ? 'Oversold' : 'Neutral'})\n- MACD: ${latestData.indicators.macd.toFixed(2)} / Signal: ${latestData.indicators.signal.toFixed(2)} (${latestData.indicators.macd > latestData.indicators.signal ? 'Bullish' : 'Bearish'} momentum)\n\nNote: Using fallback analysis due to API error: ${analysisError.message}`;
        } else if (model === 'Claude 3.7') {
          fallbackAnalysis = `OANDA XAUUSD Analysis - ${date}\n\nPrice Action Summary (${time}):\nXAUSDU is currently trading at $${latestData.currentPrice.toFixed(2)}, with daily range of $${latestData.dayLow.toFixed(2)}-$${latestData.dayHigh.toFixed(2)}.\n\nNote: Using fallback analysis due to API error: ${analysisError.message}`;
        } else {
          fallbackAnalysis = `## XAUUSD OANDA Technical Analysis\nTimestamp: ${date} ${time}\n\n### Current Market Status\n• Price: $${latestData.currentPrice.toFixed(2)}\n• 24h Change: ${latestData.dailyChange}%\n\nNote: Using fallback analysis due to API error: ${analysisError.message}`;
        }
        
        // Update UI with fallback analysis
        setModelOutputs(prev => ({
          ...prev,
          [model]: fallbackAnalysis
        }));
        
        // Reset loading state
        setLoadingModel('');
      }
    } catch (error) {
      console.error(`Error generating ${model} analysis:`, error);
      
      // Update UI to show error
      setModelOutputs(prev => ({
        ...prev,
        [model]: `Error generating ${model} analysis: ${error.message}`
      }));
      
      // Reset loading state
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
        
        {/* Market Overview */}
        <MarketOverview data={marketData} status={apiStatus} />
        
        {/* WebSocket Status */}
        <div style={{ display: 'flex', marginTop: '10px', justifyContent: 'space-between', alignItems: 'center', padding: '10px', background: wsConnected ? '#f0f8ff' : '#fffdfa', border: `1px solid ${wsConnected ? '#c8e1ff' : '#ffeeba'}`, borderRadius: '4px' }}>
          <div>
            <span style={{ fontWeight: 'bold', color: wsConnected ? '#0366d6' : '#856404' }}>
              Data Source: {isUsingWebSocket ? 'Real-time WebSocket' : 'REST API (Polling)'}
            </span>
            <span style={{ marginLeft: '10px', fontSize: '13px', color: '#666' }}>
              {marketData?.lastUpdated ? `Last update: ${marketData.lastUpdated}` : ''}
            </span>
          </div>
          
          {!wsConnected && (
            <button 
              onClick={wsReconnect}
              style={{ padding: '5px 10px', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
            >
              Reconnect WebSocket
            </button>
          )}
        </div>
        
        {/* TradingView Chart */}
        <div style={{marginTop: '20px', border: '1px solid #e0e0e0', borderRadius: '8px', overflow: 'hidden'}}>
          <ErrorBoundary fallback={<div style={{padding: 20}}>Chart could not be loaded</div>}>
            <TradingViewWidget />
          </ErrorBoundary>
        </div>
        
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
                  overflow: 'auto',
                  position: 'relative'
                }}>
                  {modelOutputs[model]}
                  
                  {/* Add a small debug indicator showing length of content */}
                  <div style={{
                    position: 'absolute',
                    bottom: '4px',
                    right: '4px',
                    background: '#fffbe6',
                    fontSize: '10px',
                    padding: '2px 4px',
                    border: '1px solid #e6c200',
                    borderRadius: '4px',
                    color: '#7a6700',
                    opacity: 0.8
                  }}>
                    {modelOutputs[model] ? modelOutputs[model].length : 0} chars
                  </div>
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
        
        {/* Debug button row (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <div style={{ display: 'flex', gap: '10px', marginTop: '10px', marginBottom: '10px' }}>
            <button 
              onClick={() => debugSetOutput('GPT-4.1', 'This is a test output for GPT-4.1')}
              style={{ padding: '5px 10px', background: '#eee', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              Test GPT Output
            </button>
            <button 
              onClick={() => debugSetOutput('Claude 3.7', 'This is a test output for Claude 3.7')}
              style={{ padding: '5px 10px', background: '#eee', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              Test Claude Output
            </button>
            <button 
              onClick={() => debugSetOutput('Perplexity Pro', 'This is a test output for Perplexity Pro')}
              style={{ padding: '5px 10px', background: '#eee', border: '1px solid #ccc', borderRadius: '4px' }}
            >
              Test Perplexity Output
            </button>
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
