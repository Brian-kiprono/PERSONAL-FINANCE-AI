#!/bin/bash

echo "========================================"
echo "  Personal Finance Manager - Loading..."
echo "========================================"
echo ""

# Navigate to project directory
cd "/c/Users/SOOQ ELASER/OneDrive/Desktop/personal-finance-ai"

# Activate virtual environment
source venv/Scripts/activate

# Install optimizations
echo "Installing latest optimizations..."
pip install flask-caching -q

# Delete old database
echo "Cleaning up..."
rm -f finance.db

# Start server
echo ""
echo "========================================"
echo "  Server running at: http://127.0.0.1:5000"
echo "  Press Ctrl+C to stop"
echo "========================================"
echo ""

# Open browser (Git Bash compatible)
explorer "http://127.0.0.1:5000" 2>/dev/null &
start "http://127.0.0.1:5000" 2>/dev/null &
cmd //c start "http://127.0.0.1:5000" 2>/dev/null &

# Run the app
python app.py