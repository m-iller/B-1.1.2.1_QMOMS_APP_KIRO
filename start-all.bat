@echo off
echo Starting Quarry Mining Operations Monitoring System...
echo.

REM Start Backend
echo [1/3] Starting Backend...
start "Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for backend to be ready by checking health endpoint
echo Waiting for backend to be ready...
set /a attempts=0
:wait_backend
set /a attempts+=1
if %attempts% gtr 30 (
    echo Backend failed to start after 30 seconds
    goto continue_startup
)
timeout /t 1 /nobreak >nul
powershell -Command "try { Invoke-WebRequest -Uri 'http://localhost:8000/health' -UseBasicParsing -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo Attempt %attempts%: Backend not ready yet...
    goto wait_backend
)
echo Backend is ready!
echo.

:continue_startup
REM Start Frontend
echo [2/3] Starting Frontend...
start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"
timeout /t 5 /nobreak >nul

REM Start Simulator
echo [3/3] Starting Simulator...
start "Simulator" cmd /k "cd /d "%~dp0simulator" && .venv\Scripts\python.exe -m simulator.main"

echo.
echo All services started in separate windows.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo Simulator: Running in background
echo.
echo Press any key to exit this launcher...
pause >nul
