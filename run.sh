#!/usr/bin/env bash
set -e

echo "Starting Wrisha AI v3.0..."

if [ ! -f ".env" ]; then
    echo ""
    echo "ERROR: .env file not found!"
    echo "Copy .env.example to .env and add your API keys:"
    echo "  cp .env.example .env"
    echo ""
    exit 1
fi

if [ -f ".venv/bin/python" ]; then
    .venv/bin/python main.py
else
    echo "Virtual environment not found. Using system Python..."
    python3 main.py
fi
