# 🚀 Quick Start - Insurance Bot

> Hướng dẫn setup và chạy Insurance Bot trong 5 phút

## 🎯 **3 Cách Setup**

### **1. Docker (Khuyên dùng - Dễ nhất)**
```bash
# 1. Setup
./deploy.sh setup

# 2. Edit config
nano .env

# 3. Deploy
./deploy.sh deploy

# 4. Test
./deploy.sh status
```

### **2. Demo (Không cần API keys)**
```bash
# Chạy demo Swagger UI
python run_swagger_demo.py
```

### **3. Manual (Python trực tiếp)**
```bash
# Install
pip install -r core/requirements.txt

# Run demo
python run_swagger_demo.py

# Or run full bot (cần API keys)
python run_swagger_ui.py
```

---

## 📋 **Checklist Setup**

### **Bước 1: Dependencies**
- [ ] Docker & Docker Compose installed
- [ ] Python 3.8+ installed
- [ ] Git installed

### **Bước 2: API Keys**
- [ ] OpenAI API Key (từ https://platform.openai.com)
- [ ] Neo4J credentials (hoặc dùng Docker)

### **Bước 3: Configuration**
- [ ] Copy `deploy.env` → `.env`
- [ ] Edit `.env` với API keys
- [ ] Check ports không bị conflict

### **Bước 4: Deploy**
- [ ] `./deploy.sh deploy` (Docker)
- [ ] Hoặc `python run_swagger_ui.py` (Python)

### **Bước 5: Verify**
- [ ] API: http://localhost:8001/health
- [ ] Swagger UI: http://localhost:8001/api/docs
- [ ] Neo4J Browser: http://localhost:7474

---

## 🐳 **Docker Commands**

```bash
# Full deployment
./deploy.sh deploy

# Individual commands
./deploy.sh setup     # Setup config
./deploy.sh build     # Build images
./deploy.sh start     # Start services
./deploy.sh import    # Import data

# Management
./deploy.sh logs      # View logs
./deploy.sh status    # Check health
./deploy.sh restart   # Restart all
./deploy.sh stop      # Stop all
./deploy.sh cleanup   # Clean up
```

---

## 🔧 **Troubleshooting**

### **Docker issues**
```bash
# Check Docker
docker --version
docker-compose --version

# Check ports
netstat -tulpn | grep :8001
netstat -tulpn | grep :7474

# Clean up
./deploy.sh cleanup
./deploy.sh deploy
```

### **API issues**
```bash
# Check API health
curl http://localhost:8001/health

# Check logs
./deploy.sh logs

# Restart API
./deploy.sh restart
```

### **Configuration issues**
```bash
# Validate config
python scripts/load_config.py

# Check .env file
cat .env | grep -v PASSWORD
```

---

## 📱 **Test API**

Sau khi deploy thành công:

### **Swagger UI**
```
🌐 http://localhost:8001/api/docs
```
- Click `POST /chat`
- Click `Try it out`
- Nhập: `{"message": "Bảo hiểm xe máy là gì?"}`
- Click `Execute`

### **Curl test**
```bash
# Health check
curl http://localhost:8001/health

# Chat test
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test"}'
```

---

## 🎉 **Success Indicators**

✅ **API Health:** `{"status": "healthy", "bot_ready": true}`

✅ **Swagger UI:** Load được trang với endpoints

✅ **Chat Response:** Nhận được JSON response với processing_time

✅ **Neo4J:** Browser accessible tại port 7474

---

## 📚 **Next Steps**

1. **Import data:** `./deploy.sh import`
2. **Run tests:** `python tests/test_bot_cuoi_cung.py`
3. **Monitor logs:** `./deploy.sh logs`
4. **Scale up:** Edit `docker-compose.yml`

---

## 🆘 **Need Help?**

- **Logs:** `./deploy.sh logs`
- **Status:** `./deploy.sh status`
- **Config:** `python scripts/load_config.py`
- **Docs:** `COMMANDS.md`, `README.md`

**🎯 Quick deploy:** `./deploy.sh setup && nano .env && ./deploy.sh deploy`
