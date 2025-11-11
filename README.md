# 🤖 Insurance RAG Bot - MiniRAG Framework

Dự án chatbot tư vấn bảo hiểm sử dụng MiniRAG framework với Neo4J làm knowledge graph.

## 📁 Cấu trúc dự án

```
/Volumes/data/MINIRAG/
├── core/                    # Core application files
│   ├── insurance_bot_minirag.py    # Main bot application
│   └── insurance_app.py            # Legacy app (deprecated)
├── scripts/                 # Import và setup scripts
│   ├── import_*.py          # Import legal documents
│   ├── load_*.py            # Load data scripts
│   └── check_*.py           # Status checking scripts
├── tests/                   # Test files
│   ├── *.py                 # Test scripts (tiếng Việt)
│   └── README.md            # Hướng dẫn chi tiết các test
├── docs/                    # Documentation
│   ├── *.md                 # README files và templates
│   └── OPTIMIZATION_LOG.md  # Performance optimization log
├── config/                  # Configuration files
│   └── insurance_config.ini # Main configuration
├── data/                    # Insurance documents
│   ├── *.md                 # Legal documents
│   └── dataw/              # Working data
├── logs/                    # Logs và data stores
│   └── insurance_rag/      # MiniRAG working directory
└── MiniRAG/                # MiniRAG framework source
```

## 🚀 Quick Start

> 📖 **Xem [`QUICKSTART.md`](QUICKSTART.md)** để setup nhanh trong 5 phút
>
> 📖 **Xem [`COMMANDS.md`](COMMANDS.md)** để biết tất cả các lệnh chạy chi tiết.

### 1. Chạy bot chính
```bash
cd /Volumes/data/MINIRAG
python core/insurance_bot_minirag.py
```

### 1.5. Chạy API server (cho frontend)
```bash
cd /Volumes/data/MINIRAG
pip install -r core/requirements.txt
python core/insurance_api_simple.py
```
**API sẽ chạy tại:** `http://localhost:8001`
- **Health check:** `http://localhost:8001/health`
- **Chat endpoint:** `POST /chat`
- **📚 Swagger UI:** `http://localhost:8001/api/docs` (tự động tạo UI)
- **OpenAPI Spec:** `http://localhost:8001/api/spec`
- **API documentation:** Xem trong `core/insurance_api_simple.py`

### 2. Import thêm dữ liệu
```bash
cd /Volumes/data/MINIRAG
python scripts/import_all_legal_docs.py
```

### 3. Test bot
```bash
cd /Volumes/data/MINIRAG
python tests/test_bot_cuoi_cung.py
```

### 4. Test Swagger UI
```bash
cd /Volumes/data/MINIRAG

# Chạy Swagger UI (khuyên dùng - tự động khởi động server và mở browser)
python run_swagger_ui.py

# Hoặc chạy thủ công
python core/insurance_api_simple.py
# Sau đó truy cập: http://localhost:8001/api/docs

# Test API endpoints với script
python tests/test_api_integration.py
python tests/test_swagger_ui.py
```

### 5. Visualize graph data
```bash
cd /Volumes/data/MINIRAG/MiniRAG/graph-visuals
python graph_with_neo4j.py
```
*Xem knowledge graph trong Neo4J Browser tại: http://localhost:7474*

## ⚙️ Configuration

File config chính: `config/insurance_config.ini`

Các tham số quan trọng:
- `TOP_K=30`: Số lượng retrieval tối đa
- `COSINE_THRESHOLD=0.3`: Ngưỡng similarity
- `OPENAI_LLM_MAX_TOKENS=800`: Token limit cho LLM

## 📊 Performance

- **Thời gian phản hồi trung bình:** ~30 giây
- **Cải thiện so với baseline:** +15.5%
- **Embedding cache:** Có (TTL 1 giờ)
- **Knowledge graph:** 4,514 nodes, 4,310 relationships

Chi tiết: `docs/OPTIMIZATION_LOG.md`

## 🧪 Test Cases

Bot có thể trả lời các câu hỏi về:
- Bảo hiểm xe máy
- Quy tắc bảo hiểm nhà tù nhân
- Bảo hiểm du lịch toàn cầu
- Bảo hiểm tai nạn con người

## 📚 Documentation

- `docs/MINIRAG_BOT_README.md`: Hướng dẫn chi tiết bot
- `docs/OPTIMIZATION_LOG.md`: Log tối ưu performance
- `docs/markdown_template_example.md`: Template import documents
- `tests/README.md`: Hướng dẫn chi tiết các file test
- `core/insurance_api.py`: API server với Swagger UI

## 🔌 API Endpoints

### Chat với Bot
```http
POST /chat
Content-Type: application/json

{
  "message": "Bảo hiểm xe máy là gì?",
  "user_id": "optional",
  "session_id": "optional"
}
```

**Response:**
```json
{
  "response": "Bảo hiểm xe máy là loại hình bảo hiểm bắt buộc...",
  "timestamp": 1234567890.123,
  "session_id": "session_123",
  "processing_time": 25.3
}
```

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1234567890.123,
  "bot_ready": true,
  "version": "1.0.0"
}
```

### 📝 **Lưu ý:**
- API chạy trên **port 8001** (thay vì 8000 để tránh conflict)
- Thời gian xử lý trung bình: **30-45 giây** (do MiniRAG processing)
- Bot cache embeddings để tăng tốc lần query sau

### 📚 Swagger UI Documentation
- **URL:** `http://localhost:8001/api/docs`
- **Features:**
  - Interactive API documentation
  - Try-it-out functionality
  - Request/response examples
  - Schema definitions
  - Authentication support

```bash
# Cách 1: Chạy API server thủ công
python core/insurance_api_simple.py

# Cách 2: Chạy với script tự động (khuyên dùng)
python run_swagger_ui.py

# Sau đó truy cập: http://localhost:8001/api/docs
```

### 📋 OpenAPI Specification
- **URL:** `http://localhost:8001/api/spec`
- **Format:** OpenAPI 3.0.3 JSON
- **Download:** Để sử dụng với các tools khác

## ⚙️ **Configuration**

### **File cấu hình chính**
```
config/insurance_config.ini
```
- **Neo4J settings:** URI, username, password
- **OpenAI settings:** API key, base URL, model
- **MiniRAG settings:** Working dir, storage, embeddings
- **Server settings:** `API_PORT=8001`, `API_HOST=0.0.0.0`

### **Thay đổi port**
```ini
# Trong config/insurance_config.ini
[DEFAULT]
API_PORT=8001  # Thay đổi port ở đây
API_HOST=0.0.0.0
```

## 🔧 Development

### Thêm dữ liệu mới
1. Đặt file .md vào `data/`
2. Chạy `python scripts/import_all_legal_docs.py`

### Test performance
```bash
cd /Volumes/data/MINIRAG
python tests/test_thoi_gian_phan_hoi_v2.py
```

### Debug issues
```bash
cd /Volumes/data/MINIRAG
python tests/debug_tim_kiem_minirag.py
```

## 🐳 **Docker Deployment (Khuyên dùng)**

### **Setup nhanh với Docker:**
```bash
# 1. Setup config
./deploy.sh setup

# 2. Edit .env file với API keys của bạn
nano .env

# 3. Deploy toàn bộ hệ thống
./deploy.sh deploy
```

### **Các lệnh Docker:**
```bash
# Start services
./deploy.sh start

# Stop services
./deploy.sh stop

# View logs
./deploy.sh logs

# Check status
./deploy.sh status

# Import data
./deploy.sh import

# Cleanup
./deploy.sh cleanup
```

### **Files cấu hình Docker:**
- **`deploy.env`** - Template config
- **`.env`** - Config thực tế (tự tạo)
- **`docker-compose.yml`** - Service definitions
- **`Dockerfile`** - Container build
- **`deploy.sh`** - Deployment script

---

## 📋 Requirements

- Python 3.8+
- Neo4J database
- OpenAI API access
- MiniRAG framework

## 🤝 Contributing

1. Fork project
2. Tạo feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

---

## 🧹 **Project Cleanup Summary**

Dự án đã được **dọn dẹp hoàn toàn** để tối ưu structure và maintainability:

- ✅ **25 files production** - Chỉ giữ files cần thiết cho production
- ✅ **Archive system** - Files cũ trong `archive/` folder (git ignored)
- ✅ **Clean git history** - .gitignore tối ưu, loại trừ files không cần thiết
- ✅ **Organized documentation** - README, QUICKSTART, COMMANDS, SERVER_DEPLOYMENT

📖 **Chi tiết dọn dẹp:** Xem [`CLEANUP_SUMMARY.md`](CLEANUP_SUMMARY.md)

---

**Project:** Insurance RAG Bot with MiniRAG
**Framework:** MiniRAG + Neo4J + OpenAI
**Status:** Production Ready 🚀
