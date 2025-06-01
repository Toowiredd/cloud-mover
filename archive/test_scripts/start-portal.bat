@echo off
echo RClone Drop Portal Launcher
echo ==========================
echo.

:: Check if rclone is configured
rclone.exe listremotes | findstr "gdrive:" >nul
if %errorlevel% neq 0 (
    echo [!] Google Drive not configured in rclone
    echo.
    echo Please run: rclone config
    echo And create a remote named "gdrive"
    echo.
    pause
    exit /b 1
)

:: Check if token is valid
echo Checking Google Drive connection...
rclone.exe lsd gdrive: --max-depth 1 >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Google Drive token expired or invalid
    echo.
    echo Refreshing token...
    rclone.exe config reconnect gdrive:
    echo.
)

:: Find available port
set PORT=8888
netstat -an | findstr :%PORT% >nul
if %errorlevel% equ 0 (
    echo Port %PORT% is in use, trying 8889...
    set PORT=8889
)

:: Create a simple uploader script
echo Creating uploader script...
(
echo @echo off
echo if "%%1"=="" (
echo     echo Usage: upload.bat [folder_path]
echo     exit /b 1
echo ^)
echo echo Uploading %%1 to Google Drive...
echo rclone.exe copy "%%1" "gdrive:uploads/%%~n1" --progress --transfers 4
echo echo Upload complete!
echo pause
) > upload.bat

:: Start the portal
echo.
echo Starting portal on http://localhost:%PORT%
echo.
echo Quick upload: Drag any folder onto upload.bat
echo Web portal: Opening in browser...
echo.
start http://localhost:%PORT%
python simple-drop-portal.py