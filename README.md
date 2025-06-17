# 🐳 Docker Container Monitoring with Slack Integration

This Python script monitors Docker containers and sends status reports to Slack with **real-time alerting** capabilities.

## ✨ Features

- 🐳 **Comprehensive Container Monitoring**: Track all containers with detailed metrics
- ⚡ **Real-time Monitoring**: Instant alerts when containers go down, restart, or change status
- 📊 **Performance Analytics**: CPU, memory, network, and disk I/O statistics
- 🔔 **Rich Slack Integration**: Beautiful formatted notifications with status indicators
- 🔄 **Advanced Restart Detection**: Detects both manual and automatic container restarts
- 📅 **Scheduled Reports**: Daily summary reports at configured times
- ⚙️ **Flexible Configuration**: Environment-based configuration with sensible defaults
- 🕐 **Multiple Execution Modes**: One-time, scheduled, continuous, or real-time monitoring
- 🧪 **Built-in Testing**: Connection testing and validation tools
- 🎯 **Container Filtering**: Regex-based container name filtering

## 🏗️ Architecture

This project follows clean architecture principles with proper separation of concerns:

```
docker-services-monitoring/
├── docker_monitor/              # Main package
│   ├── core/                    # Core business logic
│   │   ├── docker_client.py     # Thread-safe Docker daemon interaction
│   │   ├── docker_monitor.py    # Main orchestrator for scheduled 
│   │   ├── realtime_monitor.py  # Real-time monitoring orchestrator
│   │   ├── state_tracker.py     # Container state persistence and retrieval
│   │   ├── change_detector.py   # State difference analysis and change 
│   │   ├── notification_formatter.py # Message creation and formatting
│   │   ├── notification_manager.py   # Notification coordination and 
│   │   ├── cooldown_manager.py  # Notification timing and rate limiting
│   │   └── monitoring_thread.py # Background monitoring loop management
│   ├── integrations/            # External service integrations
│   │   └── slack.py             # Slack notifications
│   ├── utils/                   # Utilities and helpers
│   │   ├── config.py            # Configuration management
│   │   ├── formatters.py        # Data formatting utilities
│   │   └── logging_config.py    # Logging setup
│   ├── cli/                     # Command-line interface
│   │   └── main.py              # CLI entry point
│   ├── exceptions.py            # Custom exception hierarchy
│   └── docker_monitor.py        # Legacy compatibility module
├── scripts/                     # Executable scripts
│   └── run_monitor.py           # Main execution script
├── config/                      # Configuration templates
│   └── env.example              # Environment configuration template
├── tests/                       # Test suite
│   ├── test_config.py           # Configuration tests
│   ├── test_restart_detection.py # Restart detection tests
│   ├── test_slack_integration.py # Slack integration tests
│   └── test_threading.py        # Threading safety tests
├── docker-compose.yml           # Docker Compose configuration
├── Dockerfile                   # Docker image definition
├── setup.sh                     # Universal setup script
└── requirements.txt             # Python dependencies
```

### 🧩 Core Components 

**📊 State Management:**
- **`StateTracker`**: Manages container state persistence, retrieval, and historical tracking
- **`ChangeDetector`**: Analyzes state differences and classifies change types (start/stop/restart)

**🔔 Notification System:**
- **`NotificationFormatter`**: Creates and formats notification messages for different event types
- **`NotificationManager`**: Coordinates notification delivery and handles business logic
- **`CooldownManager`**: Manages notification timing, rate limiting, and prevents spam

**🔄 Monitoring Engine:**
- **`MonitoringThread`**: Handles background monitoring loops with proper thread management
- **`RealTimeMonitor`**: Orchestrates real-time monitoring components
- **`DockerMonitor`**: Orchestrates scheduled monitoring workflows

**🐳 Docker Integration:**
- **`DockerClient`**: Thread-safe Docker daemon interaction with connection pooling

## ⚡ Real-time Monitoring

### What's Implemented
- **Continuous container monitoring** every 10 seconds (configurable)
- **Instant Slack alerts** for container status changes
- **Smart restart detection** distinguishing manual vs automatic restarts
- **Thread-safe operations** with proper locking and resource cleanup

