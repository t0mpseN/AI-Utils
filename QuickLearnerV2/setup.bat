@echo off
SETLOCAL

:: Configuration
SET VENV_NAME=venv
SET REQUIREMENTS_FILE=requirements.txt

:: Check Python
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in PATH
    pause
    exit /b 1
)

:: Create virtual environment
echo Creating virtual environment...
python -m venv %VENV_NAME%
if %ERRORLEVEL% neq 0 (
    echo Error: Failed to create virtual environment
    pause
    exit /b 1
)

:: Install dependencies
echo Installing dependencies...
call %VENV_NAME%\Scripts\activate
pip install --upgrade pip

if exist %REQUIREMENTS_FILE% (
    pip install -r %REQUIREMENTS_FILE%
    echo Dependencies installed successfully!
    pause
) else (
    echo Warning: requirements.txt not found
    pause
)

deactivate
echo Setup complete!
pause
ENDLOCAL