import React, { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import ModelButton from '../components/ModelButton';
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

// Dynamically import TradingView widget with fallback and error handling
const TradingViewWidget = dynamic(
  () => import('../components/TradingViewWidget').catch(err => {
    console.error('Error importing TradingViewWidget:', err);
    // Return a simpler component that won't break the app
    return () => (
      <div style={{width: '100%', maxWidth: 800, height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #e0e0e0', background: '#f9f9f9', margin: '0 0 32px 0'}}>
        <div style={{textAlign: 'center'}}>
          <h3 style={{color: '#333', margin: '0 0 10px 0'}}>Gold Price Chart (XAUUSD)</h3>
          <p style={{color: '#666'}}>Chart could not be loaded</p>
          <p style={{color: '#666', fontSize: '14px'}}>Application is still functioning normally</p>
        </div>
      </div>
    );
  }),
  { 
    ssr: false, // Ensure this only loads client-side 
    loading: () => (
      <div style={{width: '100%', maxWidth: 800, height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #e0e0e0', background: '#f9f9f9', margin: '0 0 32px 0'}}>
        <div style={{textAlign: 'center'}}>
          <p style={{color: '#666'}}>Loading gold price chart...</p>
        </div>
      </div>
    )
  }
);

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
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const res = await fetch('/api/health', {
          method: 'GET',
          signal: controller.signal
        }).catch(() => null);
        
        clearTimeout(timeoutId);
        setApiStatus(res && res.ok ? 'available' : 'unavailable');
      } catch (err) {
        console.log('API check failed:', err);
        setApiStatus('unavailable');
      }
    };
    
    checkApi();
  }, []);

  // Handle model analysis
  const handleAnalyze = async (model) => {
    setLoadingModel(model);
    setModelOutputs(prev => ({ ...prev, [model]: '' }));
    
    // If API is definitely unavailable, use simulated response
    if (apiStatus === 'unavailable') {
      setTimeout(() => {
        setModelOutputs(prev => ({
          ...prev,
          [model]: "Backend API is currently unavailable. This is a simulated response."
        }));
        setLoadingModel('');
      }, 1000);
      return;
    }
    
    try {
      // Set up request with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 15000);
      
      // Make API request
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model }),
        signal: controller.signal
      }).catch(err => {
        if (err.name === 'AbortError') {
          throw new Error('API request timed out');
        }
        throw err;
      });
      
      clearTimeout(timeoutId);
      
      // Handle API response
      if (!res || !res.ok) {
        throw new Error(`API returned status ${res?.status || 'unknown'}`);
      }
      
      const data = await res.json();
      
      if (data.status === 'ok' && data.result) {
        setModelOutputs(prev => ({ ...prev, [model]: data.result }));
      } else {
        throw new Error(data.error || 'No result from API');
      }
    } catch (err) {
      console.error('Analysis error:', err);
      setModelOutputs(prev => ({
        ...prev,
        [model]: `Analysis failed: ${err.message || 'Unknown error'}`
      }));
      
      // Update API status if it was a connection issue
      if (err.message?.includes('timed out') || err.message?.includes('network')) {
        setApiStatus('unavailable');
      }
    } finally {
      setLoadingModel('');
    }
  };

  return (
    <ErrorBoundary 
      fallback={
        <div style={{padding: 40, textAlign: 'center'}}>
          <h2>Something went wrong with the application</h2>
          <p>Please try refreshing the page</p>
        </div>
      }
    >
      <main style={{
        padding: 0,
        margin: 0,
        fontFamily: 'Inter, system-ui, sans-serif',
        background: 'linear-gradient(135deg, #f8fafc 0%, #e6e2d3 100%)',
        minHeight: '100vh',
        color: '#1a1a1a',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}>
        <div style={{ width: '100%', maxWidth: 780, margin: '40px auto 0 auto', textAlign: 'center' }}>
          <h1 style={{ fontSize: 34, fontWeight: 800, marginBottom: 8, color: '#bfa100', letterSpacing: 0.5 }}>
            XAUUSD Analysis - GPT-4.1, Claude 3.7 & Perplexity Pro
          </h1>
          <p style={{ fontSize: 18, margin: '8px 0 24px 0', color: '#4d4d4d' }}>
            Instantly analyze gold (OANDA:XAUUSD) market conditions using three top AI models.
          </p>
          <div style={{ margin: '0 0 24px 0', textAlign: 'left', color: '#222', fontSize: 15 }}>
            <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
              {modelList.map(model => (
                <li key={model} style={{marginBottom: 8}}>
                  <b>{model}</b>: {modelDescriptions[model]}
                </li>
              ))}
            </ul>
          </div>
        </div>
        
        {/* TradingView chart section with error boundary */}
        <ErrorBoundary
          errorMessage="Chart could not be displayed, but other features are still available"
          fallback={
            <div style={{width: '100%', maxWidth: 800, height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #e0e0e0', background: '#f9f9f9', margin: '0 0 32px 0'}}>
              <div style={{textAlign: 'center'}}>
                <h3 style={{color: '#333', margin: '0 0 10px 0'}}>Gold Price Chart (XAUUSD)</h3>
                <p style={{color: '#666'}}>Chart temporarily unavailable</p>
              </div>
            </div>
          }
        >
          <TradingViewWidget />
        </ErrorBoundary>
        
        {/* Model buttons section */}
        <div style={{
          margin: '16px 0 24px 0',
          display: 'flex',
          flexDirection: 'row',
          gap: 32,
          justifyContent: 'center',
          flexWrap: 'wrap',
          width: '100%',
          maxWidth: 800
        }}>
          {modelList.map(model => (
            <div key={model} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 240, margin: '0 0 20px 0' }}>
              <ModelButton 
                model={model} 
                onClick={() => handleAnalyze(model)} 
                loading={loadingModel === model} 
              />
              <div style={{
                minHeight: 68,
                marginTop: 10,
                background: '#fffbe6',
                border: '1px solid #e6c200',
                borderRadius: 10,
                padding: '10px 14px',
                fontSize: 16,
                color: '#7a6700',
                width: '100%',
                whiteSpace: 'pre-line',
                boxSizing: 'border-box',
                textAlign: 'left',
                fontFamily: 'Menlo, monospace',
              }}>
                {modelOutputs[model]}
              </div>
            </div>
          ))}
        </div>
        
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
