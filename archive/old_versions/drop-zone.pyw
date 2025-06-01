#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, ttk
import os
import subprocess
import threading

class SimpleDropZone:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drop Zone")
        self.root.geometry("500x300")
        self.root.configure(bg='#1e1e1e')
        
        # Drop zone (click to browse)
        self.drop_zone = tk.Button(
            self.root,
            text="CLICK TO SELECT FOLDER\n\nOR\n\nDRAG & DROP",
            font=('Arial', 18, 'bold'),
            fg='white',
            bg='#3a3a3a',
            relief=tk.RAISED,
            bd=3,
            command=self.browse_folder
        )
        self.drop_zone.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Status
        self.status = tk.Label(
            self.root,
            text="Ready",
            font=('Arial', 12),
            fg='#00ff00',
            bg='#1e1e1e'
        )
        self.status.pack(pady=(0, 10))
        
        # Progress
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        
        self.root.mainloop()
    
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.upload(folder)
    
    def upload(self, folder):
        self.status.config(text=f"Uploading: {os.path.basename(folder)}", fg='yellow')
        self.progress.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.progress.start()
        self.drop_zone.config(state='disabled')
        
        # Background upload
        thread = threading.Thread(target=self._upload_thread, args=(folder,))
        thread.daemon = True
        thread.start()
    
    def _upload_thread(self, folder):
        folder_name = os.path.basename(folder)
        
        # Check for ignore file
        cmd = ['rclone.exe', 'copy', folder, f'gdrive:uploads/{folder_name}']
        if os.path.exists('.rcloneignore'):
            cmd.extend(['--exclude-from', '.rcloneignore'])
        cmd.extend([
            '--transfers', '16',
            '--buffer-size', '32M',
            '--drive-chunk-size', '256M',
            '--fast-list'
        ])
        
        try:
            result = subprocess.run(cmd, capture_output=True)
            success = result.returncode == 0
            self.root.after(0, self._done, success)
        except Exception as e:
            self.root.after(0, self._done, False)
    
    def _done(self, success):
        self.progress.stop()
        self.progress.pack_forget()
        self.drop_zone.config(state='normal')
        
        if success:
            self.status.config(text="✓ Upload complete!", fg='#00ff00')
        else:
            self.status.config(text="✗ Upload failed", fg='red')

if __name__ == '__main__':
    SimpleDropZone()