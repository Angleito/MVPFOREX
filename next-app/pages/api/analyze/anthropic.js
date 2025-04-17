// API proxy for Anthropic (Claude 3.7) analysis
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ status: 'error', error: 'Method not allowed' });
  }

  try {
    // Enhanced debugging for request body
    console.log('Claude analysis request body:', JSON.stringify(req.body, null, 2));
    
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5050';
    console.log(`Proxying Claude analysis request to: ${API_URL}/api/analyze/anthropic`);
    
    // Set up proper timeout handling with longer timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000); // 20 second timeout
    
    console.log('Making fetch request to Flask backend for Claude analysis...');
    const response = await fetch(`${API_URL}/api/analyze/anthropic`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(req.body),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    console.log(`Claude analysis response status: ${response.status}`);
    
    // More detailed error handling for non-200 responses
    if (!response.ok) {
      console.error(`Backend error for Claude analysis: ${response.status}`);
      
      // Try to get error details from response
      try {
        const errorData = await response.json();
        console.error('Claude analysis error details:', errorData);
        
        return res.status(response.status).json({
          status: 'error',
          error: 'Backend error: ' + (errorData.error || 'Unknown error'),
          details: errorData,
          analysis: errorData.analysis || 'Failed to generate Claude 3.7 analysis.'
        });
      } catch (jsonError) {
        console.error('Could not parse error response from backend:', jsonError);
        throw new Error(`Backend responded with status: ${response.status}`);
      }
    }
    
    // Process successful response
    try {
      const data = await response.json();
      console.log(`Successfully received Claude analysis from backend (${data.analysis ? data.analysis.length : 0} chars)`);
      return res.status(200).json(data);
    } catch (jsonError) {
      console.error('Error parsing successful response JSON:', jsonError);
      throw new Error('Invalid JSON in response from backend');
    }
  } catch (error) {
    console.error('Claude analysis proxy error:', error);
    
    // Enhanced error response
    return res.status(500).json({
      status: 'error',
      error: 'Failed to get Claude analysis',
      message: error.message,
      details: process.env.NODE_ENV === 'development' ? {
        stack: error.stack,
        message: error.message
      } : undefined,
      analysis: 'An error occurred while generating Claude 3.7 analysis. Please try again.'
    });
  }
}
