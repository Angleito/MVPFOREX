import React, { useState, useEffect } from 'react';
import TradingViewWidget from './TradingViewWidget';

export default function MarketOverview({ symbol = 'EURUSD' }) {
  const [marketData, setMarketData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        const response = await fetch(`/api/market-data?symbol=${symbol}`);
        if (!response.ok) {
          throw new Error('Failed to fetch market data');
        }
        const data = await response.json();
        setMarketData(data);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching market data:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchMarketData();
    // Refresh data every minute
    const interval = setInterval(fetchMarketData, 60000);
    return () => clearInterval(interval);
  }, [symbol]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '20px' }}>
        Loading market data...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        color: '#991b1b',
        background: '#fee2e2',
        padding: '16px',
        borderRadius: '8px',
        textAlign: 'center'
      }}>
        {error}
      </div>
    );
  }

  return (
    <div style={{
      background: '#fff',
      borderRadius: '12px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      padding: '24px',
      marginBottom: '32px'
    }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '24px',
        marginBottom: '24px'
      }}>
        <InfoCard
          title="Current Price"
          value={marketData?.price}
          change={marketData?.priceChange}
        />
        <InfoCard
          title="24h Volume"
          value={marketData?.volume}
          format="volume"
        />
        <InfoCard
          title="24h High"
          value={marketData?.high}
        />
        <InfoCard
          title="24h Low"
          value={marketData?.low}
        />
      </div>

      <div style={{ height: '400px' }}>
        <TradingViewWidget symbol={symbol} />
      </div>
    </div>
  );
}

function InfoCard({ title, value, change, format }) {
  const formatValue = (val) => {
    if (!val) return 'N/A';
    if (format === 'volume') {
      return new Intl.NumberFormat('en-US', {
        notation: 'compact',
        maximumFractionDigits: 1
      }).format(val);
    }
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 4,
      maximumFractionDigits: 4
    }).format(val);
  };

  return (
    <div style={{
      padding: '16px',
      background: '#f8fafc',
      borderRadius: '8px',
      border: '1px solid #e2e8f0'
    }}>
      <h3 style={{
        margin: '0 0 8px 0',
        fontSize: '14px',
        color: '#64748b'
      }}>
        {title}
      </h3>
      <div style={{
        fontSize: '24px',
        fontWeight: '600',
        color: '#0f172a'
      }}>
        {formatValue(value)}
      </div>
      {change !== undefined && (
        <div style={{
          marginTop: '4px',
          fontSize: '14px',
          color: change >= 0 ? '#059669' : '#dc2626'
        }}>
          {change >= 0 ? '↑' : '↓'} {Math.abs(change).toFixed(2)}%
        </div>
      )}
    </div>
  );
}