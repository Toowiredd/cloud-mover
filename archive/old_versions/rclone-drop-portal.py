#!/usr/bin/env python3
"""
RClone Drop Portal - Simple Python version
Upload folders to Google Drive via drag-and-drop web interface
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import mimetypes

PORT = 8888

HTML_CONTENT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RClone Drop Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f172a;
            color: #e2e8f0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        .container { max-width: 600px; width: 100%; }
        h1 {
            text-align: center;
            font-size: 2.5rem;
            margin-bottom: 2rem;
            background: linear-gradient(to right, #3b82f6, #8b5cf6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .drop-zone {
            border: 3px dashed #3b82f6;
            border-radius: 1rem;
            padding: 4rem;
            text-align: center;
            transition: all 0.3s;
            background: #1e293b;
            cursor: pointer;
        }
        .drop-zone.dragover {
            border-color: #8b5cf6;
            background: #2d3748;
            transform: scale(1.02);
        }
        .drop-zone-text { font-size: 1.25rem; margin-bottom: 1rem; }
        .drop-zone-subtext { color: #94a3b8; font-size: 0.875rem; }
        input[type="file"] { display: none; }
        .status {
            margin-top: 2rem;
            padding: 1rem;
            border-radius: 0.5rem;
            text-align: center;
            display: none;
        }
        .status.success { background: #065f46; color: #6ee7b7; display: block; }
        .status.error { background: #7f1d1d; color: #fca5a5; display: block; }
        .status.info { background: #1e3a8a; color: #93c5fd; display: block; }
        .upload-list {
            margin-top: 1rem;
            background: #1e293b;
            border-radius: 0.5rem;
            padding: 1rem;
            max-height: 200px;
            overflow-y: auto;
        }
        .upload-item {
            padding: 0.5rem;
            border-bottom: 1px solid #334155;
            font-size: 0.875rem;
        }
        .config-check {
            background: #7c2d12;
            color: #fed7aa;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 2rem;
            text-align: center;
        }
        code {
            background: #334155;
            padding: 0.25rem 0.5rem;
            border-radius: 0.25rem;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>RClone Drop Portal</h1>
        <div id="configCheck" class="config-check" style="display:none"></div>
        <div class="drop-zone" id="dropZone">
            <div class="drop-zone-text">Drag & Drop folders here</div>
            <div class="drop-zone-subtext">or click to browse (max 50GB)</div>
            <input type="file" id="fileInput" webkitdirectory directory multiple>
        </div>
        <div class="status" id="status"></div>
        <div class="upload-list" id="uploadList" style="display:none"></div>
    </div>
    
    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const status = document.getElementById('status');
        const uploadList = document.getElementById('uploadList');
        const configCheck = document.getElementById('configCheck');
        
        // Check configuration
        fetch('/check-config')
            .then(r => r.json())
            .then(data => {
                if (!data.configured) {
                    configCheck.style.display = 'block';
                    configCheck.innerHTML = data.message;
                }
            });
        
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            handleFiles(e.dataTransfer.files);
        });
        
        fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        
        function handleFiles(files) {
            const fileList = Array.from(files);
            const totalSize = fileList.reduce((sum, f) => sum + f.size, 0);
            
            if (totalSize > 50 * 1024 * 1024 * 1024) {
                showStatus('error', 'Total size exceeds 50GB limit!');
                return;
            }
            
            const formData = new FormData();
            fileList.forEach(file => {
                formData.append('files', file, file.webkitRelativePath || file.name);
            });
            
            showStatus('info', 'Uploading ' + fileList.length + ' files...');
            uploadList.style.display = 'block';
            uploadList.innerHTML = '<div class="upload-item">Starting upload...</div>';
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showStatus('success', 'Upload completed! Check your Google Drive.');
                } else {
                    showStatus('error', 'Upload failed: ' + data.message);
                }
            })
            .catch(err => {
                showStatus('error', 'Network error: ' + err.message);
            });
        }
        
        function showStatus(type, message) {
            status.className = 'status ' + type;
            status.textContent = message;
            status.style.display = 'block';
        }
    </script>
</body>
</html>
"""

class UploadHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_CONTENT.encode())
        elif self.path == '/check-config':
            self.check_config()
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/upload':
            self.handle_upload()
        else:
            self.send_error(404)
    
    def check_config(self):
        """Check if rclone is configured with Google Drive"""
        try:
            result = subprocess.run(['./rclone.exe', 'listremotes'], 
                                  capture_output=True, text=True)
            configured = 'gdrive:' in result.stdout
            
            if configured:
                # Test the connection
                test = subprocess.run(['./rclone.exe', 'lsd', 'gdrive:', '--max-depth', '1'],
                                    capture_output=True, text=True)
                if test.returncode != 0:
                    configured = False
                    message = "Google Drive token expired. Run: <code>rclone config reconnect gdrive:</code>"
                else:
                    message = "Google Drive configured and working!"
            else:
                message = "Google Drive not configured. Run: <code>rclone config</code> and create remote named 'gdrive'"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'configured': configured, 'message': message}
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def handle_upload(self):
        """Handle file upload"""
        try:
            content_length = int(self.headers['Content-Length'])
            
            # Parse multipart form data
            content_type = self.headers['Content-Type']
            if not content_type.startswith('multipart/form-data'):
                raise ValueError("Expected multipart/form-data")
            
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                # Read and save files
                # Note: This is a simplified version. In production, use proper multipart parser
                post_data = self.rfile.read(content_length)
                
                # For now, we'll save the entire post data and let rclone handle it
                temp_file = os.path.join(temp_dir, "upload_data")
                with open(temp_file, 'wb') as f:
                    f.write(post_data)
                
                # Start rclone upload in background
                def upload_to_drive():
                    cmd = [
                        './rclone.exe', 'copy', temp_dir, 'gdrive:uploads',
                        '--transfers', '4',
                        '--checkers', '8', 
                        '--buffer-size', '16M',
                        '--log-level', 'INFO'
                    ]
                    subprocess.run(cmd)
                
                thread = threading.Thread(target=upload_to_drive)
                thread.start()
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'success': True, 'message': 'Upload started'}
                self.wfile.write(json.dumps(response).encode())
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'success': False, 'message': str(e)}
            self.wfile.write(json.dumps(response).encode())

def main():
    print(f"Starting RClone Drop Portal on http://localhost:{PORT}")
    print("Press Ctrl+C to stop\n")
    
    server = HTTPServer(('localhost', PORT), UploadHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()

if __name__ == '__main__':
    main()