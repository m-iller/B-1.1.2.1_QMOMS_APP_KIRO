# Quarry Mining Operations Monitoring System

Production-quality MVP for real-time monitoring of quarry mining operations. Tracks machine states, ingests telemetry, manages tasks, detects anomalies, and surfaces conflicts between dispatcher overrides and operator inputs.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0 async |
| Database | PostgreSQL 15 + TimescaleDB |
| Frontend | React 18, TypeScript, Vite |
| Simulator | Python 3.11+, httpx |
| Package manager | uv |
| Deployment | Docker, Docker Compose |

## Project Structure

```
.
├── backend/          # FastAPI modular monolith
├── frontend/         # React + TypeScript SPA
├── simulator/        # Python telemetry simulator
├── docker-compose.yml
├── .env.example
├── README.md
└── INSTRUCTIONS.md
```

## Quick Start

```bash
# 1. Copy environment config
cp .env.example .env

# 2. Start all services
docker-compose up --build

# 3. Seed the database (first run only)
docker-compose exec backend python -m app.seed
```

Services after startup:

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:80 |
| Database | localhost:5432 |

## Default Credentials (after seed)

| Role | Username | Password |
|---|---|---|
| operator | operator | operatorpass123 |
| dispatcher | dispatcher | dispatcherpass123 |
| manager | manager | managerpass123 |
| admin | admin | adminpass123 |
| mechanic | mechanic | mechanicpass123 |
| IT | it | itpass123 |
| owner | owner | ownerpass123 |

## Core Business Rules

1. **State priority**: Dispatcher override > Telemetry > Operator input
2. **Conflicts**: Detected automatically, never auto-resolved — dispatcher must act
3. **Telemetry**: Validated and normalized before storage; raw data never persisted
4. **Tasks**: Operator creates → Dispatcher confirms activation → Dispatcher validates
5. **Haul cycles**: Immutable after completion

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DB_USER` | PostgreSQL username | `quarry_user` |
| `DB_PASSWORD` | PostgreSQL password | — |
| `JWT_SECRET` | JWT signing secret | — |
| `JWT_EXPIRES_IN` | Token lifetime | `8h` |
| `SIM_API_TOKEN` | Simulator auth token | — |
| `VITE_API_URL` | Frontend API base URL | `http://localhost:8000` |

See `INSTRUCTIONS.md` for detailed setup and development guides.
