import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import ModelButton from '../components/ModelButton';

const TradingViewWidget = dynamic(() => import('../components/TradingViewWidget'), { ssr: false });

export default function Home() {
  const [candles, setCandles] = useState(null);
  const [error, setError] = useState(null);
  const [loadingModel, setLoadingModel] = useState('');
  const [modelOutputs, setModelOutputs] = useState({
    'AI Model 1': '',
    'AI Model 2': '',
    'AI Model 3': '',
  });


  useEffect(() => {
    fetch('/api/test-candles')
      .then(async res => {
        const text = await res.text();
        try {
          const data = JSON.parse(text);
          setCandles(data.candles);
        } catch (e) {
          setError('API did not return JSON. Raw response: ' + text.slice(0, 200));
        }
      })
      .catch(err => setError('Fetch failed: ' + err.toString()));
  }, []);

  const modelDescriptions = {
    'AI Model 1': 'LSTM Deep Learning Model: Predicts gold price movement using historical candlestick patterns.',
    'AI Model 2': 'Transformer Model: Uses attention mechanisms to analyze recent gold price volatility.',
    'AI Model 3': 'Classic ML Model: Applies traditional technical indicators for gold trend forecasting.'
  };

  const handleAnalyze = async (model) => {
    setLoadingModel(model);
    setModelOutputs(outputs => ({ ...outputs, [model]: '' }));
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model })
      });
      const data = await res.json();
      if (data.status === 'ok' && data.result) {
        setModelOutputs(outputs => ({ ...outputs, [model]: data.result }));
      } else {
        setModelOutputs(outputs => ({ ...outputs, [model]: data.error || 'Unknown error from analysis API.' }));
      }
    } catch (err) {
      setModelOutputs(outputs => ({ ...outputs, [model]: 'Network or server error: ' + err.toString() }));
    }
    setLoadingModel('');
  };

  return (
    <main style={{
      padding: 32,
      fontFamily: 'sans-serif',
      background: 'linear-gradient(135deg, #f8fafc 0%, #e6e2d3 100%)',
      minHeight: '100vh',
      color: '#222'
    }}>
      <h1 style={{ fontSize: 38, fontWeight: 700, marginBottom: 8, color: '#bfa100', letterSpacing: 1 }}>Tri-AI Analysis Tool for Gold (XAU/USD)</h1>
      <p style={{ fontSize: 18, margin: '8px 0 24px 0', maxWidth: 700 }}>
        This tool uses three different AI models to analyze gold (OANDA:XAUUSD) price action. Select a model below to analyze the latest candlestick data and receive an instant AI-powered forecast or insight.
      </p>
      <ul style={{ margin: '0 0 28px 0', padding: 0, listStyle: 'none', fontSize: 16 }}>
        <li><b>AI Model 1</b>: {modelDescriptions['AI Model 1']}</li>
        <li><b>AI Model 2</b>: {modelDescriptions['AI Model 2']}</li>
        <li><b>AI Model 3</b>: {modelDescriptions['AI Model 3']}</li>
      </ul>
      <section style={{ margin: '32px 0 24px 0' }}>
        <TradingViewWidget />
      </section>
      <div style={{ margin: '16px 0 24px 0', display: 'flex', flexDirection: 'row', gap: 16 }}>
        {['AI Model 1', 'AI Model 2', 'AI Model 3'].map(model => (
          <div key={model} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', width: 220 }}>
            <ModelButton model={model} onClick={() => handleAnalyze(model)} loading={loadingModel === model} />
            <div style={{
              minHeight: 62,
              marginTop: 8,
              background: '#fffbe6',
              border: '1px solid #e6c200',
              borderRadius: 8,
              padding: '8px 12px',
              fontSize: 15,
              color: '#7a6700',
              width: '100%',
              whiteSpace: 'pre-line',
              boxSizing: 'border-box'
            }}>
              {modelOutputs[model]}
            </div>
          </div>
        ))}
      </div>
      {error && <div style={{ color: 'red', marginTop: 16 }}>Error: {error.includes('storage') ? 'Browser storage is not available in this context. Some widgets may not work.' : error}</div>}
    </main>
  );
}
