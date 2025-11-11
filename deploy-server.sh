#!/bin/bash

# =======================================================================
# 🚀 PRODUCTION DEPLOYMENT - Insurance Bot Server
# =======================================================================
# Description: Deploy Insurance Bot to production server
# Usage: ./deploy-server.sh [environment]
# Environments: staging, production
# =======================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_NAME="insurance-bot"
DOMAIN=${DOMAIN:-your-domain.com}
EMAIL=${EMAIL:-admin@your-domain.com}

print_header() {
    echo -e "${BLUE}=======================================================================${NC}"
    echo -e "${BLUE}🚀 INSURANCE BOT - PRODUCTION DEPLOYMENT${NC}"
    echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
    echo -e "${BLUE}=======================================================================${NC}"
}

check_server_requirements() {
    echo -e "${YELLOW}🔍 Checking server requirements...${NC}"

    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "✅ Linux detected"
    else
        echo -e "${RED}❌ This script is designed for Linux servers${NC}"
        exit 1
    fi

    # Check if running as root or sudo
    if [[ $EUID -eq 0 ]]; then
        echo "⚠️  Running as root - consider using sudo"
    fi

    # Check required commands
    local commands=("curl" "wget" "git" "docker" "docker-compose")
    for cmd in "${commands[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            echo "✅ $cmd available"
        else
            echo -e "${RED}❌ $cmd not found. Please install it first.${NC}"
            case $cmd in
                docker)
                    echo "   Ubuntu/Debian: sudo apt install docker.io docker-compose"
                    echo "   CentOS/RHEL: sudo yum install docker docker-compose"
                    ;;
                git)
                    echo "   Ubuntu/Debian: sudo apt install git"
                    ;;
            esac
            exit 1
        fi
    done

    # Check available memory
    local mem_kb=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    local mem_gb=$((mem_kb / 1024 / 1024))
    if [ $mem_gb -lt 4 ]; then
        echo -e "${YELLOW}⚠️  Low memory: ${mem_gb}GB. Recommended: 8GB+${NC}"
    else
        echo "✅ Memory: ${mem_gb}GB"
    fi

    # Check available disk space
    local disk_gb=$(df / | tail -1 | awk '{print int($4/1024/1024)}')
    if [ $disk_gb -lt 20 ]; then
        echo -e "${YELLOW}⚠️  Low disk space: ${disk_gb}GB. Recommended: 50GB+${NC}"
    else
        echo "✅ Disk space: ${disk_gb}GB"
    fi
}

setup_directories() {
    echo -e "${YELLOW}📁 Setting up directories...${NC}"

    # Create main directory
    sudo mkdir -p "/opt/${PROJECT_NAME}"
    sudo chown $USER:$USER "/opt/${PROJECT_NAME}"

    # Create subdirectories
    mkdir -p "/opt/${PROJECT_NAME}/logs"
    mkdir -p "/opt/${PROJECT_NAME}/backups"
    mkdir -p "/opt/${PROJECT_NAME}/ssl"

    echo "✅ Directories created in /opt/${PROJECT_NAME}"
}

clone_repository() {
    echo -e "${YELLOW}📥 Cloning repository...${NC}"

    local repo_url=${REPO_URL:-"https://github.com/your-username/insurance-bot.git"}

    if [ -d "/opt/${PROJECT_NAME}/.git" ]; then
        echo "📦 Repository already exists, pulling latest changes..."
        cd "/opt/${PROJECT_NAME}"
        git pull origin main
    else
        echo "📦 Cloning repository..."
        git clone "$repo_url" "/opt/${PROJECT_NAME}"
        cd "/opt/${PROJECT_NAME}"
    fi

    echo "✅ Repository ready"
}

setup_environment() {
    echo -e "${YELLOW}⚙️  Setting up environment...${NC}"

    cd "/opt/${PROJECT_NAME}"

    # Copy environment template
    if [ -f "deploy.env" ]; then
        cp deploy.env .env
        echo "✅ Environment template copied"
    else
        echo -e "${RED}❌ deploy.env not found${NC}"
        exit 1
    fi

    # Update environment-specific settings
    case $ENVIRONMENT in
        production)
            sed -i 's/ENVIRONMENT=.*/ENVIRONMENT=production/' .env
            sed -i 's/DEPLOY_TARGET=.*/DEPLOY_TARGET=server/' .env
            sed -i 's/API_PORT=.*/API_PORT=80/' .env
            sed -i 's/CORS_ORIGINS=.*/CORS_ORIGINS=https:\/\/your-domain.com/' .env
            ;;
        staging)
            sed -i 's/ENVIRONMENT=.*/ENVIRONMENT=staging/' .env
            sed -i 's/DEPLOY_TARGET=.*/DEPLOY_TARGET=server/' .env
            sed -i 's/API_PORT=.*/API_PORT=8080/' .env
            ;;
    esac

    echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file with your actual API keys!${NC}"
    echo "   nano .env"
    echo ""
    echo "   Required settings:"
    echo "   - OPENAI_API_KEY=your-key-here"
    echo "   - NEO4J_PASSWORD=your-password"
    echo "   - DOMAIN=your-domain.com (if using SSL)"
    echo ""
    read -p "Press Enter after editing .env file..."
}

