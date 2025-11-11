# FISS Chat UI

Professional Chat UI for FISS Insurance Bot built with Node.js and Express.

## 🚀 Quick Start

### Install Dependencies

```bash
cd chat-ui
npm install
```

### Run Development Server

```bash
npm start
```

Or with auto-reload:

```bash
npm run dev
```

### Access Chat UI

Open browser: http://localhost:3000

## ⚙️ Configuration

Set environment variables:

```bash
PORT=3000                    # Chat UI server port (default: 3000)
API_URL=http://localhost:8001  # Backend API URL
API_KEY=your-api-key         # API key for authentication
```

Or create `.env` file:

```env
PORT=3000
API_URL=http://localhost:8001
API_KEY=fiss-c61197f847cc4682a91ada560bbd7119
```

## 📁 Project Structure

```
chat-ui/
├── server.js          # Express server
├── package.json       # Dependencies
├── README.md          # Documentation
└── public/            # Static files
    ├── index.html     # Main HTML
    ├── styles.css     # Styles
    └── app.js         # Frontend JavaScript
```

## 🎨 Features

- ✅ Beautiful, modern UI
- ✅ Real-time chat interface
- ✅ Auto-scroll messages
- ✅ Loading indicators
- ✅ Error handling
- ✅ Responsive design
- ✅ Status indicator
- ✅ Processing time display

## 🔧 Development

### Install Dependencies

```bash
npm install
```

### Run with Nodemon (auto-reload)

```bash
npm run dev
```

## 📦 Production

### Build (if needed)

No build step required - just run:

```bash
npm start
```

### Docker (Optional)

You can containerize this with Docker if needed.

## 🔗 API Integration

The Chat UI communicates with the backend API at `/api/chat` endpoint.

**Request:**
```json
{
  "message": "Bảo hiểm xe máy là gì?",
  "session_id": "optional"
}
```

**Response:**
```json
{
  "response": "Bot response...",
  "timestamp": 1234567890.123,
  "session_id": "optional",
  "processing_time": 2.5
}
```

## 📝 License

MIT

