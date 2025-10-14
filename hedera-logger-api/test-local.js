const express = require('express');
const handler = require('./api/log.ts');
require('dotenv').config();

const app = express();
app.use(express.json());

// Mock Vercel request/response
app.post('/test-hedera', async (req, res) => {
  console.log('Testing Hedera logging with:', req.body);

  const mockReq = {
    method: 'POST',
    body: req.body
  };

  const mockRes = {
    status: (code) => {
      console.log(`Response status: ${code}`);
      return {
        json: (data) => {
          console.log('Response data:', data);
          res.status(code).json(data);
        }
      };
    },
    setHeader: () => mockRes
  };

  try {
    await handler.default(mockReq, mockRes);
  } catch (error) {
    console.error('Test error:', error);
    res.status(500).json({ error: error.message });
  }
});

const PORT = 3001;
app.listen(PORT, () => {
  console.log(`🚀 Local test server running on http://localhost:${PORT}`);
  console.log('\nTo test Hedera logging:');
  console.log(`curl -X POST http://localhost:${PORT}/test-hedera -H "Content-Type: application/json" -d '{"log_message": "Test message from local"}'`);
});