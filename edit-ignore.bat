@echo off
echo Opening .rcloneignore for editing...
echo.
echo Common patterns to add:
echo   *.log           - Ignore all log files
echo   /temp/          - Ignore temp directory
echo   **.cache/**     - Ignore all cache folders
echo   !important.log  - Don't ignore this specific file
echo.

if exist "config\.rcloneignore" (
    notepad config\.rcloneignore
) else (
    echo Creating new .rcloneignore file...
    if not exist "config" mkdir config
    copy nul config\.rcloneignore >nul
    notepad config\.rcloneignore
)