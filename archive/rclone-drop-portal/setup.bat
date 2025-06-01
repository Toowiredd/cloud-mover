@echo off
echo RClone Drop Portal Setup
echo =======================
echo.
echo Step 1: Checking for rclone configuration...
..\rclone.exe listremotes | findstr "gdrive:" >nul
if %errorlevel% equ 0 (
    echo [OK] Google Drive remote "gdrive" is already configured!
) else (
    echo [!] Google Drive remote not found. Setting up now...
    echo.
    echo Please follow the prompts to configure Google Drive:
    echo - Choose "n" for new remote
    echo - Name it "gdrive" (important!)
    echo - Choose "drive" for Google Drive
    echo - Follow the authorization steps
    echo.
    ..\rclone.exe config
)

echo.
echo Step 2: Installing Rust (if not installed)...
echo Please install Rust from https://rustup.rs/ if you haven't already
echo.
echo Step 3: Building the application...
echo Run: cargo build --release
echo.
echo Step 4: Running the application...
echo Run: cargo run --release
echo.
echo The portal will be available at http://localhost:8080
pause