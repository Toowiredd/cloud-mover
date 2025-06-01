@echo off
setlocal enabledelayedexpansion

echo ============================================
echo    RClone Drag-and-Drop Uploader
echo    Drop folders here to upload to Google Drive
echo ============================================
echo.

:: Check if a folder was dropped
if "%~1"=="" (
    echo No folder provided!
    echo.
    echo Usage: Drag and drop a folder onto this file
    echo    OR: Run "drag-drop-upload.bat C:\path\to\folder"
    echo.
    pause
    exit /b 1
)

:: Get folder info
set "FOLDER=%~1"
set "FOLDERNAME=%~n1"

echo Source folder: %FOLDER%
echo.

:: Check folder size
echo Checking folder size...
for /f "tokens=3" %%a in ('dir "%FOLDER%" /s /-c 2^>nul ^| findstr "File(s)"') do set SIZE=%%a
echo Folder contains: %SIZE% bytes
echo.

:: Check rclone config
rclone.exe listremotes | findstr "gdrive:" >nul
if %errorlevel% neq 0 (
    echo [ERROR] Google Drive not configured!
    echo Please run: rclone config
    echo.
    pause
    exit /b 1
)

:: Ask for destination
echo Where to upload in Google Drive?
echo 1. Root folder
echo 2. uploads/ folder
echo 3. Custom path
echo.
set /p CHOICE="Enter choice (1-3): "

if "%CHOICE%"=="1" set "DEST=gdrive:%FOLDERNAME%"
if "%CHOICE%"=="2" set "DEST=gdrive:uploads/%FOLDERNAME%"
if "%CHOICE%"=="3" (
    set /p CUSTOM="Enter path (e.g., MyFiles/Projects): "
    set "DEST=gdrive:!CUSTOM!/%FOLDERNAME%"
)

echo.
echo Will upload to: %DEST%
echo.
set /p CONFIRM="Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" exit /b 0

:: Perform upload
echo.
echo Starting upload...
echo =====================================
rclone.exe copy "%FOLDER%" "%DEST%" ^
    --progress ^
    --transfers 4 ^
    --checkers 8 ^
    --buffer-size 16M ^
    --drive-chunk-size 128M ^
    --log-level INFO

echo.
echo =====================================
if %errorlevel% equ 0 (
    echo [SUCCESS] Upload completed!
    echo Files uploaded to: %DEST%
) else (
    echo [ERROR] Upload failed!
)
echo.
pause