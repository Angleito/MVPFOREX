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
    const response = await fetch('http://localhost:5000/api/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ model })
    });

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
