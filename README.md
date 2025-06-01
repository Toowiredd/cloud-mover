# Cloud Mover

A Python desktop application for freeing up disk space by moving folders to Google Drive using rclone.

## Features

- 🚀 Modern GUI with drag-and-drop support
- 📊 Real-time upload progress tracking
- ✅ Automatic verification before deletion
- 🎯 Smart file filtering with .rcloneignore
- 💾 Batch upload with optimized settings

## Project Structure

```
cloud-mover/
├── cloud_mover.py          # Main entry point
├── START-CLOUD-MOVER.bat   # Windows launcher
├── rclone.exe              # RClone executable
├── src/                    # Source code
│   ├── core/              # Core functionality
│   │   ├── cloud_operations.py
│   │   └── file_operations.py
│   └── ui/                # User interface
│       └── main_window.py
├── config/                 # Configuration files
│   └── .rcloneignore      # File exclusion patterns
├── archive/               # Old versions and test scripts
│   ├── old_versions/
│   └── test_scripts/
└── docs/                  # Documentation

```

## Requirements

- Python 3.x
- rclone configured with Google Drive
- Windows OS

## Setup

1. **Download rclone.exe**:
   - Download from [rclone.org](https://rclone.org/downloads/)
   - Place `rclone.exe` in the project root directory

2. **Ensure Python is installed**

3. **Configure rclone with Google Drive**:
   ```
   rclone config
   ```

4. **Run the application**:
   ```
   START-CLOUD-MOVER.bat
   ```

## Usage

1. Launch Cloud Mover
2. Drag and drop a folder or click to browse
3. Review the analysis (file count, size)
4. Confirm the move operation
5. Wait for upload and verification
6. Files are automatically deleted after successful upload

## Configuration

Edit `config/.rcloneignore` to customize which files to exclude from uploads.

## Safety Features

- Files are only deleted after successful upload verification
- Progress tracking shows upload status in real-time
- Detailed activity log for troubleshooting
- Automatic error handling and recovery