# 🚀 Server Deployment Guide - Insurance Bot

> Hướng dẫn triển khai Insurance Bot lên production server

## 📋 **Mục lục**

- [Prerequisites](#-prerequisites)
- [Quick Deploy](#-quick-deploy)
- [Manual Setup](#-manual-setup)
- [Configuration](#-configuration)
- [SSL Setup](#-ssl-setup)
- [Monitoring](#-monitoring)
- [Backup & Recovery](#-backup--recovery)
- [Troubleshooting](#-troubleshooting)

---

## 🛠️ **Prerequisites**

### **Server Requirements**
- **OS:** Ubuntu 20.04+ / CentOS 8+ / Debian 10+
- **CPU:** 2+ cores
- **RAM:** 8GB+ (recommended)
- **Disk:** 50GB+ SSD
- **Network:** Public IP + Domain name

### **Software Requirements**
```bash
# Required packages
sudo apt update
sudo apt install -y curl wget git ufw nginx certbot python3-certbot-nginx

# Docker & Docker Compose
sudo apt install -y docker.io docker-compose
sudo systemctl enable docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
# Logout and login again for docker group to take effect
```

### **Domain & DNS**
- Domain name pointed to server IP
- DNS A record configured

---

## 🚀 **Quick Deploy**

### **One-liner Deploy (Production)**
```bash
# Set environment variables
export DOMAIN=your-domain.com
export EMAIL=admin@your-domain.com

# Run deployment
wget -O deploy-server.sh https://raw.githubusercontent.com/your-repo/insurance-bot/main/deploy-server.sh
chmod +x deploy-server.sh
./deploy-server.sh production
```

### **Staging Deploy**
```bash
export DOMAIN=staging.your-domain.com
./deploy-server.sh staging
```

---

## 📋 **Manual Setup**

### **Bước 1: Prepare Server**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install requirements (see Prerequisites)

# Create deploy user (optional)
sudo useradd -m -s /bin/bash deploy
sudo usermod -aG sudo deploy
sudo usermod -aG docker deploy
su - deploy
```

### **Bước 2: Clone Repository**
```bash
cd /opt
sudo mkdir -p insurance-bot
sudo chown $USER:$USER insurance-bot
cd insurance-bot

# Clone your repository
git clone https://github.com/your-username/insurance-bot.git .
# OR copy files manually
```

### **Bước 3: Configure Environment**
```bash
# Copy config template
cp deploy.env .env

# Edit with your settings
nano .env

# Required configurations:
OPENAI_API_KEY=sk-your-openai-key-here
NEO4J_PASSWORD=your-neo4j-password-here
DOMAIN=your-domain.com
EMAIL=admin@your-domain.com

# Production specific
ENVIRONMENT=production
API_PORT=80
```

### **Bước 4: SSL Certificate (Production)**
```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot certonly --standalone -d your-domain.com --email admin@your-domain.com

# Copy certs to project
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem ssl/
sudo chown $USER:$USER ssl/*.pem
```

### **Bước 5: Nginx Reverse Proxy**
```bash
# Create nginx config
sudo tee /etc/nginx/sites-available/insurance-bot <<EOF
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    # SSL redirect (if using SSL)
    # return 301 https://\$server_name\$request_uri;
}

# HTTPS server (if using SSL)
# server {
#     listen 443 ssl http2;
#     server_name your-domain.com;
#
#     ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
#
#     location / {
#         proxy_pass http://localhost:8001;
#         proxy_set_header Host \$host;
#         proxy_set_header X-Real-IP \$remote_addr;
#         proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
#     }
# }
EOF

# Enable site
sudo ln -s /etc/nginx/sites-available/insurance-bot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### **Bước 6: Firewall Setup**
```bash
# UFW firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Check status
sudo ufw status
```

### **Bước 7: Deploy Application**
```bash
# Build and start
docker-compose build --no-cache
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs
```

### **Bước 8: Import Data**
```bash
# Import legal documents
docker-compose exec insurance-bot python scripts/import_all_legal_docs.py

# Check Neo4J data
docker-compose exec neo4j cypher-shell -u neo4j -p your-password "MATCH (n) RETURN count(n) as nodes"
```

---

## ⚙️ **Configuration**

### **Environment Variables**
```bash
# Core settings
API_HOST=0.0.0.0
API_PORT=80
ENVIRONMENT=production

# Database
NEO4J_URI=neo4j://neo4j:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# AI Services
OPENAI_API_KEY=sk-your-key
OPENAI_LLM_MODEL=gpt-4o-mini

# MiniRAG
WORKING_DIR=/app/logs/insurance_rag
KV_STORAGE=JsonKVStorage
VECTOR_STORAGE=NanoVectorDBStorage
GRAPH_STORAGE=Neo4JStorage

# Performance
TOP_K=30
COSINE_THRESHOLD=0.3

# Security
CORS_ORIGINS=https://your-domain.com
API_SECRET_KEY=your-secret-key
```

### **Docker Compose Override**
```yaml
# docker-compose.override.yml
version: '3.8'
services:
  insurance-bot:
    environment:
      - API_PORT=80
      - ENVIRONMENT=production
    ports:
      - "80:80"
    volumes:
      - ./ssl:/app/ssl:ro
```

---

## 🔒 **SSL Setup**

### **Let's Encrypt (Recommended)**
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run
```

### **Custom SSL**
```bash
# Copy certificates
mkdir ssl
cp your-domain.crt ssl/
cp your-domain.key ssl/

# Update docker-compose.yml
volumes:
  - ./ssl:/app/ssl:ro
```

---

## 📊 **Monitoring**

### **Enable Monitoring Stack**
```bash
# Set environment variable
echo "ENABLE_MONITORING=true" >> .env

# Deploy with monitoring
docker-compose --profile monitoring up -d

# Access monitoring
# Prometheus: http://your-server:9090
# Grafana: http://your-server:3000 (admin/admin)
```

### **Application Metrics**
```bash
# View logs
docker-compose logs -f insurance-bot

# Check health
curl https://your-domain.com/health

# Performance monitoring
docker stats
```

### **System Monitoring**
```bash
# System resources
htop
df -h
free -h

# Docker monitoring
docker system df
docker stats --no-stream
```

---

## 💾 **Backup & Recovery**

### **Automated Backup**
```bash
# Backup script is created automatically
./backup.sh

# List backups
ls -la backups/
```

### **Manual Backup**
```bash
# Database backup
docker-compose exec neo4j neo4j-admin database dump neo4j --to-path=/backups/

# Configuration backup
tar -czf backup_$(date +%Y%m%d).tar.gz .env logs/ backups/

# Upload to cloud storage
# scp backup_*.tar.gz user@backup-server:/backups/
```

### **Recovery**
```bash
# Stop services
docker-compose down

# Restore database
docker-compose exec neo4j neo4j-admin database load neo4j --from-path=/backups/

# Restore configuration
tar -xzf backup_20231201.tar.gz

# Start services
docker-compose up -d
```

---

## 🔧 **Troubleshooting**

### **Application Issues**
```bash
# Check container status
docker-compose ps

# View application logs
docker-compose logs insurance-bot

# Check API health
curl http://localhost:8001/health

# Restart application
docker-compose restart insurance-bot
```

### **Database Issues**
```bash
# Check Neo4J status
docker-compose logs neo4j

# Connect to Neo4J
docker-compose exec neo4j cypher-shell -u neo4j -p password

# Restart Neo4J
docker-compose restart neo4j
```

### **Network Issues**
```bash
# Check ports
netstat -tlnp | grep :80
netstat -tlnp | grep :8001

# Test connectivity
curl -I http://localhost
curl -I https://your-domain.com

# Check firewall
sudo ufw status
```

### **Performance Issues**
```bash
# Monitor resources
docker stats

# Check memory usage
free -h

# Check disk space
df -h

# Scale resources
# Edit docker-compose.yml and increase memory limits
```

---

## 🚀 **Scaling & High Availability**

### **Load Balancing**
```nginx
# /etc/nginx/sites-available/insurance-bot
upstream insurance_bot_backend {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    location / {
        proxy_pass http://insurance_bot_backend;
    }
}
```

### **Multiple Instances**
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  insurance-bot:
    scale: 3
    environment:
      - API_PORT=8001
  insurance-bot-2:
    extends: insurance-bot
    environment:
      - API_PORT=8002
  insurance-bot-3:
    extends: insurance-bot
    environment:
      - API_PORT=8003
```

### **Database Clustering**
```yaml
# Neo4J cluster configuration
version: '3.8'
services:
  neo4j-core-1:
    image: neo4j:5-enterprise
    environment:
      NEO4J_dbms_mode:CORE
      NEO4J_causal__clustering_initial__discovery__members:neo4j-core-1:5000,neo4j-core-2:5000,neo4j-core-3:5000
```

---

## 📞 **Support & Maintenance**

### **Regular Maintenance**
```bash
# Weekly tasks
sudo apt update && sudo apt upgrade -y
docker system prune -f
./backup.sh

# Monthly tasks
sudo certbot renew
docker-compose build --no-cache
```

### **Monitoring Alerts**
- Set up alerts for:
  - High CPU/memory usage
  - API response time > 5s
  - Database connection errors
  - SSL certificate expiration

### **Contact Support**
- Check logs: `docker-compose logs`
- Health check: `curl /health`
- Configuration: `nano .env`
- Documentation: This guide

---

## 🎯 **Success Checklist**

- [ ] Server provisioned with required specs
- [ ] Domain DNS configured
- [ ] SSL certificate installed
- [ ] Docker & Docker Compose installed
- [ ] Application deployed successfully
- [ ] API accessible via HTTPS
- [ ] Swagger UI working
- [ ] Data imported to Neo4J
- [ ] Monitoring configured
- [ ] Backup system operational
- [ ] Firewall configured
- [ ] Regular maintenance scheduled

---

**🎉 Chúc mừng! Insurance Bot đã được triển khai thành công lên production server.**

**Truy cập:** `https://your-domain.com/api/docs`
