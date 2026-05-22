@echo off
REM start.bat for Windows

set VENV_DIR=venv

REM Check if python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python could not be found. Please install it and add it to your PATH.
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

REM Install requirements
echo Installing/Updating dependencies...
python -m pip install -q --upgrade pip
pip install -q -r requirements.txt

REM Run the application
echo Starting application...
python src\main.py
pause
