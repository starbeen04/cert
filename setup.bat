@echo off
echo Setting up cert_fast AI Certificate Learning Platform...
echo ================================================

REM 현재 디렉토리 확인
cd /d "%~dp0"
echo Current directory: %CD%

REM Python 가상환경 확인 및 생성
echo.
echo Checking Python virtual environment...
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment. Please ensure Python is installed.
        pause
        exit /b 1
    )
)

REM 가상환경 활성화
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM 백엔드 의존성 설치
echo.
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies.
    pause
    exit /b 1
)

REM 프론트엔드 의존성 설치
echo.
echo Installing frontend dependencies...
cd ..\frontend
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies. Please ensure Node.js and npm are installed.
    pause
    exit /b 1
)

REM 환경 설정 파일 복사
echo.
echo Setting up environment configuration...
cd ..\backend
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo Created .env file from .env.example
        echo Please edit .env file with your database credentials before starting the servers.
    )
)

cd ..

echo.
echo ================================================
echo Setup completed successfully!
echo.
echo Next steps:
echo 1. Edit backend/.env file with your MariaDB database credentials
echo 2. Create the database using database_schema.sql
echo 3. Run start_servers.bat to start both servers
echo.
echo Database setup:
echo - Import database_schema.sql into your MariaDB server
echo - Update backend/.env with your database connection details
echo.
echo ================================================
pause