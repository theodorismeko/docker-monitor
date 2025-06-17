# Docker Container Monitoring with Slack Integration

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
│   │   ├── monitor.py           # Main orchestrator
│   │   └── realtime_monitor.py  # Real-time monitoring engine
│   ├── integrations/            # External service integrations
│   │   └── slack.py             # Slack notifications
│   ├── utils/                   # Utilities and helpers
│   │   ├── config.py            # Configuration management
│   │   ├── formatters.py        # Data formatting utilities
│   │   └── logging_config.py    # Logging setup
│   ├── exceptions.py            # Custom exception hierarchy
│   └── cli/                     # Command-line interface
│       └── main.py              # CLI entry point
├── scripts/                     # Executable scripts
├── config/                      # Configuration templates
├── tests/                       # Test suite
└── requirements.txt             # Dependencies
```

## ⚡ Real-time Monitoring

### What's Implemented
- **Continuous container monitoring** every 15 seconds (configurable)
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

Before running the monitoring system, you'll need to create a Slack webhook URL:

### Method 1: Slack App (Recommended)
1. **Go to [Slack API](https://api.slack.com/apps)**
2. **Click "Create New App"** → Choose "From scratch"
3. **Name your app** (e.g., "Docker Monitor") and select your workspace
4. **Navigate to "Incoming Webhooks"** in the left sidebar
5. **Toggle "Activate Incoming Webhooks"** to ON
6. **Click "Add New Webhook to Workspace"**
7. **Choose the channel** where you want notifications (e.g., #alerts, #monitoring)
8. **Click "Allow"** to authorize the webhook
9. **Copy the webhook URL** - it looks like:
   ```
   https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX
   ```

### Method 2: Browser/Workspace Settings
1. **Open your Slack workspace** in browser
2. **Go to Settings & Administration** → Manage Apps
3. **Search for "Incoming WebHooks"** and add it
4. **Choose a channel** for notifications
5. **Click "Add Incoming WebHooks Integration"**
6. **Copy the webhook URL** from the setup page
7. **Optionally customize** the webhook name and icon

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
| `TIMEZONE` | `UTC` | Timezone for scheduling |

## 📅 Automated Daily Reports

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
