@echo off

:: If not running inside Windows Terminal, relaunch it with wt
if "%WT_SESSION%"=="" (
    wt -M new-tab --title "QuickLearner" powershell -NoExit -Command "& '%~f0'"
    exit /b
)

:: 🔧 Garante que o script sempre rode no diretório correto
cd /d "%~dp0"

SETLOCAL

:: Rest of your original script
SET VENV_NAME=venv
SET MAIN_SCRIPT=scripts\main.py

if not exist "%VENV_NAME%\Scripts\activate.bat" (
    echo Error: Virtual environment not found. Run setup.bat first.
    pause
    exit /b 1
)

call "%VENV_NAME%\Scripts\activate"

if exist "%MAIN_SCRIPT%" (
    echo Running main script...
    python "%MAIN_SCRIPT%"
    pause
) else (
    echo Error: Main script not found at %MAIN_SCRIPT%
    pause
)

deactivate
ENDLOCAL