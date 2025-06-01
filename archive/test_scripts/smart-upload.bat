@echo off
setlocal enabledelayedexpansion

echo ============================================
echo    Smart Upload with Ignore Patterns
echo ============================================
echo.

if "%~1"=="" goto :usage

set "SOURCE=%~1"
set "FOLDER_NAME=%~nx1"

:: Check for custom ignore file in source directory
set "LOCAL_IGNORE=%SOURCE%\.rcloneignore"
set "GLOBAL_IGNORE=.rcloneignore"

if exist "%LOCAL_IGNORE%" (
    echo Using local ignore file: %LOCAL_IGNORE%
    set "IGNORE_FILE=%LOCAL_IGNORE%"
) else if exist "%GLOBAL_IGNORE%" (
    echo Using global ignore file: %GLOBAL_IGNORE%
    set "IGNORE_FILE=%GLOBAL_IGNORE%"
) else (
    echo No ignore file found. Creating default .rcloneignore...
    call :create_default_ignore
    set "IGNORE_FILE=%GLOBAL_IGNORE%"
)

echo.
echo Excluded patterns:
echo ------------------
type "%IGNORE_FILE%" | findstr /v "^#" | findstr /v "^$"
echo.

:: Count files with exclusions
echo Counting files (excluding ignored patterns)...
rclone.exe size "%SOURCE%" --exclude-from "%IGNORE_FILE%" --json > temp_size.json 2>nul
for /f "tokens=2 delims=:," %%a in ('type temp_size.json ^| findstr "count"') do set FILE_COUNT=%%a
for /f "tokens=2 delims=:," %%a in ('type temp_size.json ^| findstr "bytes"') do set TOTAL_BYTES=%%a
del temp_size.json 2>nul

set /a FILE_COUNT=%FILE_COUNT: =%
set /a SIZE_MB=%TOTAL_BYTES: =% / 1048576

echo.
echo Files to upload: %FILE_COUNT%
echo Total size: %SIZE_MB% MB
echo.

set /p DEST="Destination folder in Google Drive [uploads/%FOLDER_NAME%]: "
if "%DEST%"=="" set "DEST=uploads/%FOLDER_NAME%"

echo.
echo Ready to upload to: gdrive:%DEST%
set /p CONFIRM="Continue? (Y/N): "
if /i not "%CONFIRM%"=="Y" exit /b 0

echo.
rclone.exe copy "%SOURCE%" "gdrive:%DEST%" ^
    --exclude-from "%IGNORE_FILE%" ^
    --transfers 16 ^
    --checkers 16 ^
    --buffer-size 32M ^
    --drive-chunk-size 256M ^
    --fast-list ^
    --progress ^
    --stats 5s

if %errorlevel% equ 0 (
    echo.
    echo [SUCCESS] Upload completed!
    echo Uploaded %FILE_COUNT% files to gdrive:%DEST%
) else (
    echo.
    echo [ERROR] Upload failed!
)
pause
exit /b

:usage
echo Usage: smart-upload.bat "C:\path\to\folder"
echo.
echo This will upload the folder while respecting .rcloneignore patterns.
echo.
echo To edit ignore patterns:
echo   - Edit .rcloneignore in this directory (global)
echo   - Create .rcloneignore in your source folder (local)
echo.
pause
exit /b

:create_default_ignore
(
echo # Default ignore patterns
echo # Edit this file to customize what gets uploaded
echo.
echo # Temporary files
echo *.tmp
echo *.temp
echo ~*
echo.
echo # System files  
echo Thumbs.db
echo .DS_Store
echo desktop.ini
echo.
echo # Development
echo node_modules/
echo .git/
echo __pycache__/
echo *.pyc
) > "%GLOBAL_IGNORE%"
exit /b