@echo off
echo Starting Emotional AI Companion...
REM Check if venv exists and run with that python, otherwise try system python
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    echo Virtual environment not found. Attempting to run with system Python...
    python main.py
)
pause
