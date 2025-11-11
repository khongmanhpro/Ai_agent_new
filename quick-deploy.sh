#!/bin/bash

# =======================================================================
# 🚀 QUICK DEPLOY - Insurance Bot Server
# =======================================================================
# Description: Script deploy nhanh lên production server
# Usage: ./quick-deploy.sh [domain] [email]
# =======================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DOMAIN=${1:-your-domain.com}
EMAIL=${2:-admin@your-domain.com}

print_header() {
    echo -e "${BLUE}=======================================================================${NC}"
    echo -e "${BLUE}🚀 INSURANCE BOT - QUICK DEPLOYMENT${NC}"
    echo -e "${BLUE}Domain: ${DOMAIN}${NC}"
    echo -e "${BLUE}Email: ${EMAIL}${NC}"
    echo -e "${BLUE}=======================================================================${NC}"
}

check_prerequisites() {
    echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

    # Check if running on Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        echo -e "${RED}❌ This script is designed for Linux servers${NC}"
        exit 1
    fi

    # Check required commands
    local commands=("curl" "wget" "git" "docker" "docker-compose")
    for cmd in "${commands[@]}"; do
        if ! command -v $cmd &> /dev/null; then
            echo -e "${RED}❌ $cmd is not installed${NC}"
            exit 1
        fi
    done

    echo -e "${GREEN}✅ All prerequisites met${NC}"
}

update_config() {
    echo -e "${YELLOW}⚙️ Updating configuration...${NC}"

    # Update .env with provided domain and email
    sed -i "s/DOMAIN=.*/DOMAIN=${DOMAIN}/" .env
    sed -i "s/EMAIL=.*/EMAIL=${EMAIL}/" .env

    echo -e "${GREEN}✅ Configuration updated${NC}"
}

deploy_services() {
    echo -e "${YELLOW}🐳 Deploying services...${NC}"

    # Stop any existing services
    docker-compose down 2>/dev/null || true

    # Start services
    docker-compose up -d

    echo -e "${GREEN}✅ Services deployed${NC}"
}

setup_ssl() {
    echo -e "${YELLOW}🔒 Setting up SSL certificate...${NC}"

    # Wait for nginx to be ready
    sleep 10

    # Get SSL certificate
    certbot --nginx -d ${DOMAIN} --email ${EMAIL} --agree-tos --non-interactive

    echo -e "${GREEN}✅ SSL certificate installed${NC}"
}

health_check() {
    echo -e "${YELLOW}🔍 Running health checks...${NC}"

    # Wait for services to be ready
    sleep 30

    # Check API health
    if curl -f http://localhost:8001/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API is healthy${NC}"
    else
        echo -e "${RED}❌ API health check failed${NC}"
    fi

    # Check Neo4J
    if curl -f http://localhost:7474 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Neo4J is accessible${NC}"
    else
        echo -e "${RED}❌ Neo4J health check failed${NC}"
    fi
}

show_info() {
    echo -e "${BLUE}=======================================================================${NC}"
    echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!${NC}"
    echo -e "${BLUE}=======================================================================${NC}"
    echo ""
    echo -e "${GREEN}🌐 API Endpoints:${NC}"
    echo -e "   Health Check: https://${DOMAIN}/health"
    echo -e "   Swagger UI:   https://${DOMAIN}/api/docs"
    echo -e "   Chat API:     https://${DOMAIN}/chat"
    echo ""
    echo -e "${GREEN}🔐 Authentication:${NC}"
    echo -e "   API Key: fiss-c61197f847cc4682a91ada560bbd7119"
    echo -e "   Header: Authorization: Bearer <API_KEY>"
    echo ""
    echo -e "${GREEN}🛠️ Management Commands:${NC}"
    echo -e "   View logs:    docker-compose logs -f"
    echo -e "   Restart:      docker-compose restart"
    echo -e "   Stop:         docker-compose down"
    echo ""
    echo -e "${BLUE}=======================================================================${NC}"
}

main() {
    print_header
    check_prerequisites
    update_config
    deploy_services
    setup_ssl
    health_check
    show_info
}

# Run main function
main "$@"
