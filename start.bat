@echo off
echo ========================================
echo GiftGenius Backend - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\" (
    echo [1/4] Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Make sure Python 3.8+ is installed
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

echo.
echo [2/4] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment activated

echo.
echo [3/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed

echo.
echo [4/4] Starting FastAPI server...
echo.
echo ========================================
echo Server will start at: http://localhost:8000
echo Swagger UI: http://localhost:8000/docs
echo Press Ctrl+C to stop the server
echo ========================================
echo.

uvicorn app.main:app --reload
