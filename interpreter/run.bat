@echo off
SETLOCAL

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Create virtual environment
echo Creating Python virtual environment...
python -m venv venv
if %ERRORLEVEL% neq 0 (
    echo Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate venv and install dependencies
echo Installing dependencies...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if %ERRORLEVEL% neq 0 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

:: Run the script
echo Starting the script...
python main.py
if %ERRORLEVEL% neq 0 (
    echo Script execution failed
    pause
    exit /b 1
)

pause