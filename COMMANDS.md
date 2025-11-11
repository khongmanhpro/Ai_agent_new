# 📋 Hướng Dẫn Lệnh Chạy - MiniRAG Insurance Bot

> Dự án chatbot bảo hiểm sử dụng MiniRAG framework với Neo4J, OpenAI, và Flask API

## 📊 **Tổng quan lệnh**

| Nhóm | Số lệnh | Mục đích |
|------|---------|----------|
| Setup | 1 | Cài đặt dependencies |
| Bot chính | 3 | Chạy chatbot |
| Demo | 1 | Demo không cần setup |
| Test | 6 | Kiểm tra và debug |
| Data | 2 | Import dữ liệu |
| Visualize | 1 | Hiển thị graph |
| Development | 3 | Scripts hỗ trợ |
| **Tổng** | **17** | |

---

## ⚙️ **0. CONFIGURATION - Cấu hình dự án**

### **File cấu hình chính**
```
config/insurance_config.ini
```

**Các settings quan trọng:**
- **Neo4J:** URI, username, password, pool size
- **OpenAI:** API key, base URL, model, tokens
- **MiniRAG:** Working dir, storage, embeddings
- **Server:** `API_PORT=8001`, `API_HOST=0.0.0.0`

### **Thay đổi port cho server**
```bash
# Chỉnh sửa config/insurance_config.ini
[DEFAULT]
API_PORT=8080  # Thay đổi port ở đây
API_HOST=0.0.0.0
```

**Example - Thay đổi thành port 8080:**
```bash
# Chạy script example
bash example_config_change.sh

# Hoặc chỉnh sửa thủ công
sed -i 's/API_PORT=8001/API_PORT=8080/' config/insurance_config.ini

# Restart server
python core/insurance_api_simple.py

# Truy cập: http://localhost:8080/api/docs
```

### **Thay đổi Neo4J connection**
```bash
# Chỉnh sửa config/insurance_config.ini
[DEFAULT]
NEO4J_URI=neo4j://your-server:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
```

---

## 🐳 **0. DOCKER DEPLOYMENT - Triển khai với Docker**

### **Full deployment với Docker (Khuyên dùng):**
```bash
cd /Volumes/data/MINIRAG

# 1. Setup config
./deploy.sh setup

# 2. Edit .env với API keys
nano .env

# 3. Deploy toàn bộ
./deploy.sh deploy

# 4. Check status
./deploy.sh status
```

### **Các lệnh Docker:**
```bash
./deploy.sh start     # Start services
./deploy.sh stop      # Stop services
./deploy.sh restart   # Restart services
./deploy.sh logs      # View logs
./deploy.sh status    # Check health
./deploy.sh import    # Import data
./deploy.sh cleanup   # Clean up
```

### **Files cấu hình Docker:**
- **`deploy.env`** - Template cấu hình
- **`.env`** - File cấu hình thực tế
- **`docker-compose.yml`** - Định nghĩa services
- **`Dockerfile`** - Build container
- **`deploy.sh`** - Script deployment

### **Services trong Docker:**
- **Neo4J** (port 7474/7687) - Graph database
- **Insurance Bot API** (port configurable) - Flask API + Swagger UI
- **Redis** (optional, port 6379) - Caching
- **Prometheus/Grafana** (optional) - Monitoring

### **Ưu điểm Docker:**
- ✅ Tự động setup environment
- ✅ Isolated containers
- ✅ Easy scaling
- ✅ Consistent deployment
- ✅ Health checks
- ✅ Auto-restart

---

## 🚀 **1. SETUP - Chuẩn bị môi trường**

### 1.1 Cài đặt dependencies
```bash
cd /Volumes/data/MINIRAG
pip install -r core/requirements.txt
```
- **Thời gian:** 2-5 phút (lần đầu)
- **Cần:** Internet, pip
- **Output:** Cài đặt Flask, MiniRAG, Neo4J driver, OpenAI, etc.

---

## 🤖 **2. BOT CHÍNH - Chạy chatbot**

### 2.1 Bot console (Tương tác trực tiếp)
```bash
cd /Volumes/data/MINIRAG
python core/insurance_bot_minirag.py
```
- **Cần:** Neo4J, OpenAI API key
- **Input:** Nhập câu hỏi trực tiếp
- **Output:** Trả lời từ MiniRAG
- **Dừng:** Nhấn Ctrl+C

### 2.2 API server (Cho frontend)
```bash
cd /Volumes/data/MINIRAG
python core/insurance_api_simple.py
```
- **Cần:** Neo4J, OpenAI API key
- **Port:** 8001
- **Endpoints:** `/health`, `/chat`, `/api/docs`
- **Swagger UI:** http://localhost:8001/api/docs
- **Dừng:** Nhấn Ctrl+C

### 2.3 API với auto-launch (Khuyên dùng)
```bash
cd /Volumes/data/MINIRAG
python run_swagger_ui.py
```
- **Cần:** Neo4J, OpenAI API key
- **Tự động:** Khởi động server + mở browser
- **Features:** Health check, error handling
- **Dừng:** Nhấn Ctrl+C

---

## 🎭 **3. DEMO MODE - Không cần setup**

### 3.1 Demo Swagger UI (Không cần MiniRAG)
```bash
cd /Volumes/data/MINIRAG
python run_swagger_demo.py
```
- **Cần:** Chỉ Flask + requests
- **Không cần:** Neo4J, OpenAI, MiniRAG
- **Response:** Demo responses với tag [DEMO MODE]
- **Mục đích:** Test UI, API structure

---

## 🧪 **4. TEST & DEBUG - Kiểm tra chức năng**

### 4.1 Test bot hoạt động
```bash
cd /Volumes/data/MINIRAG
python tests/test_bot_cuoi_cung.py
```
- **Test:** Bot có trả lời được không
- **Input:** Câu hỏi mẫu về bảo hiểm
- **Output:** Response + processing time

### 4.2 Test API endpoints
```bash
cd /Volumes/data/MINIRAG
python tests/test_api_integration.py
```
- **Test:** API `/health` và `/chat`
- **Output:** HTTP status, JSON response

### 4.3 Test Swagger UI
```bash
cd /Volumes/data/MINIRAG
python tests/test_swagger_ui.py
```
- **Test:** OpenAPI spec, Swagger UI accessibility
- **Output:** Validation results

### 4.4 Đo performance
```bash
cd /Volumes/data/MINIRAG
python tests/test_thoi_gian_phan_hoi_v2.py
```
- **Test:** Thời gian phản hồi
- **Output:** Stats, average time, rating

### 4.5 Debug MiniRAG
```bash
cd /Volumes/data/MINIRAG
python tests/debug_tim_kiem_minirag.py
```
- **Debug:** Quá trình retrieval của MiniRAG
- **Output:** Debug logs, search results

### 4.6 Tính chi phí token
```bash
cd /Volumes/data/MINIRAG
python tests/test_chi_phi_token.py
```
- **Test:** Chi phí OpenAI API
- **Output:** Token count, cost estimation

---

## 📊 **5. DATA - Import dữ liệu**

### 5.1 Import legal documents
```bash
cd /Volumes/data/MINIRAG
python scripts/import_all_legal_docs.py
```
- **Cần:** Neo4J running
- **Input:** Files trong `data/` folder
- **Output:** Nodes/relationships trong Neo4J
- **Thời gian:** 5-10 phút

### 5.2 Import sample insurance data
```bash
cd /Volumes/data/MINIRAG
python tests/load_insurance_data.py
```
- **Cần:** Neo4J running
- **Input:** Sample customers, policies
- **Output:** Demo data trong Neo4J

---

## 🔍 **6. VISUALIZE - Hiển thị dữ liệu**

