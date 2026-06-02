@echo off
echo Starting Wrisha AI v3.0...

if not exist ".env" if not exist "secrets\.env" (
    echo.
    echo  ERROR: No .env file found!
    echo  Copy .env.example to .env and add your API keys:
    echo    copy .env.example .env
    echo.
    pause
    exit /b 1
)

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    echo Virtual environment not found. Using system Python...
    python main.py
)
pause
