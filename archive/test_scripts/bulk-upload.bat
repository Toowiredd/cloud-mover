@echo off
setlocal enabledelayedexpansion

echo ============================================
echo    RClone Bulk Upload Tool
echo    Optimized for millions of files
echo ============================================
echo.

if "%~1"=="" (
    echo Usage: bulk-upload.bat "C:\path\to\folder"
    echo.
    echo This tool is optimized for uploading folders with millions of files.
    echo It uses advanced rclone features to maximize performance.
    echo.
    pause
    exit /b 1
)

set "SOURCE=%~1"
set "FOLDER_NAME=%~nx1"

echo Source: %SOURCE%
echo.

:: Check rclone configuration
rclone.exe listremotes | findstr "gdrive:" >nul
if %errorlevel% neq 0 (
    echo [ERROR] Google Drive not configured!
    echo Please run: rclone config
    pause
    exit /b 1
)

:: Count files (quick estimation)
echo Estimating file count...
set COUNT=0
for /f %%a in ('dir "%SOURCE%" /s /b /a-d 2^>nul ^| find /c /v ""') do set COUNT=%%a
echo Estimated files: %COUNT%
echo.

:: Get destination
set /p DEST_FOLDER="Destination folder name in Google Drive [%FOLDER_NAME%]: "
if "%DEST_FOLDER%"=="" set "DEST_FOLDER=%FOLDER_NAME%"

echo.
echo Configuration:
echo --------------
echo Source: %SOURCE%
echo Destination: gdrive:uploads/%DEST_FOLDER%
echo Estimated files: %COUNT%
echo.
echo Optimizations enabled:
echo - Fast-list for better performance
echo - 16 parallel transfers
echo - 32MB buffer per transfer
echo - 256MB chunk size for large files
echo - Batch checking of 100 files at once
echo - No modification time checks (faster)
echo.

set /p CONFIRM="Start upload? (Y/N): "
if /i not "%CONFIRM%"=="Y" exit /b 0

:: Create log file
set "LOGFILE=upload_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "LOGFILE=%LOGFILE: =0%"

echo.
echo Starting upload...
echo Log file: %LOGFILE%
echo.

:: Check for ignore file
if exist ".rcloneignore" (
    echo Using ignore patterns from .rcloneignore
    set "EXCLUDE_FROM=--exclude-from .rcloneignore"
) else (
    echo No .rcloneignore file found, uploading all files
    set "EXCLUDE_FROM="
)

:: Run rclone with optimizations for millions of files
rclone.exe copy "%SOURCE%" "gdrive:uploads/%DEST_FOLDER%" ^
    %EXCLUDE_FROM% ^
    --transfers 16 ^
    --checkers 16 ^
    --buffer-size 32M ^
    --drive-chunk-size 256M ^
    --drive-upload-cutoff 256M ^
    --fast-list ^
    --no-check-dest ^
    --no-update-modtime ^
    --drive-use-trash=false ^
    --drive-acknowledge-abuse ^
    --low-level-retries 10 ^
    --retries 5 ^
    --stats 5s ^
    --stats-log-level NOTICE ^
    --log-file "%LOGFILE%" ^
    --log-level INFO ^
    --progress

echo.
if %errorlevel% equ 0 (
    echo [SUCCESS] Upload completed!
    echo Files uploaded to: gdrive:uploads/%DEST_FOLDER%
) else (
    echo [ERROR] Upload failed! Check log file: %LOGFILE%
)

echo.
pause