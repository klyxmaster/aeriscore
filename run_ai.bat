@echo off
setlocal enabledelayedexpansion

:: === LUCID LAUNCHER ===
:: A Mod for Open WebUI

:: === 1. Ask for VENV folder name ===
set /p VENV_NAME=Enter the name of your Python environment folder (e.g., myAI): 
set VENV_PATH=%~dp0..\%VENV_NAME%

:: === 2. Set WebUI path (relative to venv)
set WEBUI_PATH=%VENV_PATH%\Lib\site-packages\open_webui

cd /d "%~dp0"
set "AI_HOME=%CD%"

echo.
echo [SETUP] Checking for required files...

:: Check for personality.txt
if not exist "personality.txt" (
    echo [ERROR] personality.txt is missing. Please place it in this folder.
    pause
    exit /b
)

:: Write base_dir.txt
echo %AI_HOME%> base_dir.txt
:: Default AI name on second line
echo Amicia>> base_dir.txt

echo [INFO] base_dir.txt created/updated.

:: Backup original main.py if not already
if not exist "%WEBUI_PATH%\main.py.bak" (
    copy /Y "%WEBUI_PATH%\main.py" "%WEBUI_PATH%\main.py.bak" >nul
    echo [INFO] Original main.py backed up.
)

:: Inject your custom main.py
copy /Y "%AI_HOME%\main.py" "%WEBUI_PATH%\main.py" >nul
echo [OK] Custom main.py injected.

:: Activate virtual environment
echo.
echo [ACTION] Activating virtual environment...
call "%VENV_PATH%\Scripts\activate.bat"
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Could not activate virtual environment: %VENV_PATH%
    pause
    exit /b
)

:: Install required Python packages
echo [INFO] Installing required Python packages (wikipedia, fastapi, uvicorn)...
pip install wikipedia fastapi uvicorn >nul 2>&1

echo [INFO] Dependencies checked.

:: Launch WebUI
echo [START] Running Open WebUI...
start /wait open-webui serve

:: Restore original main.py
echo [CLEANUP] Restoring original main.py...
copy /Y "%WEBUI_PATH%\main.py.bak" "%WEBUI_PATH%\main.py" >nul
echo [DONE] main.py restored.

:: Countdown to close
for /l %%i in (2,-1,1) do (
    echo Starting in %%i...
    timeout /t 1 >nul
)

exit

