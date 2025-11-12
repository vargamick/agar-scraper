#!/bin/bash
#
# 3DN Scraper API - Start and Test Script
# Starts all services and runs comprehensive tests
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_banner() {
    echo ""
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║                                                            ║${NC}"
    echo -e "${CYAN}║          3DN Scraper API - Start & Test Script            ║${NC}"
    echo -e "${CYAN}║                                                            ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo ""
    echo -e "${BLUE}═══ $1 ═══${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_prerequisites() {
    print_step "Checking Prerequisites"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    print_success "Docker found"

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    print_success "Docker Compose found"

    # Check curl
    if ! command -v curl &> /dev/null; then
        print_error "curl is not installed"
        exit 1
    fi
    print_success "curl found"

    # Check jq
    if ! command -v jq &> /dev/null; then
        print_info "jq not found - installing is recommended for better output"
        print_info "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
        read -p "Continue without jq? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "jq found"
    fi
}

stop_services() {
    print_step "Stopping Existing Services"
    docker-compose down -v 2>/dev/null || true
    print_success "Services stopped"
}

start_services() {
    print_step "Starting Services"

    print_info "Starting PostgreSQL, Redis, Crawl4AI, API, and Celery Worker..."
    docker-compose up -d

    print_success "Services started"

    # Show service status
    echo ""
    docker-compose ps
}

wait_for_services() {
    print_step "Waiting for Services to Be Ready"

    # Wait for PostgreSQL
    print_info "Waiting for PostgreSQL..."
    for i in {1..30}; do
        if docker-compose exec -T postgres pg_isready -U scraper_user -d scraper_db > /dev/null 2>&1; then
            print_success "PostgreSQL is ready"
            break
        fi
        echo -n "."
        sleep 1
    done

    # Wait for Redis
    print_info "Waiting for Redis..."
    for i in {1..30}; do
        if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            print_success "Redis is ready"
            break
        fi
        echo -n "."
        sleep 1
    done

    # Wait for API
    print_info "Waiting for API..."
    for i in {1..60}; do
        if curl -s http://localhost:3010/api/scraper/health > /dev/null 2>&1; then
            print_success "API is ready"
            break
        fi
        echo -n "."
        sleep 2
    done
}

run_migrations() {
    print_step "Running Database Migrations"

    docker-compose exec -T api alembic upgrade head
    print_success "Migrations completed"
}

show_service_info() {
    print_step "Service Information"

    echo ""
    echo "  🌐  API:              http://localhost:3010/api/scraper"
    echo "  📚  API Docs:         http://localhost:3010/api/scraper/docs"
    echo "  📖  ReDoc:            http://localhost:3010/api/scraper/redoc"
    echo "  🗄️   PostgreSQL:      localhost:5432"
    echo "  🔴  Redis:            localhost:6379"
    echo "  🕷️   Crawl4AI:        http://localhost:11235"
    echo ""
}

run_tests() {
    print_step "Running API Tests"

    if [ -f "./test-api.sh" ]; then
        chmod +x ./test-api.sh
        ./test-api.sh
    else
        print_error "test-api.sh not found"
        exit 1
    fi
}

show_logs_option() {
    print_step "Service Logs"

    echo ""
    echo "To view logs, use:"
    echo "  docker-compose logs -f api          # API logs"
    echo "  docker-compose logs -f celery-worker # Worker logs"
    echo "  docker-compose logs -f              # All logs"
    echo ""
}

cleanup() {
    print_step "Cleanup Options"

    echo ""
    echo "To stop services:"
    echo "  docker-compose down"
    echo ""
    echo "To stop and remove all data:"
    echo "  docker-compose down -v"
    echo ""
}

main() {
    print_banner

    # Parse arguments
    RUN_TESTS=true
    SKIP_MIGRATION=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-tests)
                RUN_TESTS=false
                shift
                ;;
            --skip-migration)
                SKIP_MIGRATION=true
                shift
                ;;
            --help)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --no-tests         Start services but don't run tests"
                echo "  --skip-migration   Skip database migration"
                echo "  --help            Show this help message"
                echo ""
                exit 0
                ;;
            *)
                echo "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done

    # Execute steps
    check_prerequisites
    stop_services
    start_services
    wait_for_services

    if [ "$SKIP_MIGRATION" = false ]; then
        run_migrations
    fi

    show_service_info

    if [ "$RUN_TESTS" = true ]; then
        run_tests
    else
        print_info "Skipping tests (use --no-tests flag to skip)"
    fi

    show_logs_option
    cleanup

    print_step "Complete"
    print_success "3DN Scraper API is running and ready!"
    echo ""
}

# Handle Ctrl+C
trap 'echo ""; print_info "Interrupted by user"; exit 130' INT

# Run main
main "$@"
