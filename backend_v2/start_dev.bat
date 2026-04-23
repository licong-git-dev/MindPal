@echo off
REM MindPal Backend V2 - Development Start Script

echo ============================================
echo   MindPal Backend V2 - Development Server
echo ============================================

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo Installing dependencies...
    pip install -r requirements.txt -q
)

REM Initialize database if not exists
if not exist "mindpal.db" (
    echo Initializing database...
    python -m scripts.init_db
)

echo.
echo Starting server...
echo API Docs: http://localhost:8000/docs
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
