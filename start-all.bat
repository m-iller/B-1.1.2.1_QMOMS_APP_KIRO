@echo off
echo Starting Quarry Mining Operations Monitoring System...
echo.

REM Start Backend
echo [1/3] Starting Backend...
start "Backend" cmd /k "cd backend && .venv\Scripts\activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

REM Start Frontend
echo [2/3] Starting Frontend...
start "Frontend" cmd /k "cd frontend && npm run dev"
timeout /t 5 /nobreak >nul

REM Start Simulator
echo [3/3] Starting Simulator...
start "Simulator" cmd /k "cd simulator && .venv\Scripts\activate && python -m simulator.main"

echo.
echo All services started in separate windows.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo Simulator: Running in background
echo.
echo Press any key to exit this launcher...
pause >nul
