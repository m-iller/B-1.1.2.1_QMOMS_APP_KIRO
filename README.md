# Quarry Mining Operations Monitoring System (QMOMS)

Production-quality MVP for real-time monitoring of quarry mining operations. Tracks machine states, ingests telemetry, manages tasks, detects anomalies, and surfaces conflicts between dispatcher overrides and operator inputs.

## Stack

| Layer | Technology | Version |
|---|---|---|
| Backend | Python, FastAPI, SQLAlchemy 2.0 async | Python ≥3.10 |
| Database | PostgreSQL + AsyncPG | PostgreSQL 15+ |
| Frontend | React, TypeScript, Vite | React 18.3 |
| State Management | React Context API | - |
| HTTP Client | Axios | 1.7.0 |
| Map Rendering | MapLibre GL JS | 4.5.0 |
| PDF Generation | jsPDF + html2canvas | 2.5.1 / 1.4.1 |
| Routing | React Router DOM | 6.23.0 |
| Simulator | Python, httpx | Python ≥3.10 |
| Testing | Pytest, Hypothesis (backend), Vitest, fast-check (frontend) | - |
| Package Manager | uv (backend), npm (frontend) | - |
| Deployment | Docker, Docker Compose | - |

## Project Structure

```
.
├── backend/          # FastAPI modular monolith
│   ├── app/
│   │   ├── modules/  # Feature modules (auth, machine, telemetry, task, etc.)
│   │   ├── common/   # Shared utilities and base classes
│   │   ├── main.py   # FastAPI application entry point
│   │   ├── database.py
│   │   └── seed.py   # Database seeding script
│   ├── alembic/      # Database migrations
│   ├── tests/        # Backend tests (Pytest + Hypothesis)
│   └── pyproject.toml
├── frontend/         # React + TypeScript SPA
│   ├── src/
│   │   ├── pages/    # Dashboard, MapView, MachineDetail, TaskPanel, etc.
│   │   ├── components/
│   │   ├── context/  # Auth and global state management
│   │   ├── hooks/    # Custom React hooks (polling, auth, etc.)
│   │   └── types/
│   ├── tests/        # Frontend tests (Vitest + fast-check)
│   └── package.json
├── simulator/        # Python telemetry simulator with antenna-based positioning
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

| Role | Username | Password | Access Level |
|---|---|---|---|
| operator | operator | operatorpass123 | Machine state input, task creation |
| dispatcher | dispatcher | dispatcherpass123 | Machine state override, conflict resolution, task validation |
| manager | manager | managerpass123 | Reports, analytics, read-only dashboard |
| admin | admin | adminpass123 | User management, system configuration |
| mechanic | mechanic | mechanicpass123 | Machine health, telemetry viewing |
| IT | it | itpass123 | System infrastructure settings |
| owner | owner | ownerpass123 | Full read access across all modules |
| dev | dev | devpass123 | Development utilities and debugging |

## Implemented Features

### Core System (✅ Complete)
- **Authentication & Authorization**: JWT-based auth with 7 role types (operator, dispatcher, manager, admin, mechanic, IT, owner)
- **Machine Management**: Full CRUD for machines with state tracking and conflict detection
- **State Priority System**: Dispatcher override > Telemetry > Operator input
- **Conflict Management**: Automatic detection with manual dispatcher resolution (bug fix in progress for multiple conflicts)
- **Telemetry Ingestion**: Real-time sensor data processing with validation and normalization
- **Anomaly Detection**: Threshold-based alerting on telemetry values
- **Task Management**: Task lifecycle with operator creation and dispatcher validation
- **Haul Cycle Tracking**: Immutable haul trip records
- **Event System**: Comprehensive audit trail for all significant actions
- **Zone Management**: Geographic/operational area organization
- **Shift Reporting**: Automated shift reports with machine utilization and task metrics
- **Notifications**: Role-based notifications for alerts and conflicts
- **Analytics Dashboard**: Real-time metrics and KPIs for managers and dispatchers
- **Role & Permissions Management**: Fine-grained access control system
- **Route Planning**: Machine route assignment and tracking

### Map Module (✅ Complete)
- **Interactive Map View**: MapLibre GL-based real-time machine positioning
- **Configurable Background**: Upload custom quarry map images or use Google Maps screenshots
- **Coordinate Calibration**: Pixel-to-real-world coordinate mapping
- **Antenna Reference Points**: Configurable positioning reference markers (minimum 1, no maximum)
- **Position Telemetry**: Real-time machine position updates via telemetry pipeline
- **Antenna-Based Simulation**: Simulator emits position estimates with Gaussian noise modeling real positioning systems

### Frontend Pages (✅ Complete)
- Dashboard with machine overview
- Interactive Map View with real-time positions
- Machine Detail view with telemetry and task summaries
- Task Panel for task management
- Notifications Panel for alerts and conflicts
- Shift Report generation and viewing
- Analytics Dashboard with KPIs
- Zones Management
- Routes Management
- Roles & Permissions configuration

### In Progress
- **Multiple Conflicts Resolution Fix**: Bug fix for resolving specific conflicts by ID when multiple conflicts exist (tasks 3.3-3.6 pending)

## Future Enhancements
- TimescaleDB integration for optimized time-series storage
- Advanced route optimization algorithms
- Predictive maintenance using ML models
- Mobile application for field operators
- Real-time WebSocket updates (currently using polling)
- Multi-quarry support for enterprise deployments

## Core Business Rules

1. **State priority**: Dispatcher override > Telemetry > Operator input
2. **Conflicts**: Detected automatically, never auto-resolved — dispatcher must act
3. **Telemetry**: Validated and normalized before storage; raw data never persisted
4. **Tasks**: Operator creates → Dispatcher confirms activation → Dispatcher validates
5. **Haul cycles**: Immutable after completion
6. **Position Updates**: Modeled as antenna-derived estimates with configurable noise for realistic simulation
7. **Map Calibration**: Real-world coordinates mapped to pixels via configurable bounds

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DB_USER` | PostgreSQL username | `quarry_user` |
| `DB_PASSWORD` | PostgreSQL password | — |
| `DB_HOST` | PostgreSQL host | `localhost` |
| `DB_PORT` | PostgreSQL port | `5432` |
| `DB_NAME` | Database name | `quarry_monitor` |
| `JWT_SECRET` | JWT signing secret | — |
| `JWT_EXPIRES_IN` | Token lifetime | `8h` |
| `SIM_API_TOKEN` | Simulator auth token | — |
| `SIM_NUM_ANTENNAS` | Number of simulated antennas | `3` |
| `SIM_POSITION_NOISE_SIGMA` | Position estimate noise (meters) | `2.0` |
| `VITE_API_URL` | Frontend API base URL | `http://localhost:8000` |

## Key Backend Dependencies

- **FastAPI** ≥0.111.0 - Modern async web framework
- **SQLAlchemy** ≥2.0.0 - ORM with async support
- **AsyncPG** ≥0.29.0 - High-performance PostgreSQL driver
- **Alembic** ≥1.13.0 - Database migrations
- **Pydantic** ≥2.7.0 - Data validation and settings management
- **python-jose** ≥3.3.0 - JWT token handling
- **Passlib** ≥1.7.4 - Password hashing with bcrypt
- **Pytest** + **Hypothesis** - Testing with property-based testing
- **httpx** ≥0.27.0 - Async HTTP client

## Key Frontend Dependencies

- **React** 18.3.0 - UI library
- **TypeScript** 5.4.0 - Type safety
- **Vite** 6.3.0 - Build tool and dev server
- **React Router DOM** 6.23.0 - Client-side routing
- **Axios** 1.7.0 - HTTP client
- **MapLibre GL** 4.5.0 - Interactive map rendering
- **jsPDF** + **html2canvas** - PDF report generation
- **Vitest** + **fast-check** - Testing with property-based testing

## Development Commands

### Backend
```bash
cd backend

# Install dependencies
uv pip install -e ".[dev]"

# Run migrations
alembic upgrade head

# Seed database
python -m app.seed

# Run tests
pytest

# Run property-based tests with verbose output
pytest -v tests/

# Start dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

### Simulator
```bash
cd simulator

# Run simulator (requires backend running)
python main.py
```

See `INSTRUCTIONS.md` for detailed setup and development guides.
