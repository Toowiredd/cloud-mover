@echo off
color 0C
echo ============================================
echo    MOVE TO CLOUD - FREE UP LAPTOP SPACE
echo ============================================
echo.
echo WARNING: This will DELETE files after upload!
echo.

:: Safety check
set /p CONFIRM="Type YES to continue: "
if not "%CONFIRM%"=="YES" exit /b

:: Start the move-to-cloud drop zone
pythonw drop-zone-move.pyw