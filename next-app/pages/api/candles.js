// Candles data endpoint - proxies to backend candles API
export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ status: 'error', error: 'Method not allowed' });
  }

  try {
    // Get API URL from environment or use fallback
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
    
    // Extract query parameters
    const { instrument = 'XAU_USD', granularity = 'H1', count = 100 } = req.query;
    
    // Validate parameters
    if (!instrument) {
      return res.status(400).json({ status: 'error', error: 'Instrument is required' });
    }
    
    const validGranularities = ['M5', 'M15', 'M30', 'H1', 'H4', 'D'];
    if (!validGranularities.includes(granularity)) {
      return res.status(400).json({ 
        status: 'error', 
        error: `Invalid granularity. Must be one of: ${validGranularities.join(', ')}` 
      });
    }
    
    // Set timeout for the request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);
    
    // Construct URL with query parameters
    const url = new URL(`${API_URL}/candles`);
    url.searchParams.append('instrument', instrument);
    url.searchParams.append('granularity', granularity);
    url.searchParams.append('count', count);
    
    const backendRes = await fetch(url.toString(), {
      method: 'GET',
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    if (!backendRes.ok) {
      throw new Error(`Backend returned status ${backendRes.status}`);
    }
    
    const data = await backendRes.json();
    return res.status(200).json(data);
  } catch (error) {
    console.error('Candles fetch error:', error);
    
    // Check if it's a timeout error
    if (error.name === 'AbortError') {
      return res.status(503).json({ 
        status: 'error',
        error: 'Request timed out fetching candle data'
      });
    }
    
    // General error handler
    return res.status(500).json({ 
      status: 'error',
      error: error.message || 'An unexpected error occurred while fetching candle data'
    });
  }
}
