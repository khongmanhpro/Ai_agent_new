const express = require('express');
const cors = require('cors');
const path = require('path');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;
const API_URL = process.env.API_URL || 'http://localhost:8001';
const API_KEY = process.env.API_KEY || 'fiss-c61197f847cc4682a91ada560bbd7119';

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Proxy endpoint để tránh CORS issues
app.post('/api/chat', async (req, res) => {
    try {
        const { message, session_id } = req.body;

        if (!message) {
            return res.status(400).json({
                error: {
                    message: "Missing 'message' field",
                    type: "validation_error",
                    code: "missing_message"
                }
            });
        }

        const response = await axios.post(`${API_URL}/chat`, {
            message: message,
            session_id: session_id
        }, {
            headers: {
                'accept': 'application/json',
                'x-api-version': '1.0.0',
                'X-API-Key': API_KEY,
                'Authorization': `Bearer ${API_KEY}`,
                'Content-Type': 'application/json'
            },
            timeout: 60000 // 60 seconds timeout
        });

        res.json(response.data);
    } catch (error) {
        console.error('❌ Chat API Error:', error.message);
        
        if (error.response) {
            // API returned error
            res.status(error.response.status).json(error.response.data);
        } else if (error.request) {
            // Request made but no response
            res.status(503).json({
                error: {
                    message: "Không thể kết nối đến API server. Vui lòng kiểm tra lại.",
                    type: "connection_error",
                    code: "api_unavailable"
                }
            });
        } else {
            // Error setting up request
            res.status(500).json({
                error: {
                    message: error.message || "Internal server error",
                    type: "server_error",
                    code: "internal_error"
                }
            });
        }
    }
});

// Health check
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        api_url: API_URL,
        timestamp: new Date().toISOString()
    });
});

// Serve index.html for all routes
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
    console.log(`🚀 FISS Chat UI Server running on http://localhost:${PORT}`);
    console.log(`📡 API URL: ${API_URL}`);
    console.log(`🔑 API Key: ${API_KEY.substring(0, 10)}...`);
});

