import { useEffect, useState } from 'react';

export default function TradingViewWidget() {
  const [widgetError, setWidgetError] = useState(false);
  useEffect(() => {
    if (typeof window === 'undefined') {
      setWidgetError(true);
      return;
    }
    try {
      if (!document.getElementById('tradingview-widget-script')) {
        const script = document.createElement('script');
        script.id = 'tradingview-widget-script';
        script.src = 'https://s3.tradingview.com/tv.js';
        script.async = true;
        script.onerror = () => {
          setWidgetError(true);
          console.error('TradingView script failed to load.');
        };
        document.body.appendChild(script);
      }
      window.TradingViewWidgetTimer = setTimeout(() => {
        if (window.TradingView) {
          try {
            new window.TradingView.widget({
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
            });
            setWidgetError(false);
          } catch (err) {
            setWidgetError(true);
            console.error('TradingView widget failed to initialize:', err);
          }
        } else {
          setWidgetError(true);
          console.error('TradingView global object not found.');
        }
      }, 700);
    } catch (err) {
      setWidgetError(true);
      console.error('TradingViewWidget error:', err);
    }
    return () => {
      if (window.TradingViewWidgetTimer) clearTimeout(window.TradingViewWidgetTimer);
    };
  }, []);

  return (
    <div>
      <h2>Gold Price Chart (OANDA: XAUUSD)</h2>
      <div id="tradingview_xauusd" style={{ width: 800, height: 400, marginBottom: 24, border: '1px solid #ccc', background: '#f9f9f9', display: widgetError ? 'none' : undefined }} />
      {widgetError && (
        <div style={{ color: 'red', fontWeight: 'bold', marginTop: 12 }}>
          Unable to load TradingView chart. Please check your internet connection or try again later.
        </div>
      )}
    </div>
  );
}