setup_ssl() {
    echo -e "${YELLOW}🔒 Setting up SSL certificates...${NC}"

    if [ "$ENVIRONMENT" = "production" ] && [ -n "$DOMAIN" ]; then
        echo "📜 Setting up Let's Encrypt SSL for $DOMAIN"

        # Install certbot if not available
        if ! command -v certbot &> /dev/null; then
            echo "Installing certbot..."
            sudo apt update
            sudo apt install -y certbot python3-certbot-nginx
        fi

        # Get SSL certificate
        sudo certbot certonly --standalone -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive

        if [ $? -eq 0 ]; then
            echo "✅ SSL certificate obtained"

            # Copy certs to project directory
            sudo cp "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" "ssl/"
            sudo cp "/etc/letsencrypt/live/$DOMAIN/privkey.pem" "ssl/"
            sudo chown $USER:$USER ssl/*.pem

            echo "✅ SSL certificates copied to ssl/ directory"
        else
            echo -e "${RED}❌ SSL certificate generation failed${NC}"
        fi
    else
        echo "⏭️  Skipping SSL setup (not production or no domain specified)"
    fi
}

setup_nginx() {
    echo -e "${YELLOW}🌐 Setting up Nginx reverse proxy...${NC}"

    # Create nginx config
    local nginx_config="/etc/nginx/sites-available/${PROJECT_NAME}"

    sudo tee "$nginx_config" > /dev/null <<EOF
# Insurance Bot Nginx Configuration
upstream insurance_bot {
    server localhost:8001;
}

server {
    listen 80;
    server_name $DOMAIN;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # API endpoints
    location /api/ {
        proxy_pass http://insurance_bot;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;

        # API specific settings
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/${PROJECT_NAME}/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        proxy_pass http://insurance_bot;
        access_log off;
    }
}
EOF

    # Enable site
    sudo ln -sf "$nginx_config" "/etc/nginx/sites-enabled/"
    sudo nginx -t
    sudo systemctl reload nginx

    echo "✅ Nginx configured and reloaded"
}

setup_firewall() {
    echo -e "${YELLOW}🔥 Setting up firewall...${NC}"

    # Check if ufw is available
    if command -v ufw &> /dev/null; then
        echo "Setting up UFW firewall..."

        # Allow SSH
        sudo ufw allow ssh

        # Allow HTTP and HTTPS
        sudo ufw allow 80
        sudo ufw allow 443

        # Enable firewall
        sudo ufw --force enable

        echo "✅ UFW firewall configured"
    else
        echo "⚠️  UFW not available, configure firewall manually"
        echo "   Allow ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)"
    fi
}

deploy_application() {
    echo -e "${YELLOW}🚀 Deploying application...${NC}"

    cd "/opt/${PROJECT_NAME}"

    # Build and start services
    echo "Building Docker images..."
    docker-compose build --no-cache

    echo "Starting services..."
    docker-compose up -d

    echo "⏳ Waiting for services to be ready..."
    sleep 30

    # Check if services are running
    if docker-compose ps | grep -q "Up"; then
        echo "✅ Services started successfully"
    else
        echo -e "${RED}❌ Services failed to start${NC}"
        docker-compose logs
        exit 1
    fi
}

setup_monitoring() {
    echo -e "${YELLOW}📊 Setting up monitoring...${NC}"

    # Install monitoring services if requested
    if [ "${ENABLE_MONITORING:-false}" = "true" ]; then
        echo "Setting up Prometheus and Grafana..."

        # Add monitoring profile to docker-compose
        docker-compose --profile monitoring up -d

        echo "✅ Monitoring services started"
        echo "   Prometheus: http://localhost:9090"
        echo "   Grafana: http://localhost:3000"
    fi

    # Setup log rotation
    sudo tee "/etc/logrotate.d/${PROJECT_NAME}" > /dev/null <<EOF
/opt/${PROJECT_NAME}/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $USER $USER
    postrotate
        docker-compose -f /opt/${PROJECT_NAME}/docker-compose.yml logs -f insurance-bot > /dev/null 2>&1 || true
    endscript
}
EOF

    echo "✅ Log rotation configured"
}

setup_backup() {
    echo -e "${YELLOW}💾 Setting up backup...${NC}"

    # Create backup script
    tee "backup.sh" > /dev/null <<EOF
#!/bin/bash
# Backup script for Insurance Bot

BACKUP_DIR="/opt/${PROJECT_NAME}/backups"
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="${PROJECT_NAME}_\${TIMESTAMP}"

echo "Creating backup: \$BACKUP_NAME"

# Create backup directory
mkdir -p "\$BACKUP_DIR/\$BACKUP_NAME"

# Backup database
echo "Backing up Neo4J database..."
docker-compose exec -T neo4j neo4j-admin database dump neo4j --to-path=/backups/\$BACKUP_NAME/

# Backup logs
cp -r logs "\$BACKUP_DIR/\$BACKUP_NAME/"

# Backup configuration
cp .env "\$BACKUP_DIR/\$BACKUP_NAME/"

# Compress backup
cd "\$BACKUP_DIR"
tar -czf "\${BACKUP_NAME}.tar.gz" "\$BACKUP_NAME"
rm -rf "\$BACKUP_NAME"

echo "✅ Backup completed: \$BACKUP_DIR/\${BACKUP_NAME}.tar.gz"

# Clean old backups (keep last 7 days)
find "\$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
EOF

    chmod +x backup.sh

    # Setup cron job for daily backup
    local cron_job="0 2 * * * /opt/${PROJECT_NAME}/backup.sh"
    (crontab -l ; echo "$cron_job") | crontab -

    echo "✅ Backup system configured (daily at 2 AM)"
}

create_systemd_service() {
    echo -e "${YELLOW}🔧 Creating systemd service...${NC}"

    # Create systemd service file
    sudo tee "/etc/systemd/system/${PROJECT_NAME}.service" > /dev/null <<EOF
[Unit]
Description=Insurance Bot Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/${PROJECT_NAME}
User=$USER
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
ExecReload=/usr/bin/docker-compose restart
TimeoutStartSec=900

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable "${PROJECT_NAME}"

    echo "✅ Systemd service created"
    echo "   Start: sudo systemctl start ${PROJECT_NAME}"
    echo "   Stop: sudo systemctl stop ${PROJECT_NAME}"
    echo "   Status: sudo systemctl status ${PROJECT_NAME}"
}

final_verification() {
    echo -e "${YELLOW}✅ Running final verification...${NC}"

    cd "/opt/${PROJECT_NAME}"

    # Check API health
    echo "Checking API health..."
    if curl -f "http://localhost:8001/health" &>/dev/null; then
        echo "✅ API is healthy"
    else
        echo -e "${RED}❌ API health check failed${NC}"
    fi

    # Check Neo4J
    echo "Checking Neo4J..."
    if docker-compose exec -T neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" "MATCH () RETURN count(*) limit 1" &>/dev/null; then
        echo "✅ Neo4J is healthy"
    else
        echo -e "${RED}❌ Neo4J health check failed${NC}"
    fi

    # Show access URLs
    echo ""
    echo "🎉 Deployment completed successfully!"
    echo ""
    echo "🌐 Access URLs:"
    if [ "$ENVIRONMENT" = "production" ] && [ -n "$DOMAIN" ]; then
        echo "   Production: https://$DOMAIN"
        echo "   API Docs: https://$DOMAIN/api/docs"
    else
        echo "   API: http://$(hostname -I | awk '{print $1}'):8001"
        echo "   API Docs: http://$(hostname -I | awk '{print $1}'):8001/api/docs"
        echo "   Neo4J Browser: http://$(hostname -I | awk '{print $1}'):7474"
    fi
    echo ""
    echo "📋 Management commands:"
    echo "   Status: docker-compose ps"
    echo "   Logs: docker-compose logs -f"
    echo "   Restart: docker-compose restart"
    echo "   Backup: ./backup.sh"
    echo ""
    echo "🆘 Support:"
    echo "   Logs: docker-compose logs > debug.log"
    echo "   Config: nano .env"
    echo "   Update: git pull && docker-compose up --build -d"
}

# Main deployment
main() {
    print_header

    echo "🚀 Starting deployment process..."
    echo ""

    check_server_requirements
    echo ""

    setup_directories
    echo ""

    clone_repository
    echo ""

    setup_environment
    echo ""

    setup_ssl
    echo ""

    setup_nginx
    echo ""

    setup_firewall
    echo ""

    deploy_application
    echo ""

    setup_monitoring
    echo ""

    setup_backup
    echo ""

    create_systemd_service
    echo ""

    final_verification
}

# Run main function
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "update")
        echo "🔄 Updating deployment..."
        cd "/opt/${PROJECT_NAME}"
        git pull origin main
        docker-compose build --no-cache
        docker-compose up -d
        echo "✅ Update completed"
        ;;
    "backup")
        cd "/opt/${PROJECT_NAME}"
        ./backup.sh
        ;;
    "status")
        cd "/opt/${PROJECT_NAME}"
        docker-compose ps
        ;;
    *)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy  - Full deployment"
        echo "  update  - Update application"
        echo "  backup  - Create backup"
        echo "  status  - Show service status"
        echo ""
        echo "Environment variables:"
        echo "  ENVIRONMENT=production|staging"
        echo "  DOMAIN=your-domain.com"
        echo "  EMAIL=admin@your-domain.com"
        ;;
esac
