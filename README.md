# Docker Container Monitoring with Slack Integration

This Python script monitors Docker containers daily and sends status reports to a Slack channel.

## 🏗️ Architecture

This project follows clean architecture principles with proper separation of concerns:

```
docker-services-monitoring/
├── docker_monitor/              # Main package
│   ├── core/                    # Core business logic
│   │   ├── docker_client.py     # Docker daemon interaction
│   │   └── monitor.py           # Main orchestrator
│   ├── integrations/            # External service integrations
│   │   └── slack.py             # Slack notifications
│   ├── utils/                   # Utilities and helpers
│   │   ├── config.py            # Configuration management
│   │   ├── formatters.py        # Data formatting utilities
│   │   └── logging_config.py    # Logging setup
│   └── cli/                     # Command-line interface
│       └── main.py              # CLI entry point
├── scripts/                     # Executable scripts
│   └── run_monitor.py           # Main execution script
├── config/                      # Configuration templates
│   └── env.example              # Environment variables template
├── tests/                       # Test suite
├── .env                         # Your local configuration
├── setup.py                     # Package setup
└── requirements.txt             # Dependencies
```

## ✨ Features

- 🐳 **Comprehensive Container Monitoring**: Track all containers with detailed metrics
- 📊 **Performance Analytics**: CPU, memory, network, and disk I/O statistics
- 🔔 **Rich Slack Integration**: Beautiful formatted notifications with status indicators
- ⚙️ **Flexible Configuration**: Environment-based configuration with sensible defaults
- 🕐 **Multiple Execution Modes**: One-time, scheduled, or continuous monitoring
- 🧪 **Built-in Testing**: Connection testing and validation tools
- 📝 **Logging**: Structured logging with multiple levels
- 🎯 **Container Filtering**: Regex-based container name filtering
- 🔄 **Robust Error Handling**: Graceful failure handling with notifications
- 🛡️ **Security Conscious**: Sensitive data filtering and secure configuration
- 🌍 **Universal Setup**: Works on any Linux system with any username

## 🚀 Quick Start

### Automated Setup (Recommended)

The easiest way to get started is with our automated setup script:

```bash
# 1. Clone or copy the project
git clone <repo> docker-services-monitoring
cd docker-services-monitoring

# 2. Run the automated setup
./setup.sh
```

**That's it!** The script will:
- ✅ Check all prerequisites (Docker, Docker Compose, user permissions)
- ✅ Create necessary directories and configuration files
- ✅ Guide you through Slack webhook setup with validation
- ✅ Configure all settings with sensible defaults
- ✅ Build and deploy the Docker container
- ✅ Test the entire setup automatically
- ✅ Send a test notification to verify Slack integration

### Manual Setup (For Advanced Users)

If you need custom configuration or prefer manual setup:

```bash
# 1. Clone the project
git clone <repo> docker-services-monitoring
cd docker-services-monitoring

# 2. Create configuration
cp config/env.example .env
nano .env  # Add your Slack webhook URL

# 3. Create logs directory
mkdir -p logs

# 4. Build and run
docker compose up -d --build
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SLACK_WEBHOOK_URL` | *Required* | Slack incoming webhook URL |
| `DAILY_CHECK_TIME` | `09:00` | Daily check time (HH:MM format) |
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
