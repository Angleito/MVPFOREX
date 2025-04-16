import { useEffect, useState } from 'react';

export default function Home() {
  const [candles, setCandles] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/test-candles')
      .then(res => res.json())
      .then(data => setCandles(data.candles))
      .catch(err => setError(err.toString()));
  }, []);

  return (
    <main style={{ padding: 32, fontFamily: 'sans-serif' }}>
      <h1>MVPFOREX Next.js Frontend</h1>
      <p>This page fetches candlestick data from your Flask API at <code>/api/test-candles</code>.</p>
      {error && <div style={{ color: 'red' }}>Error: {error}</div>}
      {candles ? (
        <table border="1" cellPadding="6" style={{ marginTop: 16 }}>
          <thead>
            <tr>
              <th>Timestamp</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th>
            </tr>
          </thead>
          <tbody>
            {candles.map((c, i) => (
              <tr key={i}>
                <td>{c.timestamp}</td>
                <td>{c.open}</td>
                <td>{c.high}</td>
                <td>{c.low}</td>
                <td>{c.close}</td>
                <td>{c.volume}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div>Loading candlestick data...</div>
      )}
    </main>
  );
}
