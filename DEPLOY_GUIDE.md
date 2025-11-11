# 🚀 Server Deployment Guide - Insurance Bot

> **Hướng dẫn deploy Insurance Bot lên production server**

---

## 📋 **Mục lục**

- [⚡ Quick Deploy (Khuyên dùng)](#-quick-deploy-khuyên-dùng)
- [🔧 Manual Deploy](#-manual-deploy)
- [⚙️ Configuration](#️-configuration)
- [🔐 Authentication](#-authentication)
- [🧪 Testing](#-testing)
- [🔍 Troubleshooting](#-troubleshooting)

---

## ⚡ **Quick Deploy (Khuyên dùng)**

### **1. Chuẩn bị server:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y curl wget git ufw nginx certbot python3-certbot-nginx

# Install Docker
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

# Logout và login lại để docker group có hiệu lực
```

### **2. Clone và deploy:**
```bash
# Clone project
git clone https://github.com/jackevansdtq/Ai_agent_new.git
cd Ai_agent_new

# Deploy nhanh với domain của bạn
./quick-deploy.sh your-domain.com admin@your-domain.com
```

**⏱️ Thời gian:** ~10-15 phút
**🎯 Kết quả:** Server sẵn sàng với SSL, monitoring, và tất cả services

---

## 🔧 **Manual Deploy**

### **Bước 1: Setup cơ bản**
```bash
# Tạo user cho ứng dụng (không dùng root)
sudo useradd -m -s /bin/bash insurance-bot
sudo usermod -aG docker insurance-bot

# Setup firewall
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

### **Bước 2: Cấu hình environment**
```bash
cd /path/to/project

# Copy config template
cp deploy.env .env

# Edit config với thông tin server
nano .env
```

**Những thứ cần thay đổi trong `.env`:**
```bash
# Domain của bạn
DOMAIN=your-domain.com
EMAIL=admin@your-domain.com

# API Keys đã có sẵn - không cần thay đổi
API_SECRET_KEY=fiss-c61197f847cc4682a91ada560bbd7119
OPENAI_API_KEY=sk-LMnsn4epAmLcPtSNAencVKyhRbkYNqUCMTzBsMIO7F24fbP0
```

### **Bước 3: Deploy services**
```bash
# Build và start tất cả services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs
```

### **Bước 4: Setup SSL**
```bash
# Chờ nginx ready
sleep 10

# Tạo SSL certificate
sudo certbot --nginx -d your-domain.com --email admin@your-domain.com --agree-tos --non-interactive

# Restart nginx
sudo systemctl restart nginx
```

---

## ⚙️ **Configuration**

### **File cấu hình chính:**
- **`.env`** - Cấu hình environment variables
- **`docker-compose.yml`** - Services definition
- **`nginx.conf`** - Web server config (tự động tạo)

### **Ports sử dụng:**
- **80/443** - HTTP/HTTPS (nginx)
- **8001** - API server (internal)
- **7474** - Neo4J Browser
- **7687** - Neo4J Bolt
- **9090** - Prometheus
- **3000** - Grafana

### **Environment Variables quan trọng:**
```bash
# Server
DOMAIN=your-domain.com
EMAIL=admin@your-domain.com
API_HOST=0.0.0.0
API_PORT=8001

# Authentication
API_SECRET_KEY=fiss-c61197f847cc4682a91ada560bbd7119
REQUIRE_API_KEY=true

# Database
NEO4J_URI=neo4j://35.185.131.185:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=Khongmanh@2001@

# AI
OPENAI_API_KEY=sk-LMnsn4epAmLcPtSNAencVKyhRbkYNqUCMTzBsMIO7F24fbP0
OPENAI_LLM_MODEL=gpt-4o-mini
```

---

## 🔐 **Authentication**

### **API Key Authentication:**
- **Key:** `fiss-c61197f847cc4682a91ada560bbd7119`
- **Header:** `Authorization: Bearer fiss-c61197f847cc4682a91ada560bbd7119`
- **Alternative:** `X-API-Key: fiss-c61197f847cc4682a91ada560bbd7119`

### **Test Authentication:**
```bash
# Test với curl
curl -X POST https://your-domain.com/chat \
  -H "Authorization: Bearer fiss-c61197f847cc4682a91ada560bbd7119" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

---

## 🧪 **Testing**

### **Health Checks:**
```bash
# API Health
curl https://your-domain.com/health

# Neo4J Health
curl http://localhost:7474

# Services status
docker-compose ps
```

### **API Testing:**
```bash
# Swagger UI
https://your-domain.com/api/docs

# Manual test
curl -X POST https://your-domain.com/chat \
  -H "Authorization: Bearer fiss-c61197f847cc4682a91ada560bbd7119" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test insurance query"}'
```

---

## 🔍 **Troubleshooting**

### **Common Issues:**

#### **1. Docker issues:**
```bash
# Check docker status
sudo systemctl status docker

# Restart docker
sudo systemctl restart docker

# Check logs
docker-compose logs -f
```

#### **2. SSL certificate:**
```bash
# Renew certificate
sudo certbot renew

# Test certificate
curl -I https://your-domain.com
```

#### **3. API not responding:**
```bash
# Check API container
docker-compose logs insurance-bot

# Restart API
docker-compose restart insurance-bot

# Check API directly
curl http://localhost:8001/health
```

#### **4. Database connection:**
```bash
# Check Neo4J
curl http://localhost:7474

# Test connection
docker-compose exec neo4j cypher-shell -u neo4j -p Khongmanh@2001@
```

#### **5. Firewall issues:**
```bash
# Check firewall status
sudo ufw status

# Allow ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### **Logs & Monitoring:**
```bash
# View all logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f insurance-bot
docker-compose logs -f neo4j

# System logs
sudo journalctl -u nginx
sudo journalctl -u docker
```

---

## 📞 **Support**

Nếu gặp lỗi, cung cấp thông tin:
- **Error message** cụ thể
- **Bước đang thực hiện**
- **Output của commands:**
  ```bash
  docker-compose ps
  docker-compose logs
  sudo ufw status
  ```

**🎉 Chúc bạn deploy thành công!**
