@echo off
echo ============================================
echo    SAFE ARCHIVE TO CLOUD
echo    Upload THEN delete (with verification)
echo ============================================
echo.

if "%~1"=="" (
    echo Drop a folder on this file to archive it to cloud
    echo.
    echo This will:
    echo   1. Upload to Google Drive
    echo   2. Verify the upload
    echo   3. Delete from laptop ONLY if successful
    echo.
    pause
    exit /b
)

set "SOURCE=%~1"
set "FOLDER_NAME=%~nx1"
set "DEST=gdrive:archived/%FOLDER_NAME%"

echo Folder to archive: %SOURCE%
echo Destination: %DEST%
echo.

:: Count files
for /f %%a in ('dir "%SOURCE%" /s /b /a-d 2^>nul ^| find /c /v ""') do set LOCAL_COUNT=%%a
echo Local files: %LOCAL_COUNT%
echo.

set /p CONFIRM="Archive and remove from laptop? (YES/NO): "
if not "%CONFIRM%"=="YES" exit /b

:: Step 1: Upload
echo.
echo STEP 1: Uploading to cloud...
rclone.exe copy "%SOURCE%" "%DEST%" ^
    --transfers 16 ^
    --buffer-size 32M ^
    --drive-chunk-size 256M ^
    --progress

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Upload failed! Files NOT deleted.
    pause
    exit /b 1
)

:: Step 2: Verify
echo.
echo STEP 2: Verifying upload...
rclone.exe size "%DEST%" --json > cloud_check.json
for /f "tokens=2 delims=:," %%a in ('type cloud_check.json ^| findstr "count"') do set CLOUD_COUNT=%%a
del cloud_check.json

set /a CLOUD_COUNT=%CLOUD_COUNT: =%

echo Cloud files: %CLOUD_COUNT%
echo Local files: %LOCAL_COUNT%

if not "%CLOUD_COUNT%"=="%LOCAL_COUNT%" (
    echo.
    echo [ERROR] File counts don't match! Files NOT deleted.
    echo Please check manually.
    pause
    exit /b 1
)

:: Step 3: Delete local
echo.
echo STEP 3: All files verified in cloud. Delete local copy?
echo.
set /p FINAL="Type DELETE to remove from laptop: "
if not "%FINAL%"=="DELETE" (
    echo Cancelled - files kept on laptop
    pause
    exit /b
)

echo.
echo Removing local files...
rmdir /s /q "%SOURCE%"

echo.
echo [SUCCESS] Archived to cloud and removed from laptop!
echo Files are now at: %DEST%
echo.
pause