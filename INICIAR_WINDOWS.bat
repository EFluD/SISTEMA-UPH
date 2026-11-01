@echo off
cd /d "%~dp0"
if not exist venv\Scripts\python.exe (
 echo Primero ejecute INSTALAR_WINDOWS.bat
 pause
 exit /b 1
)
echo Abra http://127.0.0.1:8000 en su navegador. Ctrl+C para detener.
venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
