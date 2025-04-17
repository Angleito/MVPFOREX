// Health check endpoint - proxies to backend health check
export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  try {
    // Get API URL from environment variable
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5050';
    
    const response = await fetch(`${API_URL}/health`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`Backend health check failed with status: ${response.status}`);
    }

    const data = await response.json();
    res.status(200).json({ 
      status: 'healthy',
      serverStatus: data.status || 'ok',
      serverless: data.serverless || false
    });
  } catch (error) {
    console.error('Health check error:', error);
    res.status(503).json({
      status: 'unhealthy',
      error: 'Backend service unavailable',
      details: process.env.NODE_ENV === 'development' ? error.message : undefined
    });
  }
}
