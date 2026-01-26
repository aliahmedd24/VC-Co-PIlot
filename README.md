# AI VC Co-Pilot

An agentic venture consultancy platform providing AI-powered guidance for startups across all maturity stages.

## Quick Start

### Prerequisites

- Python 3.12+
- Poetry
- Docker & Docker Compose

### Setup

1. **Clone and install dependencies:**
   ```bash
   cd backend
   poetry install
   ```

2. **Copy environment template:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start infrastructure services:**
   ```bash
   docker-compose up -d postgres redis minio
   ```

4. **Run database migrations:**
   ```bash
   cd backend
   poetry run alembic upgrade head
   ```

5. **Start the development server:**
   ```bash
   cd backend
   poetry run uvicorn app.main:app --reload
   ```

6. **Access the API:**
   - API docs: http://localhost:8000/api/v1/docs
   - Health check: http://localhost:8000/health

## Development

```bash
# Run tests
make test

# Run linting
make lint

# Start celery worker
make worker
```

## Project Structure

```
backend/
├── app/
│   ├── api/           # API routes
│   ├── core/          # Business logic (agents, brain, router)
│   ├── models/        # Database models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # External service integrations
│   └── workers/       # Celery background tasks
├── alembic/           # Database migrations
└── tests/             # Test suite
```

## License

Proprietary
