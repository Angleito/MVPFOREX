import React, { useEffect, useRef } from 'react';

export default function TradingViewWidget() {
  const container = useRef();

  useEffect(() => {
    // Create the widget script
    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.type = 'text/javascript';
    script.async = true;
    
    // Configure the widget
    script.innerHTML = JSON.stringify({
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
      "container_id": "tradingview-widget"
    });

    // Add the widget container
    const widgetContainer = document.createElement('div');
    widgetContainer.className = 'tradingview-widget-container';
    widgetContainer.style.width = '100%';
    widgetContainer.style.height = '400px';
    widgetContainer.style.maxWidth = '800px';
    
    const widget = document.createElement('div');
    widget.id = 'tradingview-widget';
    widget.style.width = '100%';
    widget.style.height = '100%';
    
    widgetContainer.appendChild(widget);
    container.current.appendChild(widgetContainer);
    container.current.appendChild(script);

    return () => {
      // Cleanup on unmount
      while (container.current?.firstChild) {
        container.current.removeChild(container.current.firstChild);
      }
    };
  }, []);

  return (
    <div 
      ref={container} 
      style={{
        width: '100%',
        maxWidth: 800,
        height: 400,
        margin: '0 0 32px 0'
      }}
    />
  );
}
