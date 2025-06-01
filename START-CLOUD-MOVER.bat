@echo off
title Cloud Mover

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not installed
    echo.
    echo Please install Python from python.org
    pause
    exit /b 1
)

:: Check rclone
if not exist "rclone.exe" (
    echo ERROR: rclone.exe not found in current directory
    pause
    exit /b 1
)

:: Start Cloud Mover
echo Starting Cloud Mover...
python cloud_mover.py
echo.
echo Process completed. 
pause