// Test API proxy to verify connectivity between Next.js and Flask
export default async function handler(req, res) {
  if (req.method !== 'GET') {
    return res.status(405).json({ status: 'error', error: 'Method not allowed' });
  }

  try {
    console.log('Running API connectivity test...');
    
    // Get API URL from environment with explicit IPv4 address
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5050';
    console.log(`Testing connectivity to: ${API_URL}/test/ping and ${API_URL}/test/echo`);
    
    // Test 1: Ping endpoint (GET request)
    console.log('Test 1: Pinging Flask backend...');
    const pingResponse = await fetch(`${API_URL}/test/ping`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });
    
    if (!pingResponse.ok) {
      throw new Error(`Ping test failed with status: ${pingResponse.status}`);
    }
    
    const pingData = await pingResponse.json();
    console.log('Ping test result:', pingData);
    
    // Test 2: Echo endpoint (POST request with JSON payload)
    console.log('Test 2: Testing Echo endpoint...');
    const testPayload = {
      test: 'payload',
      timestamp: new Date().toISOString(),
      requestOrigin: 'next-js-frontend'
    };
    
    const echoResponse = await fetch(`${API_URL}/test/echo`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(testPayload)
    });
    
    if (!echoResponse.ok) {
      throw new Error(`Echo test failed with status: ${echoResponse.status}`);
    }
    
    const echoData = await echoResponse.json();
    console.log('Echo test result:', echoData);
    
    // Return combined test results
    return res.status(200).json({
      status: 'success',
      ping_test: pingData,
      echo_test: echoData,
      message: 'API connectivity tests completed successfully'
    });
  } catch (error) {
    console.error('API connectivity test error:', error);
    
    return res.status(500).json({
      status: 'error',
      error: 'API connectivity test failed',
      message: error.message,
      stack: process.env.NODE_ENV === 'development' ? error.stack : undefined
    });
  }
}
