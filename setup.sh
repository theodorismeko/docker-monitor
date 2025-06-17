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

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_warning "Running as root user detected!"
    print_warning "For best practices (especially on cloud VMs), it's recommended to:"
    print_warning "1. Run as regular user (not root)"
    print_warning "2. Add user to docker group: sudo usermod -aG docker \$USER"
    print_warning "3. Log out and back in, then run: ./setup.sh"
    echo ""
    read -p "Continue anyway as root? (y/N): " continue_as_root
    if [[ ! $continue_as_root =~ ^[Yy] ]]; then
        print_error "Exiting. Please run as regular user for best practices."
        exit 1
    fi
fi

print_status "🐳 Docker Services Monitoring - Universal Setup"
echo "================================================="
print_status "Supports: Local development, Cloud VMs, Production servers"
echo ""

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists docker; then
    print_warning "Docker is not installed."
    if [ "$EUID" -eq 0 ] || command -v sudo >/dev/null 2>&1; then
        print_status "Installing Docker automatically..."
        if command -v curl >/dev/null 2>&1; then
            curl -fsSL https://get.docker.com -o get-docker.sh
            if [ "$EUID" -eq 0 ]; then
                sh get-docker.sh
            else
                sudo sh get-docker.sh
            fi
            rm get-docker.sh
            print_success "Docker installed successfully!"
        else
            print_error "curl not found. Please install Docker manually: https://docs.docker.com/get-docker/"
            exit 1
        fi
    else
        print_error "Docker is not installed and cannot install automatically."
        print_error "Please install Docker first: https://docs.docker.com/get-docker/"
        exit 1
    fi
fi

if ! setup_docker_compose; then
    print_error "Docker Compose is not available."
    print_error "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

print_success "Found Docker Compose: $DOCKER_COMPOSE"

# Handle Docker group permissions intelligently
print_status "Setting up Docker permissions..."
current_user=${SUDO_USER:-$USER}

if [ "$EUID" -eq 0 ]; then
    # Running as root - handle the original user
    if [ -n "$SUDO_USER" ]; then
        if ! groups $SUDO_USER | grep -q docker; then
            print_status "Adding user $SUDO_USER to docker group..."
            usermod -aG docker $SUDO_USER
            print_success "User $SUDO_USER added to docker group."
            print_warning "The user $SUDO_USER needs to log out and back in for changes to take effect."
        else
            print_success "User $SUDO_USER is already in docker group!"
        fi
    else
        print_warning "Running as root - Docker group not needed for root user."
    fi
elif ! groups $USER | grep -q docker; then
    print_status "Adding user $USER to docker group..."
    if sudo usermod -aG docker $USER; then
        print_success "User $USER added to docker group!"
        print_status "Attempting to refresh group membership..."
        
        # Try to refresh group membership without logout
        if command -v newgrp >/dev/null 2>&1; then
            print_status "Refreshing group membership with newgrp..."
            exec newgrp docker "$0" "$@"
        else
            print_warning "Group membership refreshed. Testing Docker access..."
            # Test if Docker works now
            if docker ps >/dev/null 2>&1; then
                print_success "Docker access confirmed!"
            else
                print_warning "You may need to log out and back in for Docker group changes to take effect."
                print_warning "After logging back in, run this script again."
                exit 1
            fi
        fi
    else
        print_error "Failed to add user to docker group. Please run with sudo or as root."
        exit 1
    fi
else
    print_success "User $USER is already in docker group!"
fi

# Test Docker access
print_status "Testing Docker daemon access..."
if ! docker ps >/dev/null 2>&1; then
    print_error "Cannot access Docker daemon."
    print_error "Please ensure:"
    print_error "1. Docker daemon is running: sudo systemctl start docker"
    print_error "2. User is in docker group: sudo usermod -aG docker \$USER"
    print_error "3. Log out and back in if group was just added"
    exit 1
fi

print_success "Docker daemon access confirmed!"

# Create necessary directories
print_status "Creating directories..."
mkdir -p logs
mkdir -p config
print_success "Directories created!"

# Fix file permissions (especially important for cloud VMs)
print_status "Ensuring proper file permissions..."
if [ "$EUID" -eq 0 ]; then
    # Running as root - ensure files are owned by the correct user
    if [ -n "$SUDO_USER" ]; then
        chown -R $SUDO_USER:$SUDO_USER .
        print_success "File ownership set to $SUDO_USER"
    fi
else
    # Running as regular user - fix any root-owned files
    if [ -f .env ] && [ "$(stat -c %U .env)" = "root" ]; then
        print_status "Fixing .env file ownership..."
        sudo chown $USER:$USER .env
    fi
    
    # Ensure script is executable
    chmod +x setup.sh 2>/dev/null || true
fi
print_success "File permissions verified!"

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

# Set monitoring mode to both (all services)
monitoring_mode=3
print_status "Deployment mode: Running both scheduled and real-time monitoring (all services)"

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
print_status "Building and deploying all Docker services..."

# Stop any existing containers
if dc ps | grep -q docker-monitor; then
    print_status "Stopping existing containers..."
    dc --profile realtime down
fi

# Build and start all services
print_status "Building Docker images..."
dc build

print_status "Starting all monitoring services (scheduled + real-time)..."
dc --profile realtime up -d

# Wait for container(s) to be ready
print_status "Waiting for container(s) to be ready..."
sleep 5

# Check if containers are running
if dc ps | grep -q "Up"; then
    print_success "Container(s) are running!"
else
    print_error "Container(s) failed to start. Checking logs..."
    dc logs
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
echo "  • Scheduled monitoring: Daily reports at $daily_time"
echo "  • Real-time monitoring: Immediate alerts for container failures"
echo "  • Containers: docker-monitor, docker-monitor-realtime"
echo "  • Restart policy: unless-stopped"
echo "  • Logs: ./logs/ directory"
echo ""
echo "🔧 Management commands:"
echo "  • View all logs:    $DOCKER_COMPOSE --profile realtime logs -f"
echo "  • View scheduled:   $DOCKER_COMPOSE logs -f docker-monitor"
echo "  • View real-time:   $DOCKER_COMPOSE --profile realtime logs -f docker-monitor-realtime"
echo "  • Restart all:      $DOCKER_COMPOSE --profile realtime restart"
echo "  • Stop all:         $DOCKER_COMPOSE --profile realtime down"
echo "  • Test notification: $DOCKER_COMPOSE exec docker-monitor python3 scripts/run_monitor.py --test-notification"
echo ""
echo "📊 The service will automatically:"
echo "  • Monitor all Docker containers (scheduled + real-time)"
echo "  • Send daily reports to Slack at $daily_time"
echo "  • Send immediate alerts when containers go down"
echo "  • Restart automatically if services crash"
echo "  • Start automatically when system boots"
echo ""
print_success "Your Docker monitoring service is now running! 🚀" 