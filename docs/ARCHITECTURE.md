# Cloud Mover Architecture

## Overview

Cloud Mover is a desktop application built with Python and Tkinter that helps users free up disk space by moving folders to Google Drive using rclone.

## Core Components

### 1. Entry Point (`cloud_mover.py`)
- Main application launcher
- Handles Python path setup
- Error handling for startup issues

### 2. Core Modules (`src/core/`)

#### `cloud_operations.py`
- RClone integration and command execution
- Upload progress monitoring and parsing
- Cloud storage verification
- Configuration checking

#### `file_operations.py`
- Local file management
- Safe deletion with progress tracking
- File size calculations and formatting

### 3. User Interface (`src/ui/`)

#### `main_window.py`
- Complete GUI implementation using Tkinter
- Drag-and-drop support
- Real-time progress tracking
- Activity logging
- Settings management

## Data Flow

1. **Folder Selection**: User drags folder or clicks to browse
2. **Analysis**: Background thread analyzes folder (size, file count)
3. **Confirmation**: User confirms the move operation
4. **Upload**: Files uploaded to Google Drive with progress tracking
5. **Verification**: Upload integrity checked using rclone
6. **Cleanup**: Local files safely deleted after verification

## Configuration

- **Ignore Patterns**: `config/.rcloneignore` - Controls which files to skip
- **RClone Config**: Uses system rclone configuration for Google Drive

## Safety Features

- Files only deleted after successful upload verification
- Detailed progress tracking and logging
- Error handling with user feedback
- Configurable ignore patterns to skip unwanted files

## Dependencies

- Python 3.x
- Tkinter (usually included with Python)
- rclone.exe (included in project)
- Optional: tkinterdnd2 for enhanced drag-and-drop

## Performance Optimizations

- Multi-threaded operations (UI remains responsive)
- Optimized rclone transfer settings
- Background file analysis
- Progress reporting without blocking UI