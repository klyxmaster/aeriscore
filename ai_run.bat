@echo off
setlocal enabledelayedexpansion

:: === AERISCORE LAUNCHER (BBS-STYLE INFO.CFG) ===

set "INFO_FILE=info.cfg"
if not exist "%INFO_FILE%" (
    echo [ERROR] info.cfg not found. Aborting.
    pause
    exit /b
)

:: --- Read lines properly ---
set "count=0"
for /f "usebackq tokens=* delims=" %%a in ("%INFO_FILE%") do (
    if not "%%a"=="" if /i not "%%a:~0,1%%"=="#" (
        set /a count+=1
        if "!count!"=="1" set "AI_HOME=%%a"
        if "!count!"=="2" set "WEBUI_PATH=%%a"
        if "!count!"=="3" set "COMPANION=%%a"
        if "!count!"=="4" set "USER=%%a"
    )
)

:: --- Confirm values ---
echo [OK] AerisCore Path: %AI_HOME%
echo [OK] WebUI Path: %WEBUI_PATH%
echo [OK] Companion: %COMPANION%
echo [OK] User: %USER%
echo.



:: --- Verify main.py exists ---
if not exist "%WEBUI_PATH%\main.py" (
    echo [ERROR] WebUI main.py not found at: %WEBUI_PATH%
    pause
    exit /b
)

:: --- Backup and Inject Custom Files ---
echo [COPY] Updating info.cfg and main.py...
echo [BACKUP] Saving original main.py...
copy /Y "%WEBUI_PATH%\main.py" "%WEBUI_PATH%\main.py.bak" >nul

echo [INFO] Updating info.cfg
copy /Y info.cfg "%WEBUI_PATH%\info.cfg" > nul
echo [INFO] Injecting Aeris-Core
copy /Y main.py "%WEBUI_PATH%\main.py" > nul
echo.
:: --- Launch WebUI ---
echo [START] Launching Aeris-Core powered by Open-WebUI...
start /wait open-webui serve

:: --- Restore original main.py ---
echo [RESTORE] Restoring original main.py...
copy /Y "%WEBUI_PATH%\main.py.bak" "%WEBUI_PATH%\main.py" >nul

echo [DONE] Main.py restored.

:: --- Exit nicely ---
for /l %%i in (5,-1,1) do (
    echo Exiting in %%i seconds...
    timeout /t 1 >nul
)
exit
