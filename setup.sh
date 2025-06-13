#!/bin/bash

# Docker Services Monitoring - Automated Setup Script
# This script automates the entire setup process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect and set Docker Compose command
setup_docker_compose() {
    if command_exists docker-compose; then
        DOCKER_COMPOSE="docker-compose"
    elif docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        return 1
    fi
    return 0
}

# Wrapper function for docker-compose commands
dc() {
    $DOCKER_COMPOSE "$@"
}

# Function to prompt for input with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local result
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " result
        echo "${result:-$default}"
    else
        read -p "$prompt: " result
        echo "$result"
    fi
}

# Function to validate Slack webhook URL
validate_webhook_url() {
    local url="$1"
    if [[ $url =~ ^https://hooks\.slack\.com/services/.+ ]]; then
        return 0
    else
        return 1
    fi
}

print_status "🐳 Docker Services Monitoring - Automated Setup"
echo "=================================================="

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! setup_docker_compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Found Docker Compose: $DOCKER_COMPOSE"

# Check if user is in docker group
if ! groups $USER | grep -q docker; then
    print_warning "User $USER is not in the docker group."
    print_status "Adding user to docker group..."
    sudo usermod -aG docker $USER
    print_warning "You need to log out and back in for group changes to take effect."
    print_warning "After logging back in, run this script again."
    exit 1
fi

print_success "Prerequisites check passed!"

# Create necessary directories
print_status "Creating directories..."
mkdir -p logs
mkdir -p config
print_success "Directories created!"

# Setup environment configuration
print_status "Setting up environment configuration..."

if [ ! -f .env ]; then
    if [ -f config/env.example ]; then
        cp config/env.example .env
        print_success "Created .env from template"
    else
        print_status "Creating .env file..."
        cat > .env << 'EOF'
# Slack Integration
SLACK_WEBHOOK_URL=

# Monitoring Configuration
DAILY_CHECK_TIME=09:00
LOG_LEVEL=INFO
NOTIFICATION_ENABLED=true
INCLUDE_STOPPED_CONTAINERS=true
CONTAINER_NAME_FILTER=
TIMEZONE=UTC

# Docker Configuration
DOCKER_SOCKET=unix://var/run/docker.sock
EOF
        print_success "Created .env file"
    fi
else
    print_warning ".env file already exists, skipping creation"
fi

# Configure Slack webhook
print_status "Configuring Slack integration..."

# Check if webhook is already configured
current_webhook=$(grep "^SLACK_WEBHOOK_URL=" .env | cut -d'=' -f2)

if [ -z "$current_webhook" ] || [ "$current_webhook" = "YOUR_SLACK_WEBHOOK_URL_HERE" ]; then
    echo ""
    echo "🔗 Slack Webhook Setup Required"
    echo "================================"
    echo "To get your Slack webhook URL:"
    echo "1. Go to your Slack workspace"
    echo "2. Click workspace name → Settings & administration → Manage apps"
    echo "3. Search for 'Incoming Webhooks' and add it"
    echo "4. Click 'Add New Webhook to Workspace'"
    echo "5. Choose the channel for notifications"
    echo "6. Copy the webhook URL (starts with https://hooks.slack.com/services/...)"
    echo ""
    
    webhook_url=""
    while [ -z "$webhook_url" ] || ! validate_webhook_url "$webhook_url"; do
        webhook_url=$(prompt_with_default "Enter your Slack webhook URL" "")
        if [ -z "$webhook_url" ]; then
            print_error "Webhook URL is required!"
        elif ! validate_webhook_url "$webhook_url"; then
            print_error "Invalid webhook URL! Must start with https://hooks.slack.com/services/"
        fi
    done
    
    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^SLACK_WEBHOOK_URL=.*|SLACK_WEBHOOK_URL=$webhook_url|" .env
    else
        # Linux
        sed -i "s|^SLACK_WEBHOOK_URL=.*|SLACK_WEBHOOK_URL=$webhook_url|" .env
    fi
    
    print_success "Slack webhook configured!"
else
    print_success "Slack webhook already configured"
fi

# Optional configuration
echo ""
print_status "Optional configuration (press Enter to keep defaults):"

daily_time=$(prompt_with_default "Daily check time (HH:MM format)" "09:00")
log_level=$(prompt_with_default "Log level (DEBUG/INFO/WARNING/ERROR)" "INFO")
include_stopped=$(prompt_with_default "Include stopped containers? (true/false)" "true")

# Update .env with optional settings
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|^DAILY_CHECK_TIME=.*|DAILY_CHECK_TIME=$daily_time|" .env
    sed -i '' "s|^LOG_LEVEL=.*|LOG_LEVEL=$log_level|" .env
    sed -i '' "s|^INCLUDE_STOPPED_CONTAINERS=.*|INCLUDE_STOPPED_CONTAINERS=$include_stopped|" .env
else
    # Linux
    sed -i "s|^DAILY_CHECK_TIME=.*|DAILY_CHECK_TIME=$daily_time|" .env
    sed -i "s|^LOG_LEVEL=.*|LOG_LEVEL=$log_level|" .env
    sed -i "s|^INCLUDE_STOPPED_CONTAINERS=.*|INCLUDE_STOPPED_CONTAINERS=$include_stopped|" .env
fi

print_success "Configuration updated!"

# Build and deploy
print_status "Building and deploying Docker container..."

# Stop any existing containers
if dc ps | grep -q docker-monitor; then
    print_status "Stopping existing container..."
    dc down
fi

# Build and start
print_status "Building Docker image..."
dc build

print_status "Starting Docker container..."
dc up -d

# Wait for container to be ready
print_status "Waiting for container to be ready..."
sleep 5

# Check if container is running
if dc ps | grep -q "Up"; then
    print_success "Container is running!"
else
    print_error "Container failed to start. Checking logs..."
    dc logs docker-monitor
    exit 1
fi

# Test the setup
print_status "Testing the setup..."

# Test Docker connection
print_status "Testing Docker connection..."
if dc exec -T docker-monitor python3 scripts/run_monitor.py --test > /dev/null 2>&1; then
    print_success "Docker connection test passed!"
else
    print_warning "Docker connection test failed. Check logs for details."
fi

# Test Slack notification
echo ""
test_notification=$(prompt_with_default "Send test notification to Slack? (y/n)" "y")
if [[ $test_notification =~ ^[Yy] ]]; then
    print_status "Sending test notification..."
    if dc exec -T docker-monitor python3 scripts/run_monitor.py --test-notification; then
        print_success "Test notification sent! Check your Slack channel."
    else
        print_warning "Test notification failed. Check your webhook URL and try again."
    fi
fi

# Show status
echo ""
print_status "Deployment Summary:"
echo "==================="
dc ps

echo ""
print_success "🎉 Setup completed successfully!"
echo ""
echo "📋 What's running:"
echo "  • Docker container: docker-monitor"
echo "  • Restart policy: unless-stopped"
echo "  • Schedule: Daily at $daily_time"
echo "  • Logs: ./logs/ directory"
echo ""
echo "🔧 Management commands:"
echo "  • View logs:        $DOCKER_COMPOSE logs -f docker-monitor"
echo "  • Restart:          $DOCKER_COMPOSE restart docker-monitor"
echo "  • Stop:             $DOCKER_COMPOSE down"
echo "  • Rebuild:          $DOCKER_COMPOSE up -d --build"
echo "  • Test notification: $DOCKER_COMPOSE exec docker-monitor python3 scripts/run_monitor.py --test-notification"
echo "  • Run once:         $DOCKER_COMPOSE exec docker-monitor python3 scripts/run_monitor.py --once"
echo ""
echo "📊 The service will automatically:"
echo "  • Monitor all Docker containers"
echo "  • Send daily reports to Slack at $daily_time"
echo "  • Restart automatically if it crashes"
echo "  • Start automatically when system boots"
echo ""
print_success "Your Docker monitoring service is now running! 🚀" 