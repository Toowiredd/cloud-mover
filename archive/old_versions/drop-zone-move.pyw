#!/usr/bin/env python3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import subprocess
import threading
import shutil

class MoveToCloudZone:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Move to Cloud - Free Up Space")
        self.root.geometry("500x350")
        self.root.configure(bg='#1e1e1e')
        
        # Title
        title = tk.Label(
            self.root,
            text="MOVE TO CLOUD",
            font=('Arial', 20, 'bold'),
            fg='#ff4444',
            bg='#1e1e1e'
        )
        title.pack(pady=10)
        
        # Drop zone
        self.drop_zone = tk.Button(
            self.root,
            text="CLICK TO SELECT FOLDER\n\nThis will MOVE files to cloud\nand DELETE from your laptop",
            font=('Arial', 14, 'bold'),
            fg='white',
            bg='#cc0000',
            relief=tk.RAISED,
            bd=3,
            command=self.browse_folder
        )
        self.drop_zone.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Safety checkbox
        self.confirm_var = tk.BooleanVar()
        self.confirm_check = tk.Checkbutton(
            self.root,
            text="I understand files will be DELETED after upload",
            variable=self.confirm_var,
            font=('Arial', 10),
            fg='white',
            bg='#1e1e1e',
            selectcolor='#1e1e1e'
        )
        self.confirm_check.pack(pady=5)
        
        # Status
        self.status = tk.Label(
            self.root,
            text="Ready to move files",
            font=('Arial', 12),
            fg='#00ff00',
            bg='#1e1e1e'
        )
        self.status.pack(pady=10)
        
        # Progress
        self.progress = ttk.Progressbar(self.root, mode='indeterminate')
        
        self.root.mainloop()
    
    def browse_folder(self):
        if not self.confirm_var.get():
            messagebox.warning("Confirm", "Please check the confirmation box first")
            return
            
        folder = filedialog.askdirectory()
        if folder:
            # Double confirm
            size = self.get_folder_size(folder)
            if messagebox.askyesno("Confirm Move", 
                f"This will:\n\n1. Upload {os.path.basename(folder)} ({size} MB) to Google Drive\n"
                f"2. DELETE it from your laptop\n\nAre you sure?"):
                self.move_to_cloud(folder)
    
    def get_folder_size(self, folder):
        total = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
        return total // (1024 * 1024)  # MB
    
    def move_to_cloud(self, folder):
        self.status.config(text=f"Moving: {os.path.basename(folder)}", fg='yellow')
        self.progress.pack(fill=tk.X, padx=20, pady=(0, 10))
        self.progress.start()
        self.drop_zone.config(state='disabled')
        
        thread = threading.Thread(target=self._move_thread, args=(folder,))
        thread.daemon = True
        thread.start()
    
    def _move_thread(self, folder):
        folder_name = os.path.basename(folder)
        
        # MOVE command (not copy)
        cmd = ['rclone.exe', 'move', folder, f'gdrive:uploads/{folder_name}']
        if os.path.exists('.rcloneignore'):
            cmd.extend(['--exclude-from', '.rcloneignore'])
        cmd.extend([
            '--transfers', '16',
            '--buffer-size', '32M',
            '--drive-chunk-size', '256M',
            '--fast-list',
            '--delete-empty-src-dirs'  # Remove empty folders after move
        ])
        
        try:
            result = subprocess.run(cmd, capture_output=True)
            success = result.returncode == 0
            self.root.after(0, self._done, success, folder)
        except Exception as e:
            self.root.after(0, self._done, False, folder)
    
    def _done(self, success, folder):
        self.progress.stop()
        self.progress.pack_forget()
        self.drop_zone.config(state='normal')
        
        if success:
            self.status.config(text=f"✓ Moved to cloud & deleted locally!", fg='#00ff00')
            # The folder should be gone now
        else:
            self.status.config(text="✗ Move failed - files NOT deleted", fg='red')

if __name__ == '__main__':
    MoveToCloudZone()