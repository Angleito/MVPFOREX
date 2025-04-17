// Feedback submission endpoint - proxies to backend feedback API
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ status: 'error', error: 'Method not allowed' });
  }

  try {
    // Get API URL from environment or use fallback
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';
    
    // Extract feedback data from request body
    const { model, rating, comments, analysisId } = req.body;
    
    // Validate required fields
    if (!model) {
      return res.status(400).json({ status: 'error', error: 'Model is required' });
    }
    
    if (rating === undefined || rating === null) {
      return res.status(400).json({ status: 'error', error: 'Rating is required' });
    }
    
    // Set timeout for the request
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    
    const backendRes = await fetch(`${API_URL}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        rating,
        comments,
        analysis_id: analysisId || `manual_${Date.now()}`
      }),
      signal: controller.signal,
    });
    
    clearTimeout(timeoutId);
    
    const data = await backendRes.json();
    
    if (!backendRes.ok) {
      return res.status(backendRes.status).json(data);
    }
    
    return res.status(200).json({
      status: 'ok',
      message: 'Feedback submitted successfully',
      data
    });
  } catch (error) {
    console.error('Feedback submission error:', error);
    
    // Check if it's a timeout error
    if (error.name === 'AbortError') {
      return res.status(503).json({ 
        status: 'error',
        error: 'Request timed out while submitting feedback'
      });
    }
    
    // General error handler
    return res.status(500).json({ 
      status: 'error',
      error: error.message || 'An unexpected error occurred while submitting feedback'
    });
  }
}