### Alert Types
**🚨 Critical Alerts:**
- Container failures (`running` → `exited`/`stopped`/`dead`)
- Unexpected container removal
- Health check failures

**⚠️ Warning Alerts:**
- Container restart events
- Status transitions

### Usage
```bash
# Real-time monitoring with immediate alerts
docker compose --profile realtime up -d docker-monitor-realtime

# Custom check interval (seconds)
python3 scripts/run_monitor.py --realtime 15

# Combined with daily reports
docker compose --profile realtime up -d  # Runs both services
```

### Restart Detection
The system automatically detects:
- **Manual restarts**: `docker restart <container>` commands
- **Automatic restarts**: Docker policy-based restarts (on-failure, unless-stopped)
- **Failed restarts**: When containers don't come back up

### Example Real-time Alerts
```
🚨 Container Status Alert - CRITICAL
Container: nginx-web
Status Change: running → exited
Time: 2024-01-15 14:23:45

🔄 Container Restart Detected
Container: api-service  
Type: Automatic restart
Status: running ✅
```

## 🚀 Quick Start

### Universal Automated Setup

Get monitoring running in minutes:

```bash
# 1. Clone the project
git clone <repo> docker-services-monitoring
cd docker-services-monitoring

# 2. Run the universal setup
./setup.sh
```

**The setup script automatically handles:**
- ✅ **Environment Detection** - Works on local dev, cloud VMs, production servers
- ✅ **Docker Installation** - Installs Docker if missing
- ✅ **Configuration Setup** - Guides through Slack webhook setup with validation
- ✅ **Container Deployment** - Builds and deploys with restart policies
- ✅ **Testing** - Verifies monitoring and Slack integration work

### Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp config/env.example .env
# Edit .env with your Slack webhook URL

# 3. Choose your monitoring approach:

# Real-time monitoring (recommended for production)
docker compose --profile realtime up -d

# Daily reports only
docker compose up -d docker-monitor

# Test the setup
python3 scripts/run_monitor.py --test
```

## 🔗 Setting Up Slack Webhook

Before running the monitoring system, you need a Slack webhook URL to receive notifications.

### 📱 Quick Setup Guide

**Step 1: Create a Slack App**
- Go to **https://api.slack.com/apps**
- Click the big green **"Create New App"** button
- Select **"From scratch"**
- Enter app name: `Docker Monitor` 
- Choose your Slack workspace from dropdown
- Click **"Create App"**

**Step 2: Enable Incoming Webhooks**
- In your new app's settings, find **"Incoming Webhooks"** in the left menu
- Click the toggle switch to turn it **ON** (it should turn green)
- Click the **"Add New Webhook to Workspace"** button

**Step 3: Choose Channel & Authorize**
- Select the channel where you want alerts (create `#docker-alerts` if needed)
- Click **"Allow"** to give the app permission

**Step 4: Copy Your Webhook URL**
- You'll see a webhook URL that looks like this:
  ```
  https://hooks.slack.com/services/T1234567890/B1234567890/abcdefghijklmnopqrstuvwx
  ```
- **Copy this entire URL** - you'll need it for configuration

### 🔧 Testing Your Webhook
Once you have the webhook URL, test it:

```bash
# Test with curl
curl -X POST -H 'Content-type: application/json' \
--data '{"text":"🧪 Docker Monitor Test - Webhook is working!"}' \
YOUR_WEBHOOK_URL

# Or use the built-in test
python3 scripts/run_monitor.py --test
```

### 📝 Adding to Configuration
Add your webhook URL to the `.env` file:

```bash
# In your .env file
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
```

**💡 Security Tip:** Never commit webhook URLs to version control. Always use environment variables or `.env` files (which should be in `.gitignore`).

## 🧪 Testing the System

### Running Integration Tests
The project includes different types of test files:

#### Pytest Test Suites
These require pytest to run:

```bash
# Install pytest if not already installed
pip install pytest

# Run pytest-based test files
python3 -m pytest tests/test_config.py -v              # Configuration tests
python3 -m pytest tests/test_slack_integration.py -v   # Slack integration tests
```

#### Standalone Test Scripts
These can be run directly with Python:

```bash
# Test restart detection functionality
python3 tests/test_restart_detection.py

# Test threading safety improvements
python3 tests/test_threading.py
```

### System Integration Testing
Test the complete monitoring pipeline:

```bash
# Test Docker connection and basic monitoring
python3 scripts/run_monitor.py --test

# Test Slack webhook integration
python3 scripts/run_monitor.py --test-notification

# Test inside Docker container
docker-compose exec docker-monitor python3 scripts/run_monitor.py --test
```

### Test Results Example
```bash
❯ python3 -m pytest tests/test_config.py -v
========================================= test session starts ==========================================
collected 5 items                                                                                      

tests/test_config.py::TestConfig::test_config_initialization_with_required_env PASSED            [ 20%]
tests/test_config.py::TestConfig::test_config_missing_required_env_raises_error PASSED           [ 40%]
tests/test_config.py::TestConfig::test_default_values PASSED                                     [ 60%]
tests/test_config.py::TestConfig::test_custom_values PASSED                                      [ 80%]
tests/test_config.py::TestConfig::test_get_all_returns_dict PASSED                               [100%]

========================================== 5 passed in 0.09s ===========================================
```

**Note:** The test files use pytest framework and must be run with `python3 -m pytest` rather than direct Python execution.

## 📊 Monitoring Modes

The setup script offers three monitoring modes to suit different needs:

### 1. **Scheduled Monitoring** (Default)
- ✅ **Best for:** Most users, development environments, regular health checks
- 📅 **Frequency:** Daily reports at specified time (default: 9:00 AM)
- 💬 **Notifications:** Comprehensive daily status reports
- 🔋 **Resource Usage:** Minimal - only runs once per day

```bash
# Runs daily at 9 AM
docker compose up -d docker-monitor
```

### 2. **Real-time Monitoring** 
- ✅ **Best for:** Production environments, critical services, immediate alerts
- ⚡ **Frequency:** Continuous monitoring every 10 seconds
- 🚨 **Notifications:** Immediate alerts when containers go down, restart, or fail
- 🔋 **Resource Usage:** Low - efficient state change detection

```bash
# Real-time monitoring with immediate alerts
docker compose --profile realtime up -d docker-monitor-realtime
```

### 3. **Both Modes**
- ✅ **Best for:** Comprehensive monitoring
- 📊 **Combines:** Daily reports + immediate failure alerts
- 💪 **Coverage:** Complete monitoring solution
- 🔋 **Resource Usage:** Moderate - runs both services

```bash
# Run both scheduled and real-time monitoring
docker compose --profile realtime up -d
```

## 🚨 Real-time Alert Examples

When using real-time monitoring, you'll receive immediate Slack notifications for:

**Critical Alerts (🚨):**
- Container goes from `running` → `exited`
- Container goes from `running` → `stopped` 
- Container goes from `running` → `dead`
- Container is unexpectedly removed
- Container restart fails (container doesn't come back up)

**Warning Alerts (⚠️):**
- Container status becomes `restarting`
- Container goes from `healthy` → `unhealthy`
- Container restarts successfully (manual or automatic)

**Restart Detection:**
The system automatically detects and notifies about:
- 🔄 **Manual Restarts**: When someone runs `docker restart <container>`
- 🔄 **Automatic Restarts**: When Docker restarts a container due to restart policies
- 🚨 **Failed Restarts**: When restart attempts fail and container doesn't recover

**Sample Real-time Alerts:**

*Container Failure:*
```
🚨 Container Status Alert - CRITICAL

Container: nginx-web
Status Change: running → exited
Image: nginx:latest
Time: 2024-01-15 14:23:45
Ports: 80→80/tcp, 443→443/tcp
```

*Container Restart:*
```
🚨 Container Removed - CRITICAL

Container: nginx-web
Previous Status: running
Time: 2024-01-15 14:25:10

ℹ️ Container Added

Container: nginx-web
Status: running
Image: nginx:latest
Time: 2024-01-15 14:25:15
```

*Health Check Failure:*
```
⚠️ Container Status Alert - WARNING

Container: api-server
Status Change: running → unhealthy
Image: myapp:latest
Time: 2024-01-15 14:30:22
```

## 🔄 Container Restart Detection

The monitoring system automatically detects:
- **Manual restarts**: `docker restart <container>` commands
- **Automatic restarts**: Docker policy-based restarts (on-failure, unless-stopped)
- **Failed restarts**: When containers don't come back up

## 🚀 Quick Start

### Universal Automated Setup

Get monitoring running in minutes:

```bash
# 1. Clone the project
git clone <repo> docker-services-monitoring
cd docker-services-monitoring

# 2. Run the universal setup
./setup.sh
```

**The setup script automatically handles:**
- ✅ **Environment Detection** - Works on local dev, cloud VMs, production servers
- ✅ **Docker Installation** - Installs Docker if missing
- ✅ **Configuration Setup** - Guides through Slack webhook setup with validation
- ✅ **Container Deployment** - Builds and deploys with restart policies
- ✅ **Testing** - Verifies monitoring and Slack integration work

### Manual Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp config/env.example .env
# Edit .env with your Slack webhook URL

# 3. Choose your monitoring approach:

# Real-time monitoring (recommended for production)
docker compose --profile realtime up -d

# Daily reports only
docker compose up -d docker-monitor

# Test the setup
python3 scripts/run_monitor.py --test
```

## 📊 Monitoring Modes

The setup script offers three monitoring modes to suit different needs:

### 1. **Scheduled Monitoring** (Default)
- ✅ **Best for:** Most users, development environments, regular health checks
- 📅 **Frequency:** Daily reports at specified time (default: 9:00 AM)
- 💬 **Notifications:** Comprehensive daily status reports
- 🔋 **Resource Usage:** Minimal - only runs once per day

```bash
# Runs daily at 9 AM
docker compose up -d docker-monitor
```

### 2. **Real-time Monitoring** 
- ✅ **Best for:** Production environments, critical services, immediate alerts
- ⚡ **Frequency:** Continuous monitoring every 10 seconds
- 🚨 **Notifications:** Immediate alerts when containers go down, restart, or fail
- 🔋 **Resource Usage:** Low - efficient state change detection

```bash
# Real-time monitoring with immediate alerts
docker compose --profile realtime up -d docker-monitor-realtime
```

### 3. **Both Modes**
- ✅ **Best for:** Comprehensive monitoring
- 📊 **Combines:** Daily reports + immediate failure alerts
- 💪 **Coverage:** Complete monitoring solution
- 🔋 **Resource Usage:** Moderate - runs both services

```bash
# Run both scheduled and real-time monitoring
docker compose --profile realtime up -d
```

## 🚨 Real-time Alert Examples

When using real-time monitoring, you'll receive immediate Slack notifications for:

**Critical Alerts (🚨):**
- Container goes from `running` → `exited`
- Container goes from `running` → `stopped` 
- Container goes from `running` → `dead`
- Container is unexpectedly removed
- Container restart fails (container doesn't come back up)

**Warning Alerts (⚠️):**
- Container status becomes `restarting`- Container goes from `healthy` → `unhealthy`
- Container restarts successfully (manual or automatic)

**Restart Detection:**
The system automatically detects and notifies about:
- 🔄 **Manual Restarts**: When someone runs `docker restart <container>`
- 🔄 **Automatic Restarts**: When Docker restarts a container due to restart policies
- 🚨 **Failed Restarts**: When restart attempts fail and container doesn't recover

**Sample Real-time Alerts:**

*Container Failure:*
```
🚨 Container Status Alert - CRITICAL

Container: nginx-web
Status Change: running → exited
Image: nginx:latest
Time: 2024-01-15 14:23:45
Ports: 80→80/tcp, 443→443/tcp
```

*Container Restart:*
```
🚨 Container Removed - CRITICAL

Container: nginx-web
Previous Status: running
Time: 2024-01-15 14:25:10

ℹ️ Container Added

Container: nginx-web
Status: running
Image: nginx:latest
Time: 2024-01-15 14:25:15
```

*Health Check Failure:*
```
⚠️ Container Status Alert - WARNING

Container: api-server
Status Change: running → unhealthy
Image: myapp:latest
Time: 2024-01-15 14:30:22
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_WEBHOOK_URL` | *Required* | Slack incoming webhook URL |
| `DAILY_CHECK_TIME` | `09:00` | Daily check time (HH:MM format) |
| `REALTIME_CHECK_INTERVAL` | `10` | Real-time monitoring interval (seconds) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `DOCKER_SOCKET` | `unix://var/run/docker.sock` | Docker daemon socket |
| `NOTIFICATION_ENABLED` | `true` | Enable/disable Slack notifications |
| `INCLUDE_STOPPED_CONTAINERS` | `true` | Include stopped containers in reports |
| `CONTAINER_NAME_FILTER` | - | Regex pattern to filter container names |
| `TIMEZONE` | `UTC` | Timezone for scheduling |## 📅 Automated Daily Reports

### Universal Cron Job (Recommended)
```bash
# Edit crontab
crontab -e

# Add this line for daily 9 AM reports:
0 9 * * * cd $HOME/docker-services-monitoring && python3 scripts/run_monitor.py --once
```

**Benefits of this approach:**
- ✅ Works on any system with any username
- ✅ Uses environment variable `$HOME`
- ✅ Easy to deploy across different servers

### Alternative Cron Schedules
```bash
# Every day at 8:30 AM
30 8 * * * cd $HOME/docker-services-monitoring && python3 scripts/run_monitor.py --once

# Every Monday at 9 AM
0 9 * * 1 cd $HOME/docker-services-monitoring && python3 scripts/run_monitor.py --once

# Every 6 hours
0 */6 * * * cd $HOME/docker-services-monitoring && python3 scripts/run_monitor.py --once

# Twice daily: 9 AM and 6 PM
0 9,18 * * * cd $HOME/docker-services-monitoring && python3 scripts/run_monitor.py --once
```

## 🏃‍♂️ Production Deployment

### Docker Compose (Recommended)

The easiest way to deploy in production is using Docker Compose with automatic restarts:

#### 1. Setup
```bash
# Ensure you have your .env file configured
cp config/env.example .env
nano .env  # Add your Slack webhook URL

# Create logs directory
mkdir -p logs
```

#### 2. Build and Run
```bash
# Build and start the service
docker-compose up -d

# View logs
docker-compose logs -f docker-monitor

# Check status
docker-compose ps
```

#### 3. Management Commands
```bash
# Stop the service
docker-compose down

# Restart the service
docker-compose restart docker-monitor

# Rebuild after code changes
docker-compose up -d --build

# View real-time logs
docker-compose logs -f docker-monitor

# Run one-time check
docker-compose exec docker-monitor python3 scripts/run_monitor.py --once

# Test notifications
docker-compose exec docker-monitor python3 scripts/run_monitor.py --test-notification
```

#### 4. Configuration

The Docker Compose setup includes:
- ✅ **Automatic restarts** with `restart: unless-stopped`
- ✅ **Health checks** to ensure service is running properly
- ✅ **Docker socket mounting** for container monitoring
- ✅ **Persistent logs** in `./logs` directory
- ✅ **Environment variable** support from `.env` file
- ✅ **Isolated network** for security

#### 5. Customization

You can customize the deployment by editing `docker-compose.yml`:

```yaml
# Change the schedule or run mode
services:
  docker-monitor:
    # ... other config ...
    command: ["python3", "scripts/run_monitor.py", "--continuous", "30"]  # Every 30 minutes
    # OR
    command: ["python3", "scripts/run_monitor.py", "--once"]  # Run once and exit
```

### Production Improvements
- **Thread-Safe Docker Client**: Proper locking mechanisms and resource management
- **Custom Exception Hierarchy**: Structured error handling (DockerMonitorError, ConnectionError, etc.)
- **Resource Optimization**: Alpine-based containers with automatic cleanup



