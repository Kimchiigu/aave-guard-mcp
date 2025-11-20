"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const log_1 = __importDefault(require("./api/log"));
const app = (0, express_1.default)();
const PORT = process.env.PORT || 3001;
// Middleware to parse JSON bodies
app.use(express_1.default.json());
// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'OK', message: 'Hedera Logger API is running' });
});
// Forward log requests to the Vercel handler
app.post('/api/log', async (req, res) => {
    try {
        // Create mock VercelRequest/Response objects that match what the handler expects
        const mockVercelReq = {
            method: req.method,
            body: req.body,
            headers: req.headers,
            query: req.query,
        };
        let statusCode = 200;
        let responseData = null;
        let responseSent = false;
        const mockVercelRes = {
            status: (code) => {
                statusCode = code;
                return mockVercelRes;
            },
            json: (data) => {
                if (!responseSent) {
                    responseData = data;
                    res.status(statusCode).json(data);
                    responseSent = true;
                }
                return mockVercelRes;
            },
            setHeader: (name, value) => {
                res.setHeader(name, value);
                return mockVercelRes;
            },
            end: (data) => {
                if (!responseSent) {
                    if (data) {
                        res.status(statusCode).end(data);
                    }
                    else {
                        res.status(statusCode).end();
                    }
                    responseSent = true;
                }
                return mockVercelRes;
            },
        };
        // Call the log handler
        await (0, log_1.default)(mockVercelReq, mockVercelRes);
    }
    catch (error) {
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
exports.default = app;
//# sourceMappingURL=server.js.map