const https = require('https');

async function testLiveAPI() {
  console.log('🧪 Testing live Vercel API...');

  const testData = {
    log_message: `Test message from live API check at ${new Date().toISOString()}`
  };

  const options = {
    hostname: 'aave-guard-mcp.vercel.app',
    port: 443,
    path: '/api/hedera',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(JSON.stringify(testData))
    }
  };

  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      console.log(`📡 Response status: ${res.statusCode}`);
      console.log(`📡 Response headers:`, res.headers);

      let data = '';
      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          console.log('📦 Response data:', response);
          resolve(response);
        } catch (e) {
          console.log('📦 Raw response:', data);
          resolve(data);
        }
      });
    });

    req.on('error', (error) => {
      console.error('❌ Request error:', error);
      reject(error);
    });

    console.log('📤 Sending test data:', testData);
    req.write(JSON.stringify(testData));
    req.end();
  });
}

testLiveAPI().catch(console.error);