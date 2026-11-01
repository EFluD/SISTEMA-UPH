@echo off
cd /d "%~dp0"
python -m venv venv
if errorlevel 1 goto error
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto error
venv\Scripts\python.exe configurar.py
if errorlevel 1 goto error
echo Listo. Ejecute INICIAR_WINDOWS.bat
pause
exit /b 0
:error
echo No se completo la instalacion. Revise el mensaje anterior.
pause
exit /b 1
