@echo off
echo ====================================================
echo Starting IntelliSupply Flask Backend (Port 5000)...
echo ====================================================
cd /d "%~dp0"
python backend/app.py
pause
