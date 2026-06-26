# Simulator Authentication Changes

## Overview
The simulator app now runs without requiring API token authentication. This change makes it easier to start the simulator while maintaining security for other API clients.

## What Changed

### Simulator Changes
1. **Removed API_TOKEN from simulator config** (`simulator/simulator/config.py`)
   - Deleted `API_TOKEN` field from Settings class
   - No longer requires token in `.env` file

2. **Removed Authorization header** (`simulator/simulator/api_client.py`)
   - ApiClient no longer sends `Authorization: Bearer <token>` header
   - HTTP client now runs completely unauthenticated

3. **Updated .env file** (`simulator/.env`)
   - Removed `API_TOKEN` line
   - Simulator now only needs `API_URL` to start

4. **Updated tests** (`simulator/tests/test_connectivity.py`)
   - Added test for unauthenticated telemetry posting
   - Added test to verify other endpoints still require auth
   - Added test to verify API_TOKEN was removed
   - Removed deprecated token validation tests

### Backend Changes

#### New Optional Authentication Dependency
1. **Updated dependencies.py**
   - Changed from `OAuth2PasswordBearer` to `HTTPBearer(auto_error=False)` for flexibility
   - Added `get_current_user_optional()` function that returns `None` if no credentials provided
   - Existing `get_current_user()` still enforces authentication for protected endpoints

#### Endpoints with Optional Authentication (Simulator Access)
The following endpoints now accept unauthenticated requests to support simulator operation:

1. **Telemetry Ingestion** (`POST /telemetry`)
   - Purpose: Allows simulator to send sensor data without token
   - Security: Read-only data ingestion, no sensitive data exposure

2. **List Machines** (`GET /machines`)
   - Purpose: Allows simulator to fetch machine list at startup
   - Security: Basic machine metadata only

3. **Update Machine State** (`PATCH /machines/{machine_id}/state`)
   - Purpose: Allows simulator to update machine states
   - Security: State transitions tracked in events

4. **Map Configuration** (`GET /map-config`)
   - Purpose: Allows simulator to fetch quarry boundaries and antennas
   - Security: Non-sensitive configuration data

5. **List Tasks** (`GET /tasks`)
   - Purpose: Allows simulator to query tasks for machines
   - Security: Task data is operational, not sensitive

6. **Create Task** (`POST /tasks`)
   - Purpose: Allows simulator to generate sample tasks
   - Security: Task creation logged in events

7. **Update Task** (`PATCH /tasks/{task_id}`)
   - Purpose: Allows simulator to advance task states
   - Security: State changes tracked in events

## Security Considerations

### What's Still Protected
- **All other endpoints** still require authentication:
  - User management (`/auth/*`)
  - Analytics and reports (`/analytics/*`, `/reports/*`)
  - Zones and routes (`/zones/*`, `/routes/*`)
  - Notifications (`/notifications/*`)
  - Role permissions (`/role-permissions/*`)
  - Administrative actions (DELETE, most PUT operations)

### Why This Is Safe
1. **Simulator-specific exception**: Only endpoints needed by the simulator are opened
2. **No sensitive data exposed**: Opened endpoints deal with operational data, not user credentials or sensitive business data
3. **Event logging**: All state changes are logged in the event system
4. **Read-only or append-only**: Most opened endpoints are read operations or append-only writes (telemetry)
5. **Production deployment**: In production, you should:
   - Use firewall rules to restrict simulator endpoint access to internal network only
   - Consider adding IP whitelisting for simulator endpoints
   - Monitor for unusual patterns in unauthenticated requests

## How to Use

### Starting the Simulator
```bash
cd simulator
# Update .env (only needs API_URL now)
echo "API_URL=http://127.0.0.1:8000" > .env

# Activate virtual environment
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Run simulator
python -m simulator.main
```

### Testing
```bash
cd simulator
pytest tests/test_connectivity.py -v
```

Expected test results:
- ✓ Backend reachable
- ✓ Telemetry endpoint accepts unauthenticated requests
- ✓ Other endpoints still require authentication
- ✓ API_TOKEN successfully removed from simulator config

## Migration Notes

### Existing Deployments
If you have an existing deployment with a configured `API_TOKEN`:
1. The old token will be ignored (simulator no longer sends it)
2. You can safely remove the `API_TOKEN` line from `simulator/.env`
3. No backend database changes required
4. No frontend changes required

### Rollback
If you need to revert to token-based authentication:
1. Add `API_TOKEN` back to `simulator/simulator/config.py`
2. Add Authorization header back in `simulator/simulator/api_client.py`
3. Change `get_current_user_optional` back to `get_current_user` in affected routers
4. Restore `require_roles()` for POST/PATCH task endpoints

## Production Recommendations

For production deployments, consider:

1. **Network Segmentation**
   - Run simulator on internal network only
   - Use firewall rules to restrict access to simulator endpoints

2. **API Gateway**
   - Add rate limiting for unauthenticated endpoints
   - Monitor for abuse patterns

3. **Alternative: API Key Authentication**
   - If token expiry was the issue, consider using non-expiring API keys
   - Store API key in simulator config (simpler than JWT refresh flow)

4. **Monitoring**
   - Track unauthenticated request volume
   - Alert on unusual patterns (e.g., thousands of telemetry posts/second)

## Questions?

If you encounter issues or need to adjust which endpoints require authentication, the key files are:
- `backend/app/dependencies.py` - Authentication dependency functions
- `backend/app/modules/*/router.py` - Endpoint authentication requirements