### 6.1 Visualize Neo4J graph
```bash
cd /Volumes/data/MINIRAG/MiniRAG/graph-visuals
python graph_with_neo4j.py
```
- **Cần:** Neo4J running, data imported
- **Output:** Graph visualization
- **Tools:** NetworkX, Matplotlib

---

## 🛠️ **7. DEVELOPMENT - Scripts hỗ trợ**

### 7.1 Chạy API server (script)
```bash
cd /Volumes/data/MINIRAG
python scripts/run_api_server.py
```
- **Tương tự:** `python core/insurance_api_simple.py`
- **Ưu điểm:** Script wrapper

### 7.2 Chạy UI server (legacy)
```bash
cd /Volumes/data/MINIRAG
python scripts/run_ui_server.py
```
- **Legacy:** Thay bằng Swagger UI
- **Output:** Simple HTTP server cho UI files

### 7.3 Demo Swagger API
```bash
cd /Volumes/data/MINIRAG
python demo_swagger_api.py
```
- **Standalone:** API demo không cần launcher
- **Port:** 8001
- **UI:** http://localhost:8001/api/docs

---

## 🎯 **Workflow thông thường**

### **Đầu tiên (Setup):**
```bash
pip install -r core/requirements.txt
```

### **Test nhanh (Demo):**
```bash
python run_swagger_demo.py
```

### **Chạy thật (Production):**
```bash
python run_swagger_ui.py
```

### **Import data:**
```bash
python scripts/import_all_legal_docs.py
```

### **Test full:**
```bash
python tests/test_bot_cuoi_cung.py
python tests/test_thoi_gian_phan_hoi_v2.py
```

---

## ⚠️ **Prerequisites**

| Lệnh | Cần Neo4J | Cần OpenAI | Cần MiniRAG | Thời gian |
|------|-----------|------------|--------------|-----------|
| `pip install` | ❌ | ❌ | ❌ | 5 min |
| `run_swagger_demo.py` | ❌ | ❌ | ❌ | < 5s |
| `run_swagger_ui.py` | ✅ | ✅ | ✅ | 30s |
| `insurance_api_simple.py` | ✅ | ✅ | ✅ | 30s |
| `import_all_legal_docs.py` | ✅ | ❌ | ❌ | 10 min |
| Test scripts | ✅ | ✅ | ✅ | 10-60s |

---

## 🚨 **Troubleshooting**

### **Lỗi "torch import"**
```bash
# Chạy demo thay vì bot thật
python run_swagger_demo.py
```

### **Lỗi "Neo4J connection"**
```bash
# Kiểm tra Neo4J running
docker ps | grep neo4j
```

### **Lỗi "OpenAI quota"**
```bash
# Kiểm tra API key
python tests/test_cau_hinh_openai.py
```

### **Port 8001 occupied**
```bash
# Kill process
lsof -ti:8001 | xargs kill -9
```

---

## 📚 **API Endpoints**

Sau khi chạy API server:

| Endpoint | Method | Mục đích |
|----------|--------|----------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/chat` | POST | Chat với bot |
| `/api/spec` | GET | OpenAPI spec |
| `/api/docs` | GET | **Swagger UI** |

---

## 🎉 **Quick Commands**

```bash
# 🚀 Demo nhanh (không cần gì)
python run_swagger_demo.py

# 🤖 Bot thật (cần Neo4J + OpenAI)
python run_swagger_ui.py

# 🧪 Test all
python tests/test_bot_cuoi_cung.py
python tests/test_api_integration.py
python tests/test_swagger_ui.py

# 📊 Import data
python scripts/import_all_legal_docs.py

# 🔍 Visualize
cd MiniRAG/graph-visuals && python graph_with_neo4j.py
```

---

**📅 Cập nhật:** $(date)
**👨‍💻 Author:** MiniRAG Insurance Bot Team
**📧 Support:** FISS Insurance
