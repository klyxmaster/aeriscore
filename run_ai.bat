@echo off
setlocal enabledelayedexpansion

:: === LUCID LAUNCHER ===
:: A Mod for Open WebUI

:: === 1. Ask for VENV folder name ===
set /p VENV_NAME=Enter the name of your Python environment folder (e.g., myAI): 

:: Resolve full venv path
pushd "%~dp0.."
set VENV_PATH=%CD%\%VENV_NAME%
popd

:: Set WebUI path (where main.py is)
set WEBUI_PATH=%VENV_PATH%\Lib\site-packages\open_webui
set AI_HOME=%~dp0

:: Check for required files
if not exist "%AI_HOME%\personality.txt" (
    echo [ERROR] personality.txt is missing. Please place it in this folder.
    pause
    exit /b
)

:: Create base_dir.txt only if missing
if not exist "%AI_HOME%\base_dir.txt" (
    echo %AI_HOME%> "%AI_HOME%\base_dir.txt"
    echo Amicia>> "%AI_HOME%\base_dir.txt"
    echo You>> "%AI_HOME%\base_dir.txt"
    echo [INFO] base_dir.txt created with default values.
) else (
    echo [INFO] base_dir.txt already exists. Not overwriting.
)

:: Backup original main.py if needed
if not exist "%WEBUI_PATH%\main.py.bak" (
    copy /Y "%WEBUI_PATH%\main.py" "%WEBUI_PATH%\main.py.bak"
    echo [INFO] Original main.py backed up.
)

:: Ensure WEBUI_PATH exists
if not exist "%WEBUI_PATH%" (
    echo [ERROR] WEBUI_PATH folder doesn't exist. Aborting.
    pause
    exit /b
)

:: Copy custom main.py
copy /Y "%AI_HOME%\main.py" "%WEBUI_PATH%\main.py"
if errorlevel 1 (
    echo [ERROR] Failed to copy main.py. Check paths.
    pause
    exit /b
)
echo [OK] Custom main.py injected.

:: Activate virtual environment
call "%VENV_PATH%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b
)

:: Install Python dependencies
echo [INFO] Installing required Python packages...
pip install wikipedia fastapi uvicorn >nul 2>&1
echo [INFO] Dependencies checked.

:: Launch Open WebUI
echo [START] Running Open WebUI...
start /wait open-webui serve

:: Restore original main.py
echo [CLEANUP] Restoring original main.py...
copy /Y "%WEBUI_PATH%\main.py.bak" "%WEBUI_PATH%\main.py"
echo [DONE] main.py restored.

:: Countdown before exit
for /l %%i in (3,-1,1) do (
    echo Exiting in %%i...
    timeout /t 1 >nul
)

exit
