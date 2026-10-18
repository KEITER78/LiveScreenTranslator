@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Project Python environment was not found. See README.md for setup.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" -u main.py
if errorlevel 1 (
    echo.
    echo LiveScreenTranslator could not start. See the error above.
    pause
    exit /b 1
)
