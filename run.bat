@echo off
title Discord Role Bot

echo ========================================
echo   Discord Role Bot - Local Runner
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.12+ from https://python.org
    pause
    exit /b 1
)

:: Install/update dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)
echo.

:: Check if .env exists
if not exist ".env" (
    echo [ERROR] .env file not found!
    echo Please create .env with your DISCORD_TOKEN
    pause
    exit /b 1
)

echo [2/3] Starting bot...
echo [3/3] Bot is running. Press Ctrl+C to stop.
echo.

:: Run the bot
python main.py

:: If bot crashes, pause so user can see the error
echo.
echo [INFO] Bot stopped. Press any key to exit.
pause