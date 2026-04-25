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
9. [Known Issues & Fixes](#known-issues--fixes)

---

## Prerequisites

| Tool | Minimum Version | Notes |
|---|---|---|
| Python | 3.10+ | Required for backend and simulator |
| uv | latest | Python package manager — replaces pip/venv |
| Node.js | 20 | Required for frontend |
| Docker | 24 | Required for containerized deployment |
| Docker Compose | 2.x | Included with Docker Desktop |
| PostgreSQL | 15 | Only needed for local dev without Docker |

> Python 3.10 is supported. The `str | None` union syntax works from 3.10+.

### Install uv

```powershell
pip install uv
```

Or via the official installer (recommended):
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

See https://docs.astral.sh/uv/getting-started/installation/ for full options.

---

## Environment Setup

Copy the example env file and fill in secrets:

```powershell
Copy-Item .env.example .env
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

```powershell
cd backend
uv venv
.venv\Scripts\activate
```

**2. Install dependencies**

```powershell
uv pip install -e ".[dev]"
```

**3. Set environment variables**

Create `backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://quarry_user:password@localhost:5432/quarry_monitor
JWT_SECRET=your_jwt_secret
JWT_EXPIRES_IN=3600
```

**4. Start PostgreSQL with TimescaleDB**

If you don't have TimescaleDB locally, use Docker just for the database.

**PowerShell (single line):**
```powershell
docker run -d --name quarry-db -e POSTGRES_USER=quarry_user -e POSTGRES_PASSWORD=password -e POSTGRES_DB=quarry_monitor -p 5432:5432 timescale/timescaledb:latest-pg15
```

**5. Run database migrations**

```powershell
alembic upgrade head
```

**6. Seed the database**

```powershell
python -m app.seed
```

**7. Start the development server**

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is now available at:
- API: http://localhost:8000
- Interactive docs (Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Using Swagger UI

1. Open http://localhost:8000/docs
2. Click **Authorize** (top right)
3. Enter `username` and `password` (leave `client_id` and `client_secret` blank)
4. Click **Authorize** → **Close**
5. All endpoints are now authenticated

> The Swagger Authorize button uses `POST /auth/token` (form data).
> The frontend uses `POST /auth/login` (JSON body). Both work.

### Default Credentials (after seed)

| Username | Password | Role |
|---|---|---|
| `operator` | `operatorpass123` | operator |
| `dispatcher` | `dispatcherpass123` | dispatcher |
| `manager` | `managerpass123` | manager |
| `admin` | `adminpass123` | admin |
| `mechanic` | `mechanicpass123` | mechanic |
| `it` | `itpass123` | IT |
| `owner` | `ownerpass123` | owner |

### Role Permissions

| Action | Allowed Roles |
|---|---|
| Create/update machines | admin, dispatcher |
| Update machine state | dispatcher, operator |
| Resolve conflicts | dispatcher |
| Create/update tasks | operator, dispatcher, admin, manager |
| Validate tasks | dispatcher only |
| Create haul cycles | dispatcher |
| Generate reports | manager, dispatcher, admin, owner |
| View events | manager, dispatcher, admin, owner |
| Create shifts | admin |
| Delete zones | admin |

### Alembic Migration Commands

```powershell
# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# Generate a new migration from model changes
alembic revision --autogenerate -m "describe_your_change"

# Show current migration state
alembic current
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

---

## Client (Frontend)

The frontend is a React + TypeScript SPA located in `frontend/`.

### Local Development (without Docker)

**1. Install dependencies**

```powershell
cd frontend
npm install
```

> If you get ERESOLVE errors, clean and reinstall:
> ```powershell
> Remove-Item -Recurse -Force node_modules
> Remove-Item package-lock.json
> npm install
> ```

**2. Configure API URL**

Create `frontend/.env.local`:

```env
VITE_API_URL=http://localhost:8000
```

> Important: use `localhost` (not `127.0.0.1`) to match the frontend origin and avoid CORS errors.

**3. Start the development server**

```powershell
npm run dev
```

The app is available at http://localhost:5173

> If the browser shows "connection refused", try http://127.0.0.1:5173 instead.
> The `vite.config.ts` uses `host: '0.0.0.0'` to bind on all interfaces.

### Login

Navigate to http://localhost:5173/login and enter credentials from the seed data above.

> The dashboard redirects to `/login` if no token is found in localStorage. This is expected behavior — log in first.

### Available Scripts

```powershell
npm run dev        # Start Vite dev server (hot reload)
npm run build      # TypeScript compile + Vite production build
npm run preview    # Preview production build locally
npm run test       # Run Vitest tests (single run)
```

### Page Overview

| Route | Page | Polling interval |
|---|---|---|
| `/login` | Login | — |
| `/` | Dashboard — machine list + status | 7s |
| `/map` | Map View — machine positions | 7s |
| `/machines/:id` | Machine Detail — state, telemetry, tasks | 7s |
| `/tasks` | Task Panel — active tasks, create form | 7s |
| `/notifications` | Notifications — alerts and conflicts | 7s |

### Authentication Flow

1. Submit credentials on `/login`
2. `POST /auth/login` returns a JWT
3. JWT stored in `localStorage` as `access_token`
4. All API requests include `Authorization: Bearer <token>` header
5. On logout, token is cleared and user is redirected to `/login`

---

## Simulator

The telemetry simulator is a Python async script in `simulator/`. It generates random sensor readings and machine position updates, posting them to the backend every 5 seconds.

### Local Development (without Docker)

**1. Create and activate a virtual environment**

```powershell
cd simulator
uv venv
.venv\Scripts\activate
```

**2. Install dependencies**

```powershell
uv pip install -e .
```

**3. Configure**

Create `simulator/.env`:

```env
API_URL=http://localhost:8000
API_TOKEN=your_jwt_token_here
INTERVAL_MS=5000
# Optional: comma-separated machine UUIDs
# If empty, fetched automatically from GET /machines
MACHINE_IDS=
```

**4. Get a token for the simulator**

```powershell
Invoke-WebRequest -Uri "http://localhost:8000/auth/login" -Method POST -ContentType "application/json" -Body '{"username": "dispatcher", "password": "dispatcherpass123"}' | Select-Object -ExpandProperty Content
```

Or open http://localhost:8000/docs, call `POST /auth/login` from Swagger, and copy the `access_token` from the response.

**5. Run the simulator**

```powershell
python -m simulator.main
```

### Sensor Ranges and Thresholds

| Sensor | Unit | Generated Range | Anomaly Threshold |
|---|---|---|---|
| `engine_temp` | celsius | 60–130 | > 110°C |
| `fuel_level` | percent | 0–100 | < 10% |
| `speed` | kmh | 0–90 | > 80 km/h |
| `payload_weight` | tonnes | 0–70 | > 60t |

Values occasionally exceed thresholds to trigger anomaly detection and alert notifications.

---

## Tests

All property-based tests are in `backend/tests/` and use [hypothesis](https://hypothesis.readthedocs.io/).

### Setup

```powershell
cd backend
uv pip install -e ".[dev]"
```

### Run All Tests

```powershell
pytest
```

### Run a Specific Test File

```powershell
pytest tests/test_auth_properties.py -v
pytest tests/test_machine_properties.py -v
pytest tests/test_telemetry_properties.py -v
pytest tests/test_task_properties.py -v
pytest tests/test_event_zone_report_notification_properties.py -v
```

### Run with Coverage

```powershell
uv pip install pytest-cov
pytest --cov=app --cov-report=term-missing
```

### Test Files and Coverage

| File | Properties | What is tested |
|---|---|---|
| `test_auth_properties.py` | 1–4 | JWT round-trip, wrong secret rejection, malformed token rejection, role enforcement, password hashing |
| `test_machine_properties.py` | 5–12 | State priority invariant, conflict detection, source recording, schema validation |
| `test_telemetry_properties.py` | 13–15 | Payload validation (NaN/Inf rejection), all unit conversions, threshold detection |
| `test_task_properties.py` | 16–23 | Task lifecycle, overdue logic, operator confirmation flow, haul cycle immutability |
| `test_event_zone_report_notification_properties.py` | 24–34 | Event filtering, shift expiry, zone guards, report role restriction, notification ownership |

### Notes

- Each `@given` test runs **100 examples** (`@settings(max_examples=100)`)
- Tests use `sys.modules` stubs — no live database required
- Pure functions tested directly: `resolve_effective_state`, `normalize`, `exceeds_threshold`
- Hypothesis stores its database in `backend/.hypothesis/` — commit this for reproducible shrunk examples

---

## Docker (Full Stack)

### Start Everything

```powershell
docker-compose up --build
```

### Start in Background

```powershell
docker-compose up -d --build
```

### View Logs

```powershell
docker-compose logs -f backend
docker-compose logs -f simulator
docker-compose logs -f frontend
```

### Stop All Services

```powershell
docker-compose down
```

### Stop and Remove Volumes (wipes database)

```powershell
docker-compose down -v
```

### Run Seed After First Start

```powershell
docker-compose exec backend python -m app.seed
```

### Run Migrations Manually

Migrations run automatically on backend startup. To run manually:

```powershell
docker-compose exec backend alembic upgrade head
```

### Service Ports

| Service | Host Port | Notes |
|---|---|---|
| backend | 8000 | API + Swagger docs |
| frontend | 80 | Served via nginx |
| db | 5432 | PostgreSQL + TimescaleDB |
| simulator | — | No exposed port |

---

## API Reference

Full interactive docs: http://localhost:8000/docs

### Authentication

All endpoints except `POST /auth/login` and `POST /auth/token` require:

```
Authorization: Bearer <access_token>
```

### Key Endpoints

```
POST   /auth/login                              Login with JSON body (frontend)
POST   /auth/token                              Login with form data (Swagger UI)
GET    /auth/me                                 Current user info

GET    /machines                                List all machines
POST   /machines                                Create machine (admin, dispatcher)
GET    /machines/{id}                           Get machine by ID
PATCH  /machines/{id}/state                     Update state (dispatcher, operator)
PATCH  /machines/{id}/dispatcher                Assign dispatcher (admin, dispatcher)
POST   /machines/{id}/conflicts/{cid}/resolve   Resolve conflict (dispatcher)

POST   /telemetry                               Ingest telemetry reading
GET    /telemetry/{machine_id}/latest           Latest reading per sensor type
GET    /telemetry/{machine_id}/history          Time-range history

GET    /tasks                                   List tasks (?machine_id=&state=)
POST   /tasks                                   Create task (operator, dispatcher, admin, manager)
GET    /tasks/{id}                              Get task by ID
PATCH  /tasks/{id}                              Update task state
POST   /tasks/{id}/confirm-activation           Dispatcher confirms operator activation

GET    /haul-cycles                             List haul cycles
POST   /haul-cycles                             Create haul cycle (dispatcher)
PATCH  /haul-cycles/{id}/complete               Complete haul cycle (dispatcher)

GET    /events                                  List events (?machine_id=&event_type=&shift_id=)
GET    /shifts                                  List shifts
POST   /shifts                                  Create shift (admin)
PATCH  /shifts/{id}/end                         End shift, expires events (admin)

GET    /zones                                   List zones
POST   /zones                                   Create zone (admin, dispatcher)
PATCH  /zones/{id}                              Update zone (admin, dispatcher)
DELETE /zones/{id}                              Delete zone (admin)
POST   /zones/{id}/machines                     Assign machine to zone (dispatcher)
GET    /zones/{id}/machines                     Get machines in zone

GET    /reports                                 List reports
POST   /reports/generate                        Generate shift report

GET    /notifications                           User notifications (?type=&read=)
PATCH  /notifications/{id}/read                 Mark notification as read
```

---

## Known Issues & Fixes

### `module 'bcrypt' has no attribute '__about__'`
bcrypt 4.x is incompatible with passlib. Pin in `pyproject.toml` (already done):
```
"bcrypt>=3.2.0,<4.0.0"
```

### uv not found after install
Restart your terminal or add `~/.cargo/bin` (or the uv install path) to `PATH`.

### CORS error from frontend to backend
Caused by `allow_credentials=True` + `allow_origins=["*"]` — invalid combination per CORS spec.
Fixed in `backend/app/main.py` — `allow_credentials=False`.
Also ensure `VITE_API_URL=http://localhost:8000` (not `127.0.0.1`) in `frontend/.env.local`.

### Dashboard disappears after login
Was caused by `ProtectedRoute` reading stale React state before localStorage was checked.
Fixed — `ProtectedRoute` now checks localStorage directly as fallback.

### `TypeError: Cannot read properties of undefined (reading 'toUpperCase')`
API returns snake_case (`current_state`) but frontend types used camelCase (`currentState`).
Fixed — all frontend types in `api.types.ts` now use snake_case matching the API.

### PowerShell `--` flag errors
PowerShell treats `--name` as a unary operator. Use single-line commands without `\` continuation.

### `422 Unprocessable Entity` on `POST /auth/login` from Swagger
Swagger Authorize button sends form data, but `/auth/login` expects JSON.
Fixed — added `POST /auth/token` endpoint that accepts form data for Swagger UI.
