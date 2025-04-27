@echo off
setlocal enabledelayedexpansion

:: === INIQUITY-25 LAUNCHER ===
:: Smarter version: venv creation, backup/restore, dependency check

:: --- Ask for environment name ---
set /p VENV_NAME=Choose your Python venv folder name (e.g., myAI): 

:: --- Calculate initial paths ---
pushd "%~dp0.."
set ROOT_DIR=%CD%
popd

set VENV_PATH=%ROOT_DIR%\%VENV_NAME%
set AI_HOME=%~dp0

:: --- Check if venv exists, else create ---
if not exist "%VENV_PATH%\Scripts\activate.bat" (
    echo [ACTION] Creating virtual environment at %VENV_PATH%...
    python -m venv "%VENV_PATH%"
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Exiting.
        pause
        exit /b
    )
)

:: --- Activate venv ---
call "%VENV_PATH%\Scripts\activate.bat"
if errorlevel 1 (
    echo [ERROR] Failed to activate venv. Exiting.
    pause
    exit /b
)

:: --- Install open-webui if missing ---
set WEBUI_PATH=%VENV_PATH%\Lib\site-packages\open_webui

if not exist "%WEBUI_PATH%\main.py" (
    echo [ACTION] Installing Open WebUI package...
    pip install open-webui
    if errorlevel 1 (
        echo [ERROR] Failed to install open-webui. Exiting.
        pause
        exit /b
    )
)

:: --- Install extra dependencies ---
set PACKAGES=onnxruntime wikipedia fastapi uvicorn

for %%P in (%PACKAGES%) do (
    echo [CHECK] Installing %%P...
    pip install --prefer-binary %%P >nul 2>&1
)

:: --- info.cfg setup ---
if not exist "%AI_HOME%\info.cfg" (
    (
        echo %AI_HOME%
        echo Amicia
        echo You
    ) > "%AI_HOME%\info.cfg"
)

:: --- Inject custom main.py ---
if not exist "%WEBUI_PATH%\main.py.bak" (
    echo [BACKUP] Backing up original main.py...
    copy /Y "%WEBUI_PATH%\main.py" "%WEBUI_PATH%\main.py.bak"
)

echo [COPY] Updating info.cfg...
copy /Y "%AI_HOME%\info.cfg" "%WEBUI_PATH%\info.cfg"
echo [COPY] Injecting custom main.py...
copy /Y "%AI_HOME%\main.py" "%WEBUI_PATH%\main.py"

:: --- Start WebUI ---
echo [START] Launching Open WebUI...
start /wait open-webui serve
::open-webui serve
::pause

:: --- Restore original main.py after exit ---
echo [RESTORE] Restoring original main.py...
copy /Y "%WEBUI_PATH%\main.py.bak" "%WEBUI_PATH%\main.py"

:: --- Final exit countdown ---
for /l %%i in (3,-1,1) do (
    echo Exiting in %%i seconds...
    timeout /t 1 >nul
)
exit
