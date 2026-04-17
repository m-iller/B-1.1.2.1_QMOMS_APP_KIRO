# Instructions

Detailed setup and development instructions for each component of the Quarry Mining Operations Monitoring System.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Server (Backend)](#server-backend)
4. [Client (Frontend)](#client-frontend)
5. [Simulator](#simulator)
6. [Tests](#tests)
7. [Docker (Full Stack)](#docker-full-stack)
8. [API Reference](#api-reference)

---

## Prerequisites

| Tool | Minimum Version | Notes |
|---|---|---|
| Python | 3.11 | Required for backend and simulator |
| Node.js | 20 | Required for frontend |
| Docker | 24 | Required for containerized deployment |
| Docker Compose | 2.x | Included with Docker Desktop |
| PostgreSQL | 15 | Only needed for local dev without Docker |

---

## Environment Setup

Copy the example env file and fill in secrets:

```bash
cp .env.example .env
```

Edit `.env`:

```env
DB_USER=quarry_user
DB_PASSWORD=your_secure_password
JWT_SECRET=your_jwt_secret_min_32_chars
JWT_EXPIRES_IN=8h
SIM_API_TOKEN=simulator_token_here
VITE_API_URL=http://localhost:8000
```

> Never commit `.env` to version control. It is gitignored by default.

---

## Server (Backend)

The backend is a Python/FastAPI modular monolith located in `backend/`.

### Local Development (without Docker)

**1. Create and activate a virtual environment**

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -e ".[dev]"
```

**3. Set environment variables**

Create `backend/.env` (or export variables) with at minimum:

```env
DATABASE_URL=postgresql+asyncpg://quarry_user:password@localhost:5432/quarry_monitor
JWT_SECRET=your_jwt_secret
JWT_EXPIRES_IN=3600
```

**4. Start PostgreSQL with TimescaleDB**

If you don't have TimescaleDB locally, use Docker just for the database.

**PowerShell:**
```powershell
docker run -d --name quarry-db -e POSTGRES_USER=quarry_user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=quarry_monitor -p 5432:5432 timescale/timescaledb:latest-pg15
```

**bash / CMD:**
```bash
docker run -d --name quarry-db -e POSTGRES_USER=quarry_user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=quarry_monitor -p 5432:5432 timescale/timescaledb:latest-pg15
```

**5. Run database migrations**

```bash
cd backend
alembic upgrade head
```

**6. Seed the database**

```bash
python -m app.seed
```

**7. Start the development server**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at:
- API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Alembic Migration Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Roll back all migrations
alembic downgrade base

# Generate a new migration from model changes
alembic revision --autogenerate -m "describe_your_change"

# Show current migration state
alembic current

# Show migration history
alembic history
```

### Module Structure

```
backend/app/
├── main.py              # FastAPI app factory, router registration
├── config.py            # pydantic-settings BaseSettings
├── database.py          # Async SQLAlchemy engine + session
├── dependencies.py      # get_db, get_current_user, require_roles
├── seed.py              # Database seed script
├── common/
│   ├── exceptions.py    # NotFoundException, ConflictException, ForbiddenException
│   └── schemas.py       # Shared Pydantic schemas
└── modules/
    ├── auth/            # JWT auth, login, RBAC
    ├── machine/         # Machine CRUD, state management, conflict detection
    ├── telemetry/       # Telemetry ingestion, normalization, anomaly detection
    ├── task/            # Task lifecycle, haul cycles
    ├── event/           # Event store, shift management
    ├── zone/            # Zone CRUD, machine assignment
    ├── report/          # Shift report generation
    └── notification/    # User notifications
```

Each module follows: `router.py → service.py → repository.py → models.py + schemas.py`

### Configuration Reference

All settings are loaded from environment variables via `app/config.py`:

| Variable | Type | Description |
|---|---|---|
| `DATABASE_URL` | str | SQLAlchemy async connection string |
| `JWT_SECRET` | str | Secret key for JWT signing |
| `JWT_EXPIRES_IN` | int | Token expiry in seconds |
| `PORT` | int | Server port (default: 8000) |
| `CORS_ORIGINS` | list | Allowed CORS origins (default: `["*"]`) |

---

## Client (Frontend)

The frontend is a React + TypeScript SPA located in `frontend/`.

### Local Development (without Docker)

**1. Install dependencies**

```bash
cd frontend
npm install
```

**2. Configure API URL**

Create `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

**3. Start the development server**

```bash
npm run dev
```

The app is available at http://localhost:5173

### Build for Production

```bash
npm run build
```

Output is in `frontend/dist/`. The Dockerfile serves this via nginx.

### Available Scripts

```bash
npm run dev        # Start Vite dev server (hot reload)
npm run build      # TypeScript compile + Vite production build
npm run preview    # Preview production build locally
npm run test       # Run Vitest tests (single run, no watch)
```

### Page Overview

| Route | Page | Polling |
|---|---|---|
| `/login` | Login | — |
| `/` | Dashboard — machine list + status | `GET /machines` every 7s |
| `/map` | Map View — machine positions on quarry layout | `GET /machines` every 7s |
| `/machines/:id` | Machine Detail — state, telemetry, tasks | Multiple endpoints every 7s |
| `/tasks` | Task Panel — active tasks, create task form | `GET /tasks` every 7s |
| `/notifications` | Notifications — alerts and conflicts | `GET /notifications` every 7s |

### Authentication Flow

1. User submits credentials on `/login`
2. `POST /auth/login` returns a JWT
3. JWT stored in `localStorage` as `access_token`
4. All API requests include `Authorization: Bearer <token>` header
5. On 401 response, user is redirected to `/login`

### Electron Compatibility

The frontend is structured for future Electron packaging:
- No server-side rendering dependencies
- All API calls use configurable `VITE_API_URL`
- React Router uses `BrowserRouter` (swap to `HashRouter` for Electron)
- No WebSocket dependencies — polling only

---

## Simulator

The telemetry simulator is a Python async script in `simulator/`. It generates random sensor readings and machine position updates, posting them to the backend every 5 seconds.

### Local Development (without Docker)

**1. Create and activate a virtual environment**

```bash
cd simulator
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

**2. Install dependencies**

```bash
pip install -e .
```

**3. Configure**

Create `simulator/.env` or export environment variables:

```env
API_URL=http://localhost:8000
API_TOKEN=your_sim_token
INTERVAL_MS=5000
# Optional: comma-separated machine UUIDs to simulate
# If empty, machine IDs are fetched from GET /machines
MACHINE_IDS=
```

The `API_TOKEN` must match a valid JWT. The easiest approach is to log in as any user and use that token, or create a dedicated service account.

**4. Run the simulator**

```bash
python -m simulator.main
```

The simulator will:
1. Fetch machine IDs from `GET /machines` (or use `MACHINE_IDS` env var)
2. Every `INTERVAL_MS` milliseconds, for each machine:
   - Generate random values for `engine_temp`, `fuel_level`, `speed`, `payload_weight`
   - Update machine position (random walk within quarry grid)
   - POST each reading to `POST /telemetry`
3. Log errors and continue — never crashes on API failure

### Sensor Ranges and Thresholds

| Sensor | Unit | Range | Anomaly Threshold |
|---|---|---|---|
| `engine_temp` | celsius | 60–130 | > 110°C |
| `fuel_level` | percent | 0–100 | < 10% |
| `speed` | kmh | 0–90 | > 80 km/h |
| `payload_weight` | tonnes | 0–70 | > 60t |

Values are generated to occasionally exceed thresholds, triggering anomaly detection and alert notifications.

### Getting a Simulator Token

Option 1 — use the seeded dispatcher account:

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "dispatcher", "password": "dispatcherpass123"}'
```

Copy the `access_token` from the response and set it as `API_TOKEN`.

Option 2 — set `SIM_API_TOKEN` in `.env` and configure the backend to accept it as a static token (requires custom auth middleware — not implemented by default).

---

## Tests

All property-based tests are in `backend/tests/` and use [hypothesis](https://hypothesis.readthedocs.io/).

### Setup

```bash
cd backend
pip install -e ".[dev]"
```

### Run All Tests

```bash
cd backend
pytest
```

### Run a Specific Test File

```bash
pytest tests/test_auth_properties.py
pytest tests/test_machine_properties.py
pytest tests/test_telemetry_properties.py
pytest tests/test_task_properties.py
pytest tests/test_event_zone_report_notification_properties.py
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage

```bash
pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

### Test Files and Coverage

| File | Properties | Modules Covered |
|---|---|---|
| `test_auth_properties.py` | 1–4 | JWT round-trip, invalid credentials, role enforcement, password hashing |
| `test_machine_properties.py` | 5–12 | State priority, conflict detection, source recording, schema validation |
| `test_telemetry_properties.py` | 13–15 | Payload validation, normalization correctness, threshold detection |
| `test_task_properties.py` | 16–23 | Task lifecycle, overdue logic, operator confirmation, haul cycle immutability |
| `test_event_zone_report_notification_properties.py` | 24–34 | Event filtering, shift expiry, zone guards, report roles, notification ownership |

### Property-Based Testing Notes

- Each `@given` test runs **100 examples** by default (`@settings(max_examples=100)`)
- Tests use `sys.modules` stubs to avoid requiring a live database
- Pure functions are tested directly: `resolve_effective_state`, `normalize`, `exceeds_threshold`, `_compute_overdue_logic`
- Hypothesis stores its database in `backend/.hypothesis/` — commit this to get reproducible shrunk examples

### Hypothesis Settings

Global settings are in `backend/pyproject.toml`:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

To increase examples for a deeper search:

```bash
pytest --hypothesis-seed=0 -k test_normalization
```

---

## Docker (Full Stack)

### Start Everything

```bash
docker-compose up --build
```

### Start in Background

```bash
docker-compose up -d --build
```

### View Logs

```bash
docker-compose logs -f backend
docker-compose logs -f simulator
docker-compose logs -f frontend
```

### Stop All Services

```bash
docker-compose down
```

### Stop and Remove Volumes (wipes database)

```bash
docker-compose down -v
```

### Rebuild a Single Service

```bash
docker-compose up --build backend
```

### Run Seed After First Start

```bash
docker-compose exec backend python -m app.seed
```

### Run Migrations Manually

Migrations run automatically on backend startup (`alembic upgrade head` in the Docker entrypoint). To run manually:

```bash
docker-compose exec backend alembic upgrade head
```

### Service Ports

| Service | Host Port | Container Port |
|---|---|---|
| backend | 8000 | 8000 |
| frontend | 80 | 80 |
| db | 5432 | 5432 |
| simulator | — | — (no exposed port) |

---

## API Reference

Full interactive documentation is available at http://localhost:8000/docs when the backend is running.

### Authentication

All endpoints except `POST /auth/login` require a `Bearer` token:

```
Authorization: Bearer <access_token>
```

### Key Endpoints

```
POST   /auth/login                          Login, returns JWT
GET    /auth/me                             Current user info

GET    /machines                            List all machines
POST   /machines                            Create machine (admin, dispatcher)
GET    /machines/{id}                       Get machine by ID
PATCH  /machines/{id}/state                 Update machine state (dispatcher, operator)
PATCH  /machines/{id}/dispatcher            Assign dispatcher (admin, dispatcher)
POST   /machines/{id}/conflicts/{cid}/resolve  Resolve conflict (dispatcher)

POST   /telemetry                           Ingest telemetry reading
GET    /telemetry/{machine_id}/latest       Latest reading per sensor type
GET    /telemetry/{machine_id}/history      Time-range history

GET    /tasks                               List tasks (?machine_id=&state=)
POST   /tasks                               Create task (operator, dispatcher)
GET    /tasks/{id}                          Get task by ID
PATCH  /tasks/{id}                          Update task state
POST   /tasks/{id}/confirm-activation       Dispatcher confirms operator activation

GET    /haul-cycles                         List haul cycles
POST   /haul-cycles                         Create haul cycle (dispatcher)
PATCH  /haul-cycles/{id}/complete           Complete haul cycle (dispatcher)

GET    /events                              List events (?machine_id=&event_type=&shift_id=)
GET    /shifts                              List shifts
POST   /shifts                              Create shift (admin)
PATCH  /shifts/{id}/end                     End shift, expires events (admin)

GET    /zones                               List zones
POST   /zones                               Create zone (admin, dispatcher)
PATCH  /zones/{id}                          Update zone (admin, dispatcher)
DELETE /zones/{id}                          Delete zone (admin)
POST   /zones/{id}/machines                 Assign machine to zone (dispatcher)
GET    /zones/{id}/machines                 Get machines in zone

GET    /reports                             List reports
POST   /reports/generate                    Generate shift report

GET    /notifications                       User's notifications (?type=&read=)
PATCH  /notifications/{id}/read             Mark notification as read
```

### Role Permissions Summary

| Role | Machines | Tasks | Reports | Admin |
|---|---|---|---|---|
| operator | read, update state | create, update | — | — |
| dispatcher | full | full | generate | assign dispatcher |
| manager | read | read | read | — |
| admin | full | read | generate | full |
| mechanic | read | read | — | — |
| IT | read | read | — | — |
| owner | read | read | read | — |
