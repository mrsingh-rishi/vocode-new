# AI Voice Agent

An intelligent voice-powered conversational AI agent built with FastAPI, designed for telephony integration with Twilio and real-time streaming conversations.

## Features

- 🎯 **Real-time Voice Conversations**: Stream audio for natural voice interactions
- 📞 **Telephony Integration**: Seamless integration with Twilio for phone calls
- 🤖 **Multiple AI Providers**: Support for OpenAI, Azure OpenAI, and other LLM providers
- 🔊 **Advanced Audio Processing**: Real-time transcription and speech synthesis
- 🚀 **Production Ready**: Docker containerization with Redis for session management
- 📱 **Webhook Support**: Handle inbound/outbound calls with proper webhook endpoints

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry (for local development)
- Docker & Docker Compose (for containerized deployment)
- Redis (handled automatically in Docker setup)

### Environment Setup

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd vocode-new
   make setup
   ```

2. **Configure Environment Variables**
   Edit `.env` file with your API keys:
   ```bash
   # Required API Keys
   OPENAI_API_KEY=your_openai_api_key
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   
   # Optional
   NGROK_AUTH_TOKEN=your_ngrok_token  # For local tunneling
   BASE_URL=your_domain.com          # For production deployment
   ```

## Development Setup

### Local Development

1. **Install Dependencies**
   ```bash
   make install-dev
   ```

2. **Run Application Locally**
   ```bash
   make run
   ```
   The application will be available at `http://localhost:8000`

3. **Development Commands**
   ```bash
   # Interactive chat agent
   make chat
   
   # Test transcription
   make transcribe
   
   # Test speech synthesis
   make synthesize
   
   # Run streaming conversation
   make streaming_conversation
   
   # Run turn-based conversation
   make turn_based_conversation
   ```

### Code Quality

```bash
# Lint code
make lint

# Type checking
make typecheck

# Run tests
make test
```

## Docker Deployment

### Development with Docker

1. **Start Development Stack**
   ```bash
   make docker-compose-up-detached
   ```
   This starts:
   - AI Voice Agent on `http://localhost:8000`
   - Redis on `localhost:6379`

2. **View Logs**
   ```bash
   # All logs
   make docker-logs
   
   # Application logs only
   make docker-logs-app
   
   # Redis logs only
   make docker-logs-redis
   ```

3. **Stop Development Stack**
   ```bash
   make docker-compose-down
   ```

### Production Deployment

1. **Deploy to Production**
   ```bash
   make deploy
   ```

2. **Monitor Services**
   ```bash
   # Check service status
   make status
   
   # Restart services
   make restart
   
   # Stop services
   make stop
   ```

### Docker Commands Reference

| Command | Description |
|---------|-------------|
| `make docker-build` | Build Docker image |
| `make docker-run` | Build and run single container |
| `make docker-compose-up` | Start with logs visible |
| `make docker-compose-up-detached` | Start in background |
| `make docker-compose-down` | Stop all services |
| `make docker-clean` | Clean up containers and volumes |

## API Endpoints

### Telephony Endpoints

- **POST** `/inbound_call` - Handle incoming Twilio calls
- **POST** `/outbound_call` - Initiate outbound calls
- **POST** `/events` - Webhook events from Twilio
- **GET** `/recordings/{conversation_id}` - Retrieve call recordings

### Health & Status

The application runs on port 8000 and provides telephony webhook endpoints for Twilio integration.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio account identifier | Yes |
| `TWILIO_AUTH_TOKEN` | Twilio authentication token | Yes |
| `NGROK_AUTH_TOKEN` | Ngrok token for local tunneling | No |
| `BASE_URL` | Base URL for webhooks | No* |
| `REDIS_URL` | Redis connection URL | No** |

*Required for production deployment  
**Automatically configured in Docker setup

### Twilio Configuration

1. **Configure Webhook URLs** in your Twilio Console:
   - For local development: `https://your-ngrok-url.ngrok.io/inbound_call`
   - For production: `https://your-domain.com/inbound_call`

2. **Phone Number Setup**: Assign your Twilio phone number to use the configured webhook

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Twilio Voice  │◄──►│  AI Voice Agent │◄──►│   OpenAI API    │
│     Service     │    │   (FastAPI)     │    │      LLM        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      Redis      │
                       │   (Sessions)    │
                       └─────────────────┘
```

## Development Workflow

1. **Local Development**
   ```bash
   make setup          # Initial setup
   make install-dev    # Install dependencies
   make run           # Start development server
   ```

2. **Testing Changes**
   ```bash
   make lint          # Code formatting
   make typecheck     # Type validation
   make test          # Run test suite
   ```

3. **Docker Testing**
   ```bash
   make docker-compose-up-detached  # Test in containers
   make docker-logs-app            # Monitor application
   ```

4. **Production Deployment**
   ```bash
   make deploy        # Deploy to production
   make status        # Verify deployment
   ```

## Troubleshooting

### Common Issues

1. **Ngrok Authentication Error**
   - Set `NGROK_AUTH_TOKEN` in your `.env` file
   - Or provide `BASE_URL` for production deployment

2. **Redis Connection Issues**
   - Ensure Redis is running: `make docker-logs-redis`
   - For local development, Redis runs in Docker container

3. **Twilio Webhook Failures**
   - Verify webhook URLs in Twilio Console
   - Check `BASE_URL` configuration
   - Review application logs: `make docker-logs-app`

4. **Docker Port Conflicts**
   - Stop local Redis: `redis-cli shutdown`
   - Check port usage: `lsof -i :8000` and `lsof -i :6379`

### Log Monitoring

```bash
# Real-time application logs
make docker-logs-app

# All service logs
make docker-logs

# Check service health
make status
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and test: `make test`
4. Lint code: `make lint`
5. Commit changes: `git commit -m "Description"`
6. Push and create Pull Request

## Available Commands

Run `make help` to see all available commands:

```bash
make help
```

## License

This project is licensed under the MIT License.
