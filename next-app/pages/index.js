import React from 'react';

// Simple emergency fallback page that should work regardless of environment
export default function Home() {
  const [modelOutputs, setModelOutputs] = React.useState({
    'GPT-4.1': '',
    'Claude 3.7': '',
    'Perplexity Pro': '',
  });
  
  const [loadingModel, setLoadingModel] = React.useState('');

  // Chart placeholder instead of TradingView widget
  const ChartPlaceholder = () => (
    <div style={{width: '100%', maxWidth: 800, height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid #e0e0e0', background: '#f9f9f9', margin: '0 0 32px 0'}}>
      <div style={{textAlign: 'center'}}>
        <h3 style={{color: '#333', margin: '0 0 10px 0'}}>Gold Price Chart (XAUUSD)</h3>
        <p style={{color: '#666'}}>TradingView chart temporarily unavailable</p>
        <p style={{color: '#666', fontSize: '14px'}}>The app is functioning normally without the chart</p>
      </div>
    </div>
  );

  // Simple button component instead of importing ModelButton
  const Button = ({ model, onClick, loading }) => (
    <button
      onClick={onClick}
      disabled={loading}
      style={{
        margin: '0 0 10px 0',
        padding: '12px 20px',
        fontSize: 16,
        background: '#ffd700',
        border: '1px solid #c9b037',
        borderRadius: 8,
        cursor: loading ? 'wait' : 'pointer',
        opacity: loading ? 0.6 : 1,
        fontWeight: 'bold',
        color: '#333',
      }}
    >
      Analyze with {model}
    </button>
  );

  const handleAnalyze = async (model) => {
    setLoadingModel(model);
    setModelOutputs(outputs => ({ ...outputs, [model]: '' }));
    
    try {
      setTimeout(() => {
        // Simulate API response - no actual fetch calls
        setModelOutputs(outputs => ({ 
          ...outputs, 
          [model]: "This is a simulated response. The backend API is not connected, but the UI is working properly."
        }));
        setLoadingModel('');
      }, 1500);
    } catch (err) {
      console.error('Analysis error:', err);
      setModelOutputs(outputs => ({
        ...outputs,
        [model]: `Could not complete analysis: ${err.message || err.toString()}`
      }));
      setLoadingModel('');
    }
  };

  const modelList = ['GPT-4.1', 'Claude 3.7', 'Perplexity Pro'];
  
  const modelDescriptions = {
    'GPT-4.1': "OpenAI's latest GPT model, tuned for financial and technical analysis.",
    'Claude 3.7': "Anthropic's Claude, specialized for reasoning and market narratives.",
    'Perplexity Pro': "Perplexity's Pro AI, focused on rapid, data-driven market insights."
  };

  console.log('Rendering minimal Home component');

  return (
    <div style={{
      padding: 0,
      margin: 0,
      fontFamily: 'system-ui, sans-serif',
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
        <div style={{ margin: '0 0 24px 0', textAlign: 'left', color: '#222', fontSize: 15, paddingLeft: 20 }}>
          <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
            {modelList.map(model => (
              <li key={model} style={{marginBottom: 8}}>
                <b>{model}</b>: {modelDescriptions[model]}
              </li>
            ))}
          </ul>
        </div>
      </div>
      
      <ChartPlaceholder />
      
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
            <Button 
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
              fontFamily: 'monospace',
            }}>
              {modelOutputs[model]}
            </div>
          </div>
        ))}
      </div>
      
      <div style={{marginTop: 20, marginBottom: 40, color: '#666', fontSize: 14, textAlign: 'center', maxWidth: 600}}>
        <p>Note: This is running in emergency mode without TradingView integration or backend API connection.</p>
        <p>UI is displaying correctly. After clicking a model button, you'll see a simulated response.</p>
      </div>
    </div>
  );
}
