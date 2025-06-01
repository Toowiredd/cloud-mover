@echo off
echo Starting Drop Zone...

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed
    echo Please install Python from python.org
    pause
    exit /b 1
)

:: Check rclone
if not exist "rclone.exe" (
    echo ERROR: rclone.exe not found
    pause
    exit /b 1
)

:: Check Google Drive config
rclone.exe listremotes | findstr "gdrive:" >nul
if %errorlevel% neq 0 (
    echo ERROR: Google Drive not configured
    echo Run: rclone config
    pause
    exit /b 1
)

:: Start the drop zone
start pythonw drop-zone.pyw

echo Drop Zone started!
echo.
echo A window should appear where you can:
echo   - Click to select a folder
echo   - It will upload to Google Drive
echo.
echo The .rcloneignore file controls what gets uploaded
echo.
timeout /t 3 >nul