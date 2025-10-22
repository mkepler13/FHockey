@echo off
setlocal ENABLEDELAYEDEXPANSION

:: -------------------------------
:: Configuration
:: -------------------------------
set FANTRAX_SCRIPT=CoroBach
set DISCORD_SCRIPT=FHockey.py
set FANTRAX_API=http://localhost:8000
set MAX_WAIT_SECONDS=30

:: -------------------------------
:: Start Fantrax API Server (Python 3.13)
:: -------------------------------
echo ======================================
echo Starting Fantrax API Server (Python 3.13)...
echo ======================================
start "Fantrax API Server" cmd /k "uvicorn %FANTRAX_SCRIPT%:app --reload --port 8000 --host 127.0.0.1"

:: -------------------------------
:: Wait for Fantrax API to come online
:: -------------------------------
echo Waiting for Fantrax API to start (checking %FANTRAX_API%/status)...
set WAIT_SECONDS=0

:wait_loop
curl --silent --fail %FANTRAX_API%/status >nul 2>&1
if !errorlevel! EQU 0 (
    echo Fantrax API is online!
    goto :start_discord
)

set /a WAIT_SECONDS+=1
if !WAIT_SECONDS! GEQ %MAX_WAIT_SECONDS% (
    echo Fantrax API did not start within %MAX_WAIT_SECONDS% seconds.
    echo You can still start the Discord bot manually once the API is ready.
    goto :end
)
timeout /t 1 /nobreak >nul
goto :wait_loop

:start_discord
:: -------------------------------
:: Start Discord Bot (Python 3.8)
:: -------------------------------
echo ======================================
echo Starting Discord Bot (Python 3.8)...
echo ======================================
start "FHockey Discord Bot" cmd /k "python38 %DISCORD_SCRIPT%"

echo ======================================
echo All services launched!
echo Closing this window in 10 seconds
echo ======================================
timeout /t 10 /nobreak >nul

:end
exit
