@echo off
cd /d "%~dp0"
pip install -r requirements.txt
echo.
echo Abre http://localhost:3000 en el navegador
python server.py
pause
