@echo off
if "%1"=="" (
    echo Usage: upload.bat [folder_path]
    exit /b 1
)
echo Uploading %1 to Google Drive...
rclone.exe copy "%1" "gdrive:uploads/%~n1" --progress --transfers 4
echo Upload complete!
pause
