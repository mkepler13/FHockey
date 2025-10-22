@echo off
echo ======================================
echo Starting Fantrax API Server (Python 3.13)
echo ======================================
start "Fantrax API Server" cmd /k "python CoroBach.py"
echo ======================================
echo Starting Discord Bot (Python 3.8)
echo ======================================
start "FHockey Discord Bot" cmd /k "python38 FHockey.py"
echo ======================================
echo All services launched!
echo Closing this window in 10 seconds
echo ======================================
timeout /t 10 /nobreak >nul
exit