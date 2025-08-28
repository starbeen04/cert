@echo off
chcp 65001 >nul
echo Stopping cert_fast AI Certificate Learning Platform...
echo ================================================

REM Kill processes on port 8100 (backend)
echo Stopping backend server on port 8100...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8100"') do (
    if not "%%a"=="0" (
        echo Terminating process %%a
        taskkill /f /pid %%a >nul 2>&1
    )
)

REM Kill processes on port 3100 (frontend)
echo Stopping frontend server on port 3100...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3100"') do (
    if not "%%a"=="0" (
        echo Terminating process %%a
        taskkill /f /pid %%a >nul 2>&1
    )
)

REM Kill any remaining Node.js processes (safe to kill all)
echo Stopping any remaining Node.js processes...
taskkill /f /im node.exe >nul 2>&1

REM Note: Python processes are NOT killed globally to prevent terminating other important processes like Claude

echo.
echo ================================================
echo All cert_fast servers have been stopped.
echo ================================================
echo.
pause