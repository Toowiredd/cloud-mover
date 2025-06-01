@echo off
echo Refreshing Google Drive token...
echo.
echo When prompted, press Enter to use the existing token and refresh it.
echo You'll need to authorize in your browser again.
echo.
rclone.exe config reconnect gdrive:
echo.
echo Token refresh complete!
pause