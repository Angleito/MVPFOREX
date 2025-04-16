import { useEffect, useState, useRef } from 'react';
import { isStorageAvailable } from '../utils/storage';

/**
 * Enhanced TradingView Widget with comprehensive error handling
 * - Safely loads TradingView script
 * - Handles storage access errors gracefully
 * - Provides fallback UI when chart can't load
 * - Cleans up resources properly
 */
export default function TradingViewWidget() {
  const [status, setStatus] = useState('loading'); // loading, ready, error
  const [errorMessage, setErrorMessage] = useState('');
  const containerRef = useRef(null);
  const widgetRef = useRef(null);
  
  // Function to safely create the widget
  const createWidget = () => {
    try {
      if (!window.TradingView) {
        setStatus('error');
        setErrorMessage('TradingView library not loaded');
        return false;
      }

      if (!document.getElementById('tradingview_xauusd')) {
        setStatus('error');
        setErrorMessage('Chart container not found');
        return false;
      }

      // Create widget with storage error prevention
      widgetRef.current = new window.TradingView.widget({
        width: 800,
        height: 400,
        symbol: 'OANDA:XAUUSD',
        interval: '60',
        timezone: 'Etc/UTC',
        theme: 'light',
        style: '1',
        locale: 'en',
        toolbar_bg: '#f1f3f6',
        enable_publishing: false,
        allow_symbol_change: false,
        hide_top_toolbar: false,
        hide_legend: false,
        container_id: 'tradingview_xauusd',
        // Handle initialization errors
        disabled_features: ['storage_adapter'],
        save_image: false,
        autosize: false,
      });
      
      setStatus('ready');
      return true;
    } catch (err) {
      console.error('TradingView widget creation error:', err);
      setStatus('error');
      setErrorMessage(err.message || 'Failed to initialize chart');
      return false;
    }
  };

  // Main initialization effect
  useEffect(() => {
    // Skip on server
    if (typeof window === 'undefined') {
      return;
    }
    
    let scriptLoaded = false;
    let scriptElement = null;
    let initTimeout = null;
    let storageAvailable = false;
    
    // Check storage availability
    try {
      storageAvailable = isStorageAvailable();
      console.log('Storage availability check:', storageAvailable);
    } catch (e) {
      console.warn('Storage check failed:', e);
    }
    
    // Create and load script
    const loadScript = () => {
      try {
        // Check if script already exists
        scriptElement = document.getElementById('tradingview-widget-script');
        if (!scriptElement) {
          scriptElement = document.createElement('script');
          scriptElement.id = 'tradingview-widget-script';
          scriptElement.src = 'https://s3.tradingview.com/tv.js';
          scriptElement.async = true;
          
          // Handle load errors
          scriptElement.onerror = (e) => {
            console.error('TradingView script failed to load:', e);
            setStatus('error');
            setErrorMessage('Failed to load TradingView library');
            scriptLoaded = false;
          };
          
          // Handle successful load
          scriptElement.onload = () => {
            console.log('TradingView script loaded successfully');
            scriptLoaded = true;
            
            // Initialize widget after script is ready
            initTimeout = setTimeout(() => {
              createWidget();
            }, 500);
          };
          
          document.body.appendChild(scriptElement);
        } else {
          // Script already exists, try to initialize widget directly
          if (window.TradingView) {
            scriptLoaded = true;
            createWidget();
          } else {
            // Wait for existing script to load
            initTimeout = setTimeout(() => {
              if (window.TradingView) {
                createWidget();
              } else {
                setStatus('error');
                setErrorMessage('TradingView not available after timeout');
              }
            }, 2000);
          }
        }
      } catch (err) {
        console.error('Script loading error:', err);
        setStatus('error');
        setErrorMessage('Error loading chart dependencies');
      }
    };
    
    // Initialize
    if (!storageAvailable) {
      console.warn('Storage not available - providing fallback chart experience');
    }
    
    loadScript();
    
    // Cleanup
    return () => {
      if (initTimeout) clearTimeout(initTimeout);
      // Only remove script if we created it
      if (scriptElement && !scriptElement.parentNode) {
        document.body.removeChild(scriptElement);
      }
      // Clean up widget if created
      if (widgetRef.current) {
        try {
          if (widgetRef.current.remove) {
            widgetRef.current.remove();
          }
        } catch (e) {
          console.warn('Error cleaning up widget:', e);
        }
      }
    };
  }, []);
  
  // Render appropriate UI based on status
  return (
    <div ref={containerRef} style={{ width: 800, margin: '0 auto 20px auto' }}>
      <h2 style={{ fontSize: 24, fontWeight: 600, textAlign: 'center', margin: '0 0 15px 0', color: '#333' }}>
        Gold Price Chart (OANDA: XAUUSD)
      </h2>
      
      {/* Chart container - hidden when in error state */}
      <div 
        id="tradingview_xauusd" 
        style={{ 
          width: 800, 
          height: 400, 
          border: '1px solid #ddd', 
          background: '#f9f9f9', 
          display: status === 'error' ? 'none' : 'block',
          borderRadius: 4,
        }} 
      />
      
      {/* Loading state */}
      {status === 'loading' && (
        <div style={{ 
          position: 'absolute', 
          top: 0, 
          left: 0, 
          width: '100%', 
          height: '100%', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          background: 'rgba(255,255,255,0.8)',
          zIndex: 1,
        }}>
          <div style={{ textAlign: 'center' }}>
            <p style={{ color: '#666' }}>Loading gold price chart...</p>
          </div>
        </div>
      )}
      
      {/* Error state */}
      {status === 'error' && (
        <div style={{ 
          width: 800, 
          height: 400, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          background: '#f9f9f9', 
          border: '1px solid #e0e0e0',
          borderRadius: 4,
        }}>
          <div style={{ textAlign: 'center', padding: 20 }}>
            <div style={{ color: '#d32f2f', marginBottom: 10, fontWeight: 'bold' }}>
              Chart temporarily unavailable
            </div>
            <p style={{ color: '#666', margin: '10px 0' }}>
              {errorMessage || 'Unable to load TradingView chart.'}
            </p>
            <p style={{ color: '#666', fontSize: 14, marginTop: 5 }}>
              You can still use all other features of the application.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
