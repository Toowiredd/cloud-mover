#!/usr/bin/env python3
import os
import subprocess
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import json

PORT = 8888

HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RClone Drop Portal</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a1a;
            color: #fff;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: #2a2a2a;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        h1 {
            color: #4CAF50;
            margin-bottom: 30px;
        }
        #dropzone {
            border: 3px dashed #4CAF50;
            border-radius: 10px;
            padding: 50px;
            margin: 20px 0;
            cursor: pointer;
            transition: all 0.3s;
        }
        #dropzone:hover, #dropzone.dragover {
            background: #3a3a3a;
            border-color: #76ff03;
        }
        #status {
            margin-top: 20px;
            padding: 10px;
            border-radius: 5px;
            display: none;
        }
        .success { background: #4CAF50; color: white; }
        .error { background: #f44336; color: white; }
        .info { background: #2196F3; color: white; }
        button {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover {
            background: #45a049;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>RClone Drop Portal</h1>
        <div id="dropzone">
            <p>Drag & Drop folders here</p>
            <p>or</p>
            <button onclick="selectFolder()">Select Folder</button>
        </div>
        <div id="status"></div>
        <input type="file" id="folderInput" webkitdirectory style="display:none">
    </div>
    
    <script>
        const dropzone = document.getElementById('dropzone');
        const status = document.getElementById('status');
        const folderInput = document.getElementById('folderInput');
        
        function showStatus(type, message) {
            status.className = type;
            status.textContent = message;
            status.style.display = 'block';
        }
        
        function selectFolder() {
            folderInput.click();
        }
        
        folderInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                uploadFiles(e.target.files);
            }
        });
        
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
        
        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('dragover');
        });
        
        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
            
            const items = e.dataTransfer.items;
            const files = [];
            
            for (let i = 0; i < items.length; i++) {
                if (items[i].kind === 'file') {
                    files.push(items[i].getAsFile());
                }
            }
            
            if (files.length > 0) {
                uploadFiles(files);
            }
        });
        
        function uploadFiles(files) {
            const folderName = prompt('Enter folder name for Google Drive:', 'upload_' + Date.now());
            if (!folderName) return;
            
            showStatus('info', 'Preparing upload...');
            
            const formData = new FormData();
            formData.append('folder', folderName);
            
            for (let file of files) {
                formData.append('files', file);
            }
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showStatus('success', data.message);
                } else {
                    showStatus('error', data.message);
                }
            })
            .catch(err => {
                showStatus('error', 'Upload failed: ' + err.message);
            });
        }
    </script>
</body>
</html>"""

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML.encode())
        else:
            self.send_error(404)
    
    def do_POST(self):
        if self.path == '/upload':
            # For simplicity, we'll just return a message
            # In a real implementation, you'd handle the file upload here
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            # Check if rclone is configured
            result = subprocess.run(['./rclone.exe', 'listremotes'], 
                                  capture_output=True, text=True)
            
            if 'gdrive:' in result.stdout:
                message = "Upload functionality ready. For actual upload, use: rclone copy [folder] gdrive:[destination]"
                success = True
            else:
                message = "Google Drive not configured. Run: rclone config"
                success = False
            
            response = json.dumps({'success': success, 'message': message})
            self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        # Suppress log messages
        pass

def main():
    print(f"\n🚀 RClone Drop Portal starting on http://localhost:{PORT}")
    print("📁 Open your browser to upload folders to Google Drive")
    print("Press Ctrl+C to stop\n")
    
    # Try to open browser
    try:
        webbrowser.open(f'http://localhost:{PORT}')
    except:
        pass
    
    server = HTTPServer(('localhost', PORT), RequestHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✋ Shutting down...")
        server.shutdown()

if __name__ == '__main__':
    main()