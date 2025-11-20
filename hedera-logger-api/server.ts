import express, { Request, Response } from 'express';
import logHandler from './api/log';

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware to parse JSON bodies
app.use(express.json());

// Health check endpoint
app.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'OK', message: 'Hedera Logger API is running' });
});

// Forward log requests to the Vercel handler
app.post('/api/log', async (req: Request, res: Response) => {
  try {
    // Create mock VercelRequest/Response objects that match what the handler expects
    const mockVercelReq = {
      method: req.method,
      body: req.body,
      headers: req.headers,
      query: req.query,
    };

    let statusCode = 200;
    let responseData: any = null;
    let responseSent = false;

    const mockVercelRes = {
      status: (code: number) => {
        statusCode = code;
        return mockVercelRes;
      },
      json: (data: any) => {
        if (!responseSent) {
          responseData = data;
          res.status(statusCode).json(data);
          responseSent = true;
        }
        return mockVercelRes;
      },
      setHeader: (name: string, value: any) => {
        res.setHeader(name, value);
        return mockVercelRes;
      },
      end: (data?: any) => {
        if (!responseSent) {
          if (data) {
            res.status(statusCode).end(data);
          } else {
            res.status(statusCode).end();
          }
          responseSent = true;
        }
        return mockVercelRes;
      },
    };

    // Call the log handler
    await logHandler(mockVercelReq as any, mockVercelRes as any);
  } catch (error: any) {
    console.error('Error in log handler:', error);
    if (!res.headersSent) {
      res.status(500).json({ error: error.message });
    }
  }
});

// Start the server
app.listen(PORT, () => {
  console.log(`🚀 Hedera Logger API server is running on http://localhost:${PORT}`);
  console.log(`📝 Log endpoint: http://localhost:${PORT}/api/log`);
  console.log(`❤️  Health check: http://localhost:${PORT}/health`);
});

export default app;