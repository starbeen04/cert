@echo off
chcp 65001 >nul
echo Stopping cert_fast AI Certificate Learning Platform...
echo ================================================

REM Function to safely kill processes on specific ports
echo Stopping backend server on port 8100...
for /f "tokens=2,5" %%a in ('netstat -ano ^| findstr ":8100"') do (
    if not "%%b"=="0" (
        echo Terminating PID %%b on port 8100
        taskkill /f /pid %%b >nul 2>&1
    )
)

echo Stopping frontend server on port 3100...
for /f "tokens=2,5" %%a in ('netstat -ano ^| findstr ":3100"') do (
    if not "%%b"=="0" (
        echo Terminating PID %%b on port 3100
        taskkill /f /pid %%b >nul 2>&1
    )
)

REM Only kill Node.js processes (Vue dev server)
echo Stopping Node.js processes (Vue dev server)...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo csv ^| findstr "node.exe"') do (
    set "pid=%%~i"
    echo Stopping Node.js process !pid!
    taskkill /f /pid !pid! >nul 2>&1
)

echo.
echo ================================================
echo cert_fast servers have been stopped safely.
echo Claude and other Python processes are preserved.
echo ================================================
echo.
pause