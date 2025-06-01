# RClone Drop Portal

A drag-and-drop web interface for uploading folders up to 50GB to Google Drive using rclone.

## Features

- 🎯 Drag-and-drop interface for folders
- 📁 Support for folders up to 50GB
- 🚀 Fast parallel uploads using rclone
- 📊 Progress tracking
- 🎨 Modern, responsive UI

## Prerequisites

1. **Rust**: Install from [rustup.rs](https://rustup.rs/)
2. **RClone**: Already included in parent directory
3. **Google Drive API**: Will be configured during setup

## Quick Start

### Windows:
```bash
# Run the setup script
setup.bat

# Build and run
cargo build --release
cargo run --release
```

### Linux/Mac:
```bash
# Configure rclone
../rclone config
# Create a remote named "gdrive" for Google Drive

# Build and run
cargo build --release
cargo run --release
```

## Usage

1. Open http://localhost:8080 in your browser
2. Drag and drop a folder onto the drop zone
3. Click "Upload to Google Drive"
4. Files will be uploaded to the root of your Google Drive

## Configuration

The application expects an rclone remote named `gdrive` to be configured. You can change this in `src/main.rs` if needed.

### Rclone Performance Settings:
- `--transfers 4`: Number of parallel file transfers
- `--checkers 8`: Number of parallel directory checkers  
- `--buffer-size 16M`: In-memory buffer per transfer

## Architecture

- **Frontend**: Vanilla JavaScript with drag-and-drop API
- **Backend**: Actix-web (Rust) server
- **Upload**: Delegates to rclone for actual transfers
- **Storage**: Temporary files cleared after upload

## Troubleshooting

1. **"Google Drive is not configured"**: Run `rclone config` and create a remote named "gdrive"
2. **Upload fails**: Check rclone logs and ensure you have permissions
3. **Large uploads timeout**: The upload runs in background, check Google Drive directly

## Development

```bash
# Run in development mode
cargo run

# Run with debug logs
RUST_LOG=debug cargo run
```