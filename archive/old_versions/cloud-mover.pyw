#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, filedialog, font, messagebox
import os
import subprocess
import threading
import json
import time
from datetime import datetime
from pathlib import Path

class CloudMover:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cloud Mover - Free Up Space")
        self.root.geometry("800x650")
        self.root.configure(bg='#0a0a0a')
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (650 // 2)
        self.root.geometry(f'+{x}+{y}')
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("success.Horizontal.TProgressbar", 
                       troughcolor='#1a1a1a', 
                       background='#4CAF50',
                       lightcolor='#4CAF50',
                       darkcolor='#4CAF50',
                       bordercolor='#1a1a1a')
        
        # Variables
        self.current_folder = None
        self.is_moving = False
        
        # Header with gradient effect
        self.create_header()
        
        # Main content
        main_container = tk.Frame(self.root, bg='#0a0a0a')
        main_container.pack(fill='both', expand=True, padx=30)
        
        # Drop zone
        self.create_drop_zone(main_container)
        
        # Stats cards
        self.create_stats_cards(main_container)
        
        # Progress section
        self.create_progress_section(main_container)
        
        # Log area
        self.create_log_area(main_container)
        
        # Footer
        self.create_footer()
        
        # Check configuration
        self.check_config()
        
        # Bind drag and drop
        self.setup_drag_drop()
        
        self.root.mainloop()
    
    def create_header(self):
        header_frame = tk.Frame(self.root, bg='#0a0a0a', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        # Logo and title
        title_container = tk.Frame(header_frame, bg='#0a0a0a')
        title_container.pack(expand=True)
        
        # Cloud icon
        cloud_icon = tk.Label(
            title_container,
            text="☁",
            font=('Arial', 36),
            fg='#3498db',
            bg='#0a0a0a'
        )
        cloud_icon.pack(side='left', padx=(0, 10))
        
        # Title with gradient look
        title_font = font.Font(family="Arial", size=32, weight="bold")
        title = tk.Label(
            title_container,
            text="Cloud Mover",
            font=title_font,
            fg='#ffffff',
            bg='#0a0a0a'
        )
        title.pack(side='left')
        
        # Subtitle
        subtitle = tk.Label(
            title_container,
            text="Free up space instantly",
            font=('Arial', 13),
            fg='#7f8c8d',
            bg='#0a0a0a'
        )
        subtitle.pack(side='left', padx=(15, 0))
        
    
    def setup_drag_drop(self):
        # Enable file drop on the entire window
        try:
            from tkinterdnd2 import TkinterDnD, DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
        except:
            pass  # Drag and drop not available
    
    def handle_drop(self, event):
        if self.is_moving:
            return
        files = self.root.tk.splitlist(event.data)
        if files and os.path.isdir(files[0]):
            self.process_folder(files[0])
    
    def create_drop_zone(self, parent):
        # Drop zone container with rounded corners
        drop_container = tk.Frame(parent, bg='#0a0a0a')
        drop_container.pack(fill='x', pady=(0, 20))
        
        # Main drop frame
        drop_frame = tk.Frame(drop_container, bg='#1a1a1a', relief='flat', bd=0, height=180)
        drop_frame.pack(fill='x')
        drop_frame.pack_propagate(False)
        
        # Inner content
        inner_frame = tk.Frame(drop_frame, bg='#1a1a1a')
        inner_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Folder icon
        folder_icon = tk.Label(
            inner_frame,
            text="📁",
            font=('Arial', 48),
            fg='#3498db',
            bg='#1a1a1a'
        )
        folder_icon.pack()
        
        # Main text
        self.drop_text = tk.Label(
            inner_frame,
            text="Drop folder here or click to browse",
            font=('Arial', 16, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        self.drop_text.pack(pady=(10, 5))
        
        # Sub text
        self.drop_subtext = tk.Label(
            inner_frame,
            text="Supports folders up to 50GB",
            font=('Arial', 11),
            fg='#7f8c8d',
            bg='#1a1a1a'
        )
        self.drop_subtext.pack()
        
        # Make entire frame clickable
        for widget in [drop_frame, inner_frame, folder_icon, self.drop_text, self.drop_subtext]:
            widget.bind('<Button-1>', lambda e: self.select_folder() if not self.is_moving else None)
            widget.bind('<Enter>', lambda e: self.on_hover_enter() if not self.is_moving else None)
            widget.bind('<Leave>', lambda e: self.on_hover_leave() if not self.is_moving else None)
            widget.config(cursor='hand2' if not self.is_moving else 'arrow')
        
        self.drop_frame = drop_frame
        self.inner_frame = inner_frame
    
    def on_hover_enter(self):
        if not self.is_moving:
            self.drop_frame.config(bg='#2a2a2a')
            self.inner_frame.config(bg='#2a2a2a')
            for widget in self.inner_frame.winfo_children():
                widget.config(bg='#2a2a2a')
    
    def on_hover_leave(self):
        if not self.is_moving:
            self.drop_frame.config(bg='#1a1a1a')
            self.inner_frame.config(bg='#1a1a1a')
            for widget in self.inner_frame.winfo_children():
                widget.config(bg='#1a1a1a')
    
    def create_stats_cards(self, parent):
        # Stats container
        stats_frame = tk.Frame(parent, bg='#0a0a0a')
        stats_frame.pack(fill='x', pady=(0, 20))
        
        # Create 3 stat cards
        cards_data = [
            {"id": "folder", "label": "Selected Folder", "value": "None", "icon": "📂"},
            {"id": "files", "label": "Total Files", "value": "0", "icon": "📄"},
            {"id": "size", "label": "Total Size", "value": "0 MB", "icon": "💾"}
        ]
        
        self.stat_cards = {}
        
        for i, card_data in enumerate(cards_data):
            # Card frame
            card = tk.Frame(stats_frame, bg='#1a1a1a', relief='flat', bd=0)
            card.pack(side='left', fill='both', expand=True, padx=(0 if i == 0 else 5, 0))
            
            # Card content
            card_inner = tk.Frame(card, bg='#1a1a1a')
            card_inner.pack(expand=True, pady=15)
            
            # Icon and label
            icon_label = tk.Label(
                card_inner,
                text=f"{card_data['icon']} {card_data['label']}",
                font=('Arial', 10),
                fg='#7f8c8d',
                bg='#1a1a1a'
            )
            icon_label.pack()
            
            # Value
            value_label = tk.Label(
                card_inner,
                text=card_data['value'],
                font=('Arial', 14, 'bold'),
                fg='#ffffff',
                bg='#1a1a1a'
            )
            value_label.pack(pady=(5, 0))
            
            self.stat_cards[card_data['id']] = value_label
    
    def create_progress_section(self, parent):
        progress_container = tk.Frame(parent, bg='#0a0a0a')
        progress_container.pack(fill='x', pady=(0, 15))
        
        # Progress header
        progress_header = tk.Frame(progress_container, bg='#0a0a0a')
        progress_header.pack(fill='x', pady=(0, 10))
        
        # Status with icon
        self.status_icon = tk.Label(
            progress_header,
            text="✓",
            font=('Arial', 14),
            fg='#4CAF50',
            bg='#0a0a0a'
        )
        self.status_icon.pack(side='left', padx=(0, 8))
        
        self.status_label = tk.Label(
            progress_header,
            text="Ready to move files",
            font=('Arial', 12, 'bold'),
            fg='#ffffff',
            bg='#0a0a0a'
        )
        self.status_label.pack(side='left')
        
        # Speed indicator
        self.speed_label = tk.Label(
            progress_header,
            text="",
            font=('Arial', 10),
            fg='#7f8c8d',
            bg='#0a0a0a'
        )
        self.speed_label.pack(side='right')
        
        # Progress bar container
        progress_bg = tk.Frame(progress_container, bg='#1a1a1a', height=8)
        progress_bg.pack(fill='x', pady=(0, 5))
        
        # Custom progress bar
        self.progress_bar = tk.Frame(progress_bg, bg='#3498db', height=8)
        self.progress_bar.place(x=0, y=0, relheight=1, relwidth=0)
        
        # Progress details
        details_frame = tk.Frame(progress_container, bg='#0a0a0a')
        details_frame.pack(fill='x')
        
        self.progress_percent = tk.Label(
            details_frame,
            text="0%",
            font=('Arial', 10, 'bold'),
            fg='#3498db',
            bg='#0a0a0a'
        )
        self.progress_percent.pack(side='left')
        
        self.progress_detail = tk.Label(
            details_frame,
            text="",
            font=('Arial', 10),
            fg='#7f8c8d',
            bg='#0a0a0a'
        )
        self.progress_detail.pack(side='left', padx=(10, 0))
        
        # ETA
        self.eta_label = tk.Label(
            details_frame,
            text="",
            font=('Arial', 10),
            fg='#7f8c8d',
            bg='#0a0a0a'
        )
        self.eta_label.pack(side='right')
    
    def create_log_area(self, parent):
        # Log container with header
        log_container = tk.Frame(parent, bg='#0a0a0a')
        log_container.pack(fill='both', expand=True)
        
        # Log header
        log_header = tk.Frame(log_container, bg='#0a0a0a')
        log_header.pack(fill='x', pady=(0, 5))
        
        log_title = tk.Label(
            log_header,
            text="📋 Activity Log",
            font=('Arial', 10, 'bold'),
            fg='#7f8c8d',
            bg='#0a0a0a'
        )
        log_title.pack(side='left')
        
        # Clear button
        clear_btn = tk.Label(
            log_header,
            text="Clear",
            font=('Arial', 9),
            fg='#3498db',
            bg='#0a0a0a',
            cursor='hand2'
        )
        clear_btn.pack(side='right')
        clear_btn.bind('<Button-1>', lambda e: self.clear_log())
        
        # Log frame
        log_frame = tk.Frame(log_container, bg='#1a1a1a', relief='flat', bd=0)
        log_frame.pack(fill='both', expand=True)
        
        # Log text widget with custom scrollbar
        log_inner = tk.Frame(log_frame, bg='#1a1a1a')
        log_inner.pack(fill='both', expand=True, padx=1, pady=1)
        
        self.log_text = tk.Text(
            log_inner,
            bg='#0f0f0f',
            fg='#cccccc',
            font=('Consolas', 9),
            height=6,
            wrap='word',
            relief='flat',
            bd=0,
            padx=10,
            pady=10,
            insertbackground='#ffffff'
        )
        self.log_text.pack(side='left', fill='both', expand=True)
        
        # Custom scrollbar
        scrollbar = tk.Frame(log_inner, bg='#1a1a1a', width=10)
        scrollbar.pack(side='right', fill='y')
        
        # Tags for colored text
        self.log_text.tag_config('info', foreground='#7f8c8d')
        self.log_text.tag_config('success', foreground='#2ecc71', font=('Consolas', 9, 'bold'))
        self.log_text.tag_config('error', foreground='#e74c3c', font=('Consolas', 9, 'bold'))
        self.log_text.tag_config('warning', foreground='#f39c12')
        self.log_text.tag_config('highlight', background='#2a2a2a')
    
    def create_footer(self):
        footer = tk.Frame(self.root, bg='#0a0a0a', height=40)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        
        # Footer content
        footer_content = tk.Frame(footer, bg='#0a0a0a')
        footer_content.pack(expand=True)
        
        # Settings icon
        settings_btn = tk.Label(
            footer_content,
            text="⚙",
            font=('Arial', 16),
            fg='#7f8c8d',
            bg='#0a0a0a',
            cursor='hand2'
        )
        settings_btn.pack(side='left', padx=(0, 15))
        settings_btn.bind('<Button-1>', lambda e: self.show_settings())
        
        # Status text
        self.footer_status = tk.Label(
            footer_content,
            text="Using .rcloneignore for exclusions",
            font=('Arial', 9),
            fg='#7f8c8d',
            bg='#0a0a0a'
        )
        self.footer_status.pack(side='left')
    
    def log(self, message, tag='info'):
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert('end', f"[{timestamp}] {message}\n", tag)
        self.log_text.see('end')
        self.root.update()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
    
    def show_settings(self):
        # Settings popup
        settings = tk.Toplevel(self.root)
        settings.title("Settings")
        settings.geometry("400x300")
        settings.configure(bg='#0a0a0a')
        settings.transient(self.root)
        
        # Center the settings window
        settings.update_idletasks()
        x = (settings.winfo_screenwidth() // 2) - (400 // 2)
        y = (settings.winfo_screenheight() // 2) - (300 // 2)
        settings.geometry(f'+{x}+{y}')
        
        # Settings content
        tk.Label(settings, text="Settings", font=('Arial', 16, 'bold'), 
                fg='white', bg='#0a0a0a').pack(pady=20)
        
        # Ignore file path
        tk.Label(settings, text="Ignore file: .rcloneignore", 
                font=('Arial', 10), fg='#7f8c8d', bg='#0a0a0a').pack()
        
        # Edit button
        edit_btn = tk.Button(
            settings,
            text="Edit Ignore Patterns",
            font=('Arial', 10),
            fg='white',
            bg='#3498db',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=lambda: os.system('notepad .rcloneignore')
        )
        edit_btn.pack(pady=20)
    
    def check_config(self):
        try:
            result = subprocess.run(['rclone.exe', 'listremotes'], 
                                  capture_output=True, text=True)
            if 'gdrive:' in result.stdout:
                self.log("✓ Google Drive configured", 'success')
                # Test connection
                test = subprocess.run(['rclone.exe', 'about', 'gdrive:', '--json'],
                                    capture_output=True, text=True)
                if test.returncode == 0:
                    data = json.loads(test.stdout)
                    total = data.get('total', 0) / (1024**3)  # Convert to GB
                    used = data.get('used', 0) / (1024**3)
                    free = total - used
                    self.log(f"Google Drive: {free:.1f}GB free of {total:.1f}GB", 'info')
                else:
                    self.log("⚠ Token may need refresh", 'warning')
            else:
                self.log("✗ Google Drive not configured. Run: rclone config", 'error')
                self.drop_text.config(text="Configuration Required")
                self.drop_subtext.config(text="Run: rclone config")
                self.disable_drop_zone()
        except:
            self.log("✗ rclone.exe not found", 'error')
            self.drop_text.config(text="RClone Not Found")
            self.drop_subtext.config(text="Place rclone.exe in current directory")
            self.disable_drop_zone()
    
    def disable_drop_zone(self):
        for widget in [self.drop_frame, self.inner_frame] + self.inner_frame.winfo_children():
            widget.config(cursor='arrow')
            widget.unbind('<Button-1>')
    
    def select_folder(self):
        if self.is_moving:
            return
            
        folder = filedialog.askdirectory(
            title="Select Folder to Move to Cloud"
        )
        if folder:
            self.process_folder(folder)
    
    def process_folder(self, folder):
        self.current_folder = folder
        folder_name = os.path.basename(folder)
        
        # Update UI immediately
        self.stat_cards['folder'].config(text=folder_name[:30] + "..." if len(folder_name) > 30 else folder_name)
        self.drop_text.config(text="Analyzing folder...")
        self.drop_subtext.config(text="Please wait")
        
        # Animate the drop zone
        self.animate_analyzing()
        
        # Calculate size in background
        thread = threading.Thread(target=self._analyze_folder, args=(folder,))
        thread.daemon = True
        thread.start()
    
    def animate_analyzing(self):
        # Simple loading animation
        if hasattr(self, '_analyzing') and self._analyzing:
            dots = getattr(self, '_dots', 0)
            self._dots = (dots + 1) % 4
            self.drop_subtext.config(text="Please wait" + "." * self._dots)
            self.root.after(500, self.animate_analyzing)
    
    def _analyze_folder(self, folder):
        self._analyzing = True
        self.log(f"Analyzing: {folder}")
        
        # Count files and size  
        total_size = 0
        file_count = 0
        ignored_count = 0
        
        # Load ignore patterns
        ignore_patterns = []
        if os.path.exists('.rcloneignore'):
            with open('.rcloneignore', 'r') as f:
                ignore_patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        start_time = time.time()
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder)
                
                # Check if file should be ignored
                is_ignored = any(self.matches_pattern(relative_path, pattern) for pattern in ignore_patterns)
                
                if is_ignored:
                    ignored_count += 1
                else:
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except:
                        pass
        
        analysis_time = time.time() - start_time
        size_gb = total_size / (1024 * 1024 * 1024)
        
        self._analyzing = False
        self.root.after(0, self._show_analysis, folder, file_count, size_gb, ignored_count, analysis_time)
    
    def matches_pattern(self, path, pattern):
        # Simple pattern matching (can be enhanced)
        import fnmatch
        path_parts = path.replace('\\', '/').split('/')
        pattern_parts = pattern.replace('\\', '/').split('/')
        
        for part, pat in zip(path_parts, pattern_parts):
            if pat.startswith('**'):
                return True
            if not fnmatch.fnmatch(part, pat):
                return False
        return True
    
    def _show_analysis(self, folder, file_count, size_gb, ignored_count, analysis_time):
        # Stop animation
        self._analyzing = False
        
        # Update stats cards with animation
        self.animate_counter(self.stat_cards['files'], 0, file_count, suffix=" files")
        
        size_text = f"{size_gb:.2f} GB" if size_gb >= 1 else f"{size_gb*1024:.0f} MB"
        self.stat_cards['size'].config(text=size_text)
        
        # Update drop zone
        self.drop_text.config(text="Ready to move to cloud")
        if ignored_count > 0:
            self.drop_subtext.config(text=f"Click to start • {ignored_count} files will be ignored")
            self.log(f"Analysis complete in {analysis_time:.1f}s", 'info')
            self.log(f"Files to move: {file_count:,} ({size_text})", 'info')
            self.log(f"Files to ignore: {ignored_count:,}", 'warning')
        else:
            self.drop_subtext.config(text="Click to start moving")
            self.log(f"Analysis complete in {analysis_time:.1f}s", 'info')
            self.log(f"Files to move: {file_count:,} ({size_text})", 'info')
        
        # Show confirmation dialog
        self.root.after(500, self._confirm_move, folder, file_count, size_gb)
    
    def animate_counter(self, label, start, end, duration=1000, suffix=""):
        # Animated counter
        steps = 30
        increment = (end - start) / steps
        
        def update_counter(current_step):
            if current_step <= steps:
                value = int(start + increment * current_step)
                label.config(text=f"{value:,}{suffix}")
                self.root.after(duration // steps, lambda: update_counter(current_step + 1))
            else:
                label.config(text=f"{end:,}{suffix}")
        
        update_counter(0)
    
    def _confirm_move(self, folder, file_count, size_gb):
        # Create confirmation dialog
        confirm_dialog = tk.Toplevel(self.root)
        confirm_dialog.title("Confirm Move")
        confirm_dialog.geometry("450x250")
        confirm_dialog.configure(bg='#0a0a0a')
        confirm_dialog.transient(self.root)
        confirm_dialog.resizable(False, False)
        
        # Center dialog
        confirm_dialog.update_idletasks()
        x = (confirm_dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (confirm_dialog.winfo_screenheight() // 2) - (250 // 2)
        confirm_dialog.geometry(f'+{x}+{y}')
        
        # Content
        tk.Label(
            confirm_dialog,
            text="⚠️ Confirm Move to Cloud",
            font=('Arial', 16, 'bold'),
            fg='#f39c12',
            bg='#0a0a0a'
        ).pack(pady=20)
        
        size_text = f"{size_gb:.2f} GB" if size_gb >= 1 else f"{size_gb*1024:.0f} MB"
        
        info_text = f"This will:\n\n• Upload {file_count:,} files ({size_text}) to Google Drive\n• Delete them from your laptop after verification\n• Free up {size_text} of space\n\nFiles will be moved to: gdrive:archived/"
        
        tk.Label(
            confirm_dialog,
            text=info_text,
            font=('Arial', 10),
            fg='#cccccc',
            bg='#0a0a0a',
            justify='left'
        ).pack(padx=30, pady=10)
        
        # Buttons
        button_frame = tk.Frame(confirm_dialog, bg='#0a0a0a')
        button_frame.pack(pady=20)
        
        def proceed():
            confirm_dialog.destroy()
            self.start_move(folder, file_count)
        
        def cancel():
            confirm_dialog.destroy()
            self.reset_ui()
        
        # Proceed button
        proceed_btn = tk.Button(
            button_frame,
            text="Move to Cloud",
            font=('Arial', 10, 'bold'),
            fg='white',
            bg='#e74c3c',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=proceed
        )
        proceed_btn.pack(side='left', padx=5)
        
        # Cancel button
        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=('Arial', 10),
            fg='white',
            bg='#7f8c8d',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=cancel
        )
        cancel_btn.pack(side='left', padx=5)
    
    def reset_ui(self):
        self.drop_text.config(text="Drop folder here or click to browse")
        self.drop_subtext.config(text="Supports folders up to 50GB")
        self.stat_cards['folder'].config(text="None")
        self.stat_cards['files'].config(text="0")
        self.stat_cards['size'].config(text="0 MB")
        self.log("Operation cancelled", 'info')
    
    def start_move(self, folder, expected_count):
        self.is_moving = True
        self.drop_text.config(text="Moving to cloud...")
        self.drop_subtext.config(text="Do not close this window")
        
        # Update status
        self.status_icon.config(text="⬆", fg='#3498db')
        self.status_label.config(text="Uploading to cloud")
        
        # Disable interactions
        for widget in [self.drop_frame, self.inner_frame] + self.inner_frame.winfo_children():
            widget.config(cursor='wait')
        
        # Start upload
        thread = threading.Thread(target=self._move_process, args=(folder, expected_count))
        thread.daemon = True
        thread.start()
    
    def update_progress(self, percent, speed="", eta=""):
        # Update progress bar with smooth animation
        self.progress_bar.place(relwidth=percent/100)
        self.progress_percent.config(text=f"{percent}%")
        
        if speed:
            self.speed_label.config(text=speed)
        if eta:
            self.eta_label.config(text=f"ETA: {eta}")
    
    def _move_process(self, folder, expected_count):
        self.start_time = time.time()
        folder_name = os.path.basename(folder)
        destination = f"gdrive:archived/{folder_name}"
        
        try:
            # Step 1: Upload
            self.root.after(0, lambda: self.log("📤 Starting upload to Google Drive...", 'info'))
            
            cmd = ['rclone.exe', 'copy', folder, destination]
            if os.path.exists('.rcloneignore'):
                cmd.extend(['--exclude-from', '.rcloneignore'])
            cmd.extend([
                '--transfers', '16',
                '--buffer-size', '32M',
                '--drive-chunk-size', '256M',
                '--fast-list',
                '--progress',
                '--stats', '1s',
                '--stats-one-line',
                '--log-level', 'INFO'
            ])
            
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            
            # Monitor progress with enhanced parsing
            last_percent = 0
            while True:
                line = process.stderr.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    # Parse progress info
                    if 'Transferred:' in line:
                        try:
                            # Extract percentage
                            if '%' in line:
                                percent_match = line.split('%')[0].split()[-1]
                                percent = int(percent_match)
                                
                                # Extract speed
                                speed = ""
                                if 'ETA' in line:
                                    parts = line.split(',')
                                    for part in parts:
                                        if '/s' in part:
                                            speed = part.strip()
                                            break
                                
                                # Extract ETA
                                eta = ""
                                if 'ETA' in line:
                                    eta_part = line.split('ETA')[1].strip()
                                    eta = eta_part.split()[0] if eta_part else ""
                                
                                # Update UI
                                if percent != last_percent:
                                    self.root.after(0, self.update_progress, percent, speed, eta)
                                    last_percent = percent
                                    
                                    # Log milestones
                                    if percent in [25, 50, 75]:
                                        self.root.after(0, lambda p=percent: self.log(f"Upload {p}% complete", 'info'))
                        except:
                            pass
            
            process.wait()
            
            if process.returncode != 0:
                stderr = process.stderr.read()
                raise Exception(f"Upload failed: {stderr}")
            
            self.root.after(0, lambda: self.log("✅ Upload completed successfully!", 'success'))
            self.root.after(0, self.update_progress, 100, "", "")
            
            # Step 2: Verify
            self.root.after(500, self._verify_upload, folder, destination, expected_count)
            
        except Exception as e:
            self.root.after(0, self._move_failed, str(e))
    
    def _verify_upload(self, local_folder, cloud_destination, expected_count):
        self.status_icon.config(text="🔍", fg='#2196F3')  
        self.status_label.config(text="Verifying upload")
        self.log("🔍 Verifying files in cloud...", 'info')
        
        # Run verification in background
        thread = threading.Thread(target=self._verify_thread, args=(local_folder, cloud_destination, expected_count))
        thread.daemon = True
        thread.start()
    
    def _verify_thread(self, local_folder, cloud_destination, expected_count):
        try:
            # Count cloud files
            result = subprocess.run(
                ['rclone.exe', 'size', cloud_destination, '--json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise Exception("Failed to check cloud files")
            
            data = json.loads(result.stdout)
            cloud_count = data.get('count', 0)
            cloud_size = data.get('bytes', 0) / (1024**3)  # GB
            
            self.root.after(0, lambda: self.log(f"📊 Cloud verification: {cloud_count:,} files, {cloud_size:.2f}GB", 'info'))
            
            # Do a detailed check
            self.root.after(0, lambda: self.log("🔄 Running integrity check...", 'info'))
            
            check_cmd = ['rclone.exe', 'check', local_folder, cloud_destination, '--one-way']
            if os.path.exists('.rcloneignore'):
                check_cmd.extend(['--exclude-from', '.rcloneignore'])
            
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            if check_result.returncode == 0:
                self.root.after(0, lambda: self.log("✅ All files verified successfully!", 'success'))
                self.root.after(0, lambda: self._delete_local(local_folder))
            else:
                # Parse check output for details
                output = check_result.stdout + check_result.stderr
                if "0 differences found" in output:
                    self.root.after(0, lambda: self.log("✅ Perfect match - all files uploaded!", 'success'))
                    self.root.after(0, lambda: self._delete_local(local_folder))
                else:
                    raise Exception("Some files may not have uploaded correctly")
                
        except Exception as e:
            self.root.after(0, lambda: self._move_failed(f"Verification error: {str(e)}"))
    
    def _delete_local(self, folder):
        self.status_icon.config(text="🗑", fg='#e74c3c')
        self.status_label.config(text="Removing local files")
        self.log("🗑 Deleting local files to free up space...", 'warning')
        
        # Show deletion progress
        self.progress_detail.config(text="Deleting files...")
        
        # Delete in background
        thread = threading.Thread(target=self._delete_thread, args=(folder,))
        thread.daemon = True
        thread.start()
    
    def _delete_thread(self, folder):
        try:
            # Count files for progress
            total_items = sum(1 for _ in Path(folder).rglob('*'))
            deleted = 0
            
            # Delete files first, then directories
            for item in Path(folder).rglob('*'):
                if item.is_file():
                    try:
                        item.unlink()
                        deleted += 1
                        if deleted % 100 == 0:  # Update every 100 files
                            percent = int((deleted / total_items) * 100)
                            self.root.after(0, lambda p=percent: self.progress_detail.config(text=f"Deleting... {p}%"))
                    except:
                        pass
            
            # Remove empty directories
            import shutil
            shutil.rmtree(folder)
            
            # Calculate freed space
            elapsed = time.time() - self.start_time
            elapsed_min = elapsed / 60
            
            self.root.after(0, lambda: self.log(f"✅ Deleted {total_items:,} items", 'success'))
            self.root.after(0, lambda: self.log(f"⏱ Total time: {elapsed_min:.1f} minutes", 'info'))
            self.root.after(0, self._move_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"⚠ Delete error: {str(e)}", 'error'))
            self.root.after(0, lambda: self.log("Files are safe in cloud but still on disk", 'warning'))
            self.root.after(0, self._move_complete)
    
    def _move_complete(self):
        self.is_moving = False
        
        # Success animation
        self.status_icon.config(text="✨", fg='#2ecc71')
        self.status_label.config(text="Move complete!")
        self.update_progress(100)
        
        # Update drop zone
        self.drop_text.config(text="Success! Space freed up")
        self.drop_subtext.config(text="Drop another folder to continue")
        
        # Re-enable interactions
        for widget in [self.drop_frame, self.inner_frame] + self.inner_frame.winfo_children():
            widget.config(cursor='hand2')
        
        # Play success sound if available
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        except:
            pass
        
        # Reset after delay
        self.root.after(5000, self.reset_after_success)
    
    def reset_after_success(self):
        self.drop_text.config(text="Drop folder here or click to browse")
        self.drop_subtext.config(text="Supports folders up to 50GB")
        self.status_icon.config(text="✓", fg='#4CAF50')
        self.status_label.config(text="Ready to move files")
        self.progress_bar.place(relwidth=0)
        self.progress_percent.config(text="0%")
        self.progress_detail.config(text="")
        self.speed_label.config(text="")
        self.eta_label.config(text="")
    
    def _move_failed(self, error):
        self.is_moving = False
        
        # Error UI
        self.status_icon.config(text="❌", fg='#e74c3c')
        self.status_label.config(text="Move failed")
        self.log(f"❌ {error}", 'error')
        
        # Update drop zone
        self.drop_text.config(text="Move failed - Files NOT deleted")
        self.drop_subtext.config(text="Click to try again")
        
        # Re-enable interactions
        for widget in [self.drop_frame, self.inner_frame] + self.inner_frame.winfo_children():
            widget.config(cursor='hand2')
        
        # Reset progress
        self.progress_bar.place(relwidth=0)
        self.progress_percent.config(text="0%")
        self.progress_detail.config(text="")
        
        # Play error sound
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_ICONHAND)
        except:
            pass

if __name__ == '__main__':
    app = CloudMover()