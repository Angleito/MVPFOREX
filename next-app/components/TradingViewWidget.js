import React, { useEffect, useRef, memo } from 'react';

// Use dynamic import to avoid SSR issues
const TradingViewWidget = () => {
  const container = useRef(null);
  
  useEffect(() => {
    // Only run on client-side
    if (typeof window === 'undefined') return;
    
    // Clean up any existing widget
    if (container.current) {
      while (container.current.firstChild) {
        container.current.removeChild(container.current.firstChild);
      }
    }
    
    try {
      // Create widget container
      const widgetContainer = document.createElement('div');
      widgetContainer.className = 'tradingview-widget-container';
      widgetContainer.style.width = '100%';
      widgetContainer.style.height = '100%';

      // Create widget div
      const widget = document.createElement('div');
      widget.id = 'tradingview-widget-' + Math.random().toString(36).substring(2, 8); // Unique ID
      widget.style.width = '100%';
      widget.style.height = '100%';
      widgetContainer.appendChild(widget);
      
      // Append to container
      if (container.current) {
        container.current.appendChild(widgetContainer);
      }
      
      // TradingView widget configuration
      const config = {
        "autosize": true,
        "symbol": "OANDA:XAUUSD",
        "interval": "5",
        "timezone": "exchange",
        "theme": "light",
        "style": "1",
        "locale": "en",
        "enable_publishing": false,
        "gridColor": "rgba(180, 180, 180, 0.14)",
        "allow_symbol_change": false,
        "support_host": "https://www.tradingview.com",
        "calendar": false,
        "hide_volume": false,
        "support_resister": false,
        "backgroundColor": "rgba(255, 255, 255, 1)",
        "hide_side_toolbar": false,
        "studies": [
          "RSI@tv-basicstudies",
          "MACD@tv-basicstudies",
          "BB@tv-basicstudies"
        ],
        "container_id": widget.id
      };
      
      // Load TradingView script
      const script = document.createElement('script');
      script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
      script.type = 'text/javascript';
      script.async = true;
      script.innerHTML = JSON.stringify(config);
      widgetContainer.appendChild(script);
      
      console.log('TradingView widget initialized with ID:', widget.id);
    } catch (error) {
      console.error('Error initializing TradingView widget:', error);
    }

    return () => {
      // Cleanup on unmount
      if (container.current) {
        while (container.current.firstChild) {
          container.current.removeChild(container.current.firstChild);
        }
      }
    };
  }, []);

  return (
    <div 
      ref={container} 
      className="trading-view-container"
      style={{
        width: '100%',
        maxWidth: '100%',
        height: '500px',
        margin: '0 auto 32px auto',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        overflow: 'hidden',
        backgroundColor: '#fff'
      }}
    />
  );
};

// Use memo to prevent unnecessary re-renders
export default memo(TradingViewWidget);
