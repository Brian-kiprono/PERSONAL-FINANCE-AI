@echo off
title Personal Finance Manager - Ultra Fast
color 0A
echo ========================================
echo   Personal Finance Manager - Loading...
echo ========================================
echo.
cd /d "C:\Users\SOOQ ELASER\OneDrive\Desktop\personal-finance-ai"
call venv\Scripts\activate
echo Installing latest optimizations...
pip install flask-caching -q
echo.
echo Deleting old cache...
if exist finance.db del finance.db
echo.
echo Starting server...
echo.
echo ========================================
echo   Server running at: http://127.0.0.1:5000
echo   Press Ctrl+C to stop
echo ========================================
echo.
start http://127.0.0.1:5000
python app.py
pause