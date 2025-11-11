#!/bin/bash

# =======================================================================
# 🚀 INSURANCE BOT DEPLOYMENT SCRIPT
# =======================================================================
# Description: Automated deployment script for Insurance Bot
# Usage: ./deploy.sh [command]
# Commands: setup, deploy, start, stop, restart, logs, cleanup
# =======================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="insurance-bot"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
DEPLOY_ENV_FILE="deploy.env"

# Functions
print_header() {
    echo -e "${BLUE}=======================================================================${NC}"
    echo -e "${BLUE}🚀 INSURANCE BOT DEPLOYMENT${NC}"
    echo -e "${BLUE}=======================================================================${NC}"
}

print_step() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_requirements() {
    echo "🔍 Checking requirements..."

    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi

    print_step "Requirements check passed"
}

setup_config() {
    echo "⚙️  Setting up configuration..."

    # Copy deploy.env to .env if .env doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$DEPLOY_ENV_FILE" ]; then
            cp "$DEPLOY_ENV_FILE" "$ENV_FILE"
            print_step "Copied $DEPLOY_ENV_FILE to $ENV_FILE"
            print_warning "Please edit $ENV_FILE with your actual configuration values"
            echo "   nano $ENV_FILE  # or vim $ENV_FILE"
        else
            print_error "Configuration file $DEPLOY_ENV_FILE not found!"
            exit 1
        fi
    else
        print_step "Configuration file $ENV_FILE already exists"
    fi

    # Validate required environment variables
    if ! grep -q "OPENAI_API_KEY=" "$ENV_FILE" 2>/dev/null; then
        print_warning "OPENAI_API_KEY not found in $ENV_FILE. Please add it."
    fi

    if ! grep -q "NEO4J_PASSWORD=" "$ENV_FILE" 2>/dev/null; then
        print_warning "NEO4J_PASSWORD not found in $ENV_FILE. Please add it."
    fi
}

build_images() {
    echo "🏗️  Building Docker images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    print_step "Docker images built successfully"
}

start_services() {
    echo "🚀 Starting services..."

    # Load environment variables
    if [ -f "$ENV_FILE" ]; then
        export $(grep -v '^#' "$ENV_FILE" | xargs)
    fi

    # Start services
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

    # Wait for services to be healthy
    echo "⏳ Waiting for services to be ready..."

    # Wait for Neo4J
    echo "   Waiting for Neo4J..."
    for i in {1..30}; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T neo4j cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "MATCH () RETURN count(*) limit 1" &>/dev/null; then
            print_step "Neo4J is ready"
            break
        fi
        echo "   Attempt $i/30..."
        sleep 10
    done

    # Wait for API
    echo "   Waiting for API..."
    API_PORT=${API_PORT:-8001}
    for i in {1..20}; do
        if curl -f "http://localhost:$API_PORT/health" &>/dev/null; then
            print_step "API is ready"
            break
        fi
        echo "   Attempt $i/20..."
        sleep 5
    done

    print_step "All services started successfully"
    echo ""
    echo "🌐 Access URLs:"
    echo "   API: http://localhost:$API_PORT"
    echo "   Swagger UI: http://localhost:$API_PORT/api/docs"
    echo "   Neo4J Browser: http://localhost:7474"
}

stop_services() {
    echo "🛑 Stopping services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    print_step "Services stopped"
}

restart_services() {
    echo "🔄 Restarting services..."
    stop_services
    sleep 2
    start_services
}

show_logs() {
    echo "📋 Showing service logs..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
}

show_status() {
    echo "📊 Service Status:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps

    echo ""
    echo "🏥 Health Checks:"
    API_PORT=${API_PORT:-8001}
    if curl -f "http://localhost:$API_PORT/health" &>/dev/null; then
        echo -e "   API (${API_PORT}): ${GREEN}Healthy${NC}"
    else
        echo -e "   API (${API_PORT}): ${RED}Unhealthy${NC}"
    fi

    if docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T neo4j cypher-shell -u neo4j -p "${NEO4J_PASSWORD:-password}" "MATCH () RETURN count(*) limit 1" &>/dev/null; then
        echo -e "   Neo4J: ${GREEN}Healthy${NC}"
    else
        echo -e "   Neo4J: ${RED}Unhealthy${NC}"
    fi
}

cleanup() {
    echo "🧹 Cleaning up..."

    # Stop and remove containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" down -v

    # Remove images
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --rmi all

    # Remove volumes
    docker volume prune -f

    # Clean logs
    rm -rf logs/*

    print_step "Cleanup completed"
}

import_data() {
    echo "📊 Importing data..."

    API_PORT=${API_PORT:-8001}

    # Wait for API to be ready
    echo "   Waiting for API..."
    for i in {1..20}; do
        if curl -f "http://localhost:$API_PORT/health" &>/dev/null; then
            break
        fi
        sleep 5
    done

    # Run import script inside container
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T insurance-bot python scripts/import_all_legal_docs.py

    print_step "Data import completed"
}

# Main script
print_header

case "${1:-help}" in
    "setup")
        check_requirements
        setup_config
        ;;
    "build")
        check_requirements
        build_images
        ;;
    "start"|"up")
        check_requirements
        start_services
        ;;
    "stop"|"down")
        stop_services
        ;;
    "restart")
        check_requirements
        restart_services
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "import")
        import_data
        ;;
    "deploy")
        check_requirements
        setup_config
        build_images
        start_services
        import_data
        show_status
        ;;
    "help"|*)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  setup    - Setup configuration files"
        echo "  build    - Build Docker images"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show service logs"
        echo "  status   - Show service status"
        echo "  cleanup  - Clean up containers and volumes"
        echo "  import   - Import data to Neo4J"
        echo "  deploy   - Full deployment (setup + build + start + import)"
        echo "  help     - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 deploy          # Full deployment"
        echo "  $0 start           # Start services only"
        echo "  $0 logs            # View logs"
        echo "  $0 status          # Check status"
        echo ""
        echo "Quick start:"
        echo "  1. $0 setup"
        echo "  2. Edit .env file with your API keys"
        echo "  3. $0 deploy"
        ;;
esac
