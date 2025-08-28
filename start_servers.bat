@echo off
chcp 65001 >nul
echo Starting cert_fast AI Certificate Learning Platform...
echo ================================================

REM Check if backend directory exists
if not exist "backend" (
    echo ERROR: Backend directory not found!
    echo Please run this script from the cert_fast root directory.
    pause
    exit /b 1
)

REM Check if frontend directory exists
if not exist "frontend" (
    echo ERROR: Frontend directory not found!
    echo Please run this script from the cert_fast root directory.
    pause
    exit /b 1
)

REM Kill processes on port 8100 (backend)
echo Checking for existing backend server on port 8100...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8100"') do (
    if not "%%a"=="0" (
        echo Terminating process %%a on port 8100
        taskkill /f /pid %%a >nul 2>&1
    )
)

REM Kill processes on port 3100 (frontend)
echo Checking for existing frontend server on port 3100...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3100"') do (
    if not "%%a"=="0" (
        echo Terminating process %%a on port 3100
        taskkill /f /pid %%a >nul 2>&1
    )
)

echo.
echo Starting servers...
echo.

REM Start backend server (new window)
echo Starting FastAPI Backend Server on port 8100...
start "cert_fast Backend" cmd /k "cd /d "%~dp0backend" && python run.py"

REM Wait a moment for backend to start
echo Waiting 3 seconds for backend to initialize...
timeout /t 3 /nobreak >nul

REM Start frontend server (new window)
echo Starting Vue.js Frontend Server on port 3100...
start "cert_fast Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ================================================
echo cert_fast servers are starting...
echo.
echo Backend:  http://localhost:8100
echo Frontend: http://localhost:3100
echo API Docs: http://localhost:8100/docs
echo.
echo Both servers will open in separate command windows.
echo Close those windows to stop the servers.
echo ================================================
echo.
pause