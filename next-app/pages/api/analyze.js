// Analysis endpoint - proxies to backend model analysis
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { model } = req.body;

  if (!model) {
    return res.status(400).json({ error: 'Model parameter is required' });
  }

  try {
    // Get API URL from environment variable with explicit IPv4 address
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5050';
    console.log(`Proxying analyze request to: ${API_URL}/api/analyze`);
    
    // Use AbortController for timeout management
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
    
    const response = await fetch(`${API_URL}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ model }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();
    res.status(200).json({
      status: 'ok',
      result: data.analysis
    });
  } catch (error) {
    console.error('Analysis error:', error);
    res.status(500).json({
      status: 'error',
      error: 'Failed to perform analysis',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}
