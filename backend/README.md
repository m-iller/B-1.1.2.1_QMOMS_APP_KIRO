# QMOMS Backend

FastAPI-based modular monolith for the Quarry Mining Operations Monitoring System.

## Architecture

The backend follows a modular monolith architecture with feature-based modules:

### Modules

- **auth** - JWT-based authentication and role-based access control
- **machine** - Machine CRUD, state management, and conflict detection
- **telemetry** - Sensor data ingestion, validation, normalization, and anomaly detection
- **task** - Task lifecycle management and haul cycle tracking
- **event** - System event tracking and audit trail
- **zone** - Geographic/operational area management
- **route** - Machine route planning and assignment
- **report** - Shift report generation and retrieval
- **notification** - User notification management
- **map_config** - Map configuration and coordinate calibration
- **analytics** - Real-time metrics and KPIs
- **role_permissions** - Fine-grained access control system
- **dev** - Development utilities and debugging endpoints

### Common Infrastructure

- **database.py** - AsyncPG connection management and session factory
- **dependencies.py** - FastAPI dependency injection utilities
- **config.py** - Environment-based configuration with Pydantic Settings
- **common/** - Shared base classes, exceptions, and utilities

## Tech Stack

- **Python** ≥3.10
- **FastAPI** ≥0.111.0 - Async web framework with automatic OpenAPI docs
- **SQLAlchemy** ≥2.0.0 - ORM with async support
- **AsyncPG** ≥0.29.0 - High-performance PostgreSQL async driver
- **Alembic** ≥1.13.0 - Database schema migrations
- **Pydantic** ≥2.7.0 - Data validation and settings
- **python-jose** ≥3.3.0 - JWT token encoding/decoding
- **Passlib** ≥1.7.4 - Password hashing with bcrypt

## Development

### Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies (requires uv)
uv pip install -e ".[dev]"

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
```

### Database

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Seed database with initial data
python -m app.seed
```

### Running

```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

API documentation available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_machine.py

# Run property-based tests with verbose output
pytest -v tests/property/

# Run with hypothesis statistics
pytest --hypothesis-show-statistics
```

## Testing Strategy

The backend uses a hybrid testing approach:

### Property-Based Testing (Hypothesis)

Used for core business logic that must hold universally:
- **Conflict resolution** - Multiple conflicts resolved correctly by ID
- **State priority** - Dispatcher > Telemetry > Operator ordering
- **Telemetry normalization** - Unit conversions preserve values within tolerance
- **Coordinate transformations** - Round-trip pixel↔world conversions

Property tests generate thousands of test cases automatically.

### Example-Based Testing (Pytest)

Used for:
- API endpoint contracts
- Authentication and authorization
- Database repository functions
- Error handling and validation

## API Structure

### Authentication
- `POST /auth/login` - User login with JWT token
- `GET /auth/me` - Get current user info

### Machines
- `GET /machines` - List all machines
- `POST /machines` - Create machine (admin/dispatcher)
- `GET /machines/{id}` - Get machine details
- `PATCH /machines/{id}/state` - Update machine state
- `POST /machines/{machine_id}/conflicts/{conflict_id}/resolve` - Resolve conflict

### Telemetry
- `POST /telemetry` - Ingest sensor readings (used by simulator)
- `GET /telemetry/{machine_id}` - Get machine telemetry history

### Tasks
- `GET /tasks` - List tasks (filterable by machine, state)
- `POST /tasks` - Create task
- `PATCH /tasks/{id}` - Update task state

### Map
- `GET /map-config` - Get map configuration
- `PUT /map-config` - Update map config (dispatcher/admin)
- `POST /map-config/upload` - Upload map image

### Reports
- `POST /reports/generate` - Generate shift report
- `GET /reports` - List generated reports

### Notifications
- `GET /notifications` - Get user notifications
- `PATCH /notifications/{id}/read` - Mark as read

### Analytics
- `GET /analytics/kpis` - Real-time KPI metrics

## Environment Variables

| Variable | Description | Required | Default |
|---|---|---|---|
| `DB_USER` | PostgreSQL username | Yes | - |
| `DB_PASSWORD` | PostgreSQL password | Yes | - |
| `DB_HOST` | PostgreSQL host | No | `localhost` |
| `DB_PORT` | PostgreSQL port | No | `5432` |
| `DB_NAME` | Database name | No | `quarry_monitor` |
| `JWT_SECRET` | Secret key for JWT signing | Yes | - |
| `JWT_ALGORITHM` | JWT algorithm | No | `HS256` |
| `JWT_EXPIRES_IN` | Token lifetime | No | `8h` |
| `API_PREFIX` | API route prefix | No | `` |
| `CORS_ORIGINS` | Allowed CORS origins | No | `*` |

## Database Schema

The schema includes tables for:
- `users` - User accounts and roles
- `machines` - Fleet equipment
- `machine_states` - State history and conflicts
- `conflicts` - Dispatcher-operator disagreements
- `telemetry_data` - Processed sensor readings
- `anomalies` - Threshold violations
- `tasks` - Work assignments
- `haul_cycles` - Immutable trip records
- `events` - Audit trail
- `zones` - Geographic areas
- `routes` - Planned paths
- `reports` - Generated shift reports
- `notifications` - User alerts
- `map_config` - Map calibration
- `antennas` - Position reference points
- `role_permissions` - Access control matrix

See `alembic/versions/` for migration history.

## Code Structure

```
app/
├── modules/
│   ├── auth/
│   │   ├── router.py      # FastAPI routes
│   │   ├── service.py     # Business logic
│   │   ├── repository.py  # Database queries
│   │   ├── models.py      # SQLAlchemy models
│   │   └── schemas.py     # Pydantic schemas
│   └── [other modules follow same pattern]
├── common/
│   ├── base.py           # Base model classes
│   ├── exceptions.py     # Custom exceptions
│   └── response.py       # Standard API responses
├── main.py               # FastAPI app factory
├── database.py           # DB connection setup
├── dependencies.py       # DI helpers
├── config.py             # Settings
└── seed.py               # Database seeding

tests/
├── property/             # Property-based tests
│   ├── test_conflict_resolution.py
│   └── test_coordinate_transforms.py
├── test_auth.py
├── test_machine.py
└── conftest.py           # Pytest fixtures
```

## Adding a New Module

1. Create module directory under `app/modules/`
2. Add `models.py` with SQLAlchemy models
3. Add `schemas.py` with Pydantic request/response schemas
4. Add `repository.py` with database query functions
5. Add `service.py` with business logic
6. Add `router.py` with FastAPI routes
7. Register router in `app/main.py`
8. Create migration: `alembic revision --autogenerate -m "add module"`
9. Add tests in `tests/test_module.py`

## Common Issues

### Database connection errors
- Verify PostgreSQL is running: `docker ps` or `systemctl status postgresql`
- Check `.env` database credentials
- Ensure database exists: `createdb quarry_monitor`

### Migration conflicts
- If migrations are out of sync: `alembic downgrade base && alembic upgrade head`
- For development, can drop and recreate: `docker-compose down -v && docker-compose up`

### JWT errors
- Verify `JWT_SECRET` is set in `.env`
- Token expiry: login again to get fresh token
- Check token format in Authorization header: `Bearer <token>`

## Contributing

- Follow existing code structure (models → repository → service → router)
- Add type hints to all function signatures
- Write property-based tests for business logic invariants
- Write example tests for API contracts
- Run `pytest` before committing
- Use meaningful migration messages
