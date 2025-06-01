#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from tkinterdnd2 import TkinterDnD, DND_FILES
import os
import subprocess
import threading
import json

class DropPortal:
    def __init__(self):
        self.window = TkinterDnD.Tk()
        self.window.title("RClone Drop Portal")
        self.window.geometry("600x400")
        self.window.configure(bg='#1a1a1a')
        
        # Main drop zone
        self.drop_frame = tk.Frame(self.window, bg='#2a2a2a', relief=tk.RAISED, bd=2)
        self.drop_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.drop_label = tk.Label(
            self.drop_frame,
            text="DRAG FOLDER HERE",
            font=('Arial', 24, 'bold'),
            fg='#4CAF50',
            bg='#2a2a2a'
        )
        self.drop_label.pack(expand=True)
        
        # Status label
        self.status_label = tk.Label(
            self.window,
            text="Ready - Drop a folder to upload",
            font=('Arial', 12),
            fg='white',
            bg='#1a1a1a'
        )
        self.status_label.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.window, mode='indeterminate')
        self.progress.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        # Enable drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.drop_handler)
        
        # Check rclone config
        self.check_config()
        
    def check_config(self):
        try:
            result = subprocess.run(['rclone.exe', 'listremotes'], 
                                  capture_output=True, text=True)
            if 'gdrive:' not in result.stdout:
                self.status_label.config(
                    text="ERROR: Google Drive not configured. Run: rclone config",
                    fg='red'
                )
        except:
            self.status_label.config(
                text="ERROR: rclone.exe not found",
                fg='red'
            )
    
    def drop_handler(self, event):
        files = self.window.tk.splitlist(event.data)
        if files:
            folder = files[0]
            if os.path.isdir(folder):
                self.upload_folder(folder)
            else:
                self.status_label.config(text="Please drop a FOLDER, not a file", fg='yellow')
    
    def upload_folder(self, folder_path):
        self.status_label.config(text=f"Uploading: {os.path.basename(folder_path)}", fg='white')
        self.progress.start()
        
        # Run upload in background thread
        thread = threading.Thread(target=self._do_upload, args=(folder_path,))
        thread.daemon = True
        thread.start()
    
    def _do_upload(self, folder_path):
        folder_name = os.path.basename(folder_path)
        dest = f"gdrive:uploads/{folder_name}"
        
        # Check for ignore file
        ignore_file = ".rcloneignore"
        exclude_args = []
        if os.path.exists(ignore_file):
            exclude_args = ["--exclude-from", ignore_file]
        
        try:
            result = subprocess.run([
                'rclone.exe', 'copy', folder_path, dest,
                *exclude_args,
                '--transfers', '16',
                '--checkers', '16',
                '--buffer-size', '32M',
                '--drive-chunk-size', '256M',
                '--fast-list',
                '--progress'
            ], capture_output=True, text=True)
            
            self.window.after(0, self._upload_complete, result.returncode == 0)
        except Exception as e:
            self.window.after(0, self._upload_complete, False, str(e))
    
    def _upload_complete(self, success, error_msg=""):
        self.progress.stop()
        if success:
            self.status_label.config(text="Upload complete! Drop another folder", fg='#4CAF50')
        else:
            self.status_label.config(text=f"Upload failed: {error_msg}", fg='red')
    
    def run(self):
        self.window.mainloop()

if __name__ == '__main__':
    # Try to import tkinterdnd2, install if needed
    try:
        import tkinterdnd2
    except ImportError:
        print("Installing required package...")
        subprocess.run([sys.executable, "-m", "pip", "install", "tkinterdnd2"])
        import tkinterdnd2
    
    app = DropPortal()
    app.run()