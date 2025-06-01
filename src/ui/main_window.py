#!/usr/bin/env python3
"""Main window UI for Cloud Mover application."""

import tkinter as tk
from tkinter import ttk, filedialog, font, messagebox
import os
import threading
import time
from datetime import datetime
from pathlib import Path

from core.cloud_operations import CloudOperations
from core.file_operations import FileOperations


class CloudMoverUI:
    """Main UI class for Cloud Mover application."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Cloud Mover - Free Up Space")
        self.root.geometry("800x650")
        self.root.configure(bg='#0a0a0a')
        self.root.resizable(False, False)
        
        # Center window
        self.center_window()
        
        # Initialize core components
        self.cloud_ops = CloudOperations()
        self.file_ops = FileOperations()
        
        # Variables
        self.current_folders = []  # Changed to support multiple folders
        self.is_moving = False
        self.config_path = os.path.join("config", ".rcloneignore")
        
        # Create UI components
        self.setup_styles()
        self.create_header()
        self.create_main_content()
        self.create_footer()
        
        # Check configuration
        self.check_config()
        
        # Setup drag and drop
        self.setup_drag_drop()
        
    def center_window(self):
        """Center the window on screen."""
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (650 // 2)
        self.root.geometry(f'+{x}+{y}')
    
    def setup_styles(self):
        """Configure ttk styles."""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("success.Horizontal.TProgressbar", 
                       troughcolor='#1a1a1a', 
                       background='#4CAF50',
                       lightcolor='#4CAF50',
                       darkcolor='#4CAF50',
                       bordercolor='#1a1a1a')
    
    def create_header(self):
        """Create application header."""
        header_frame = tk.Frame(self.root, bg='#0a0a0a', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
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
        
        # Title
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
    
    def create_main_content(self):
        """Create main content area."""
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
    
    def create_drop_zone(self, parent):
        """Create the drop zone for folder selection."""
        drop_container = tk.Frame(parent, bg='#0a0a0a')
        drop_container.pack(fill='x', pady=(0, 20))
        
        # Main drop frame
        self.drop_frame = tk.Frame(drop_container, bg='#1a1a1a', relief='flat', bd=0, height=180)
        self.drop_frame.pack(fill='x')
        self.drop_frame.pack_propagate(False)
        
        # Inner content
        self.inner_frame = tk.Frame(self.drop_frame, bg='#1a1a1a')
        self.inner_frame.place(relx=0.5, rely=0.5, anchor='center')
        
        # Folder icon
        folder_icon = tk.Label(
            self.inner_frame,
            text="📁",
            font=('Arial', 48),
            fg='#3498db',
            bg='#1a1a1a'
        )
        folder_icon.pack()
        
        # Main text
        self.drop_text = tk.Label(
            self.inner_frame,
            text="Select folders to move to cloud",
            font=('Arial', 16, 'bold'),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        self.drop_text.pack(pady=(10, 5))
        
        # Sub text
        self.drop_subtext = tk.Label(
            self.inner_frame,
            text="Free up disk space instantly • Files moved, not copied",
            font=('Arial', 11),
            fg='#7f8c8d',
            bg='#1a1a1a'
        )
        self.drop_subtext.pack()
        
        # Single folder selection button
        select_btn = tk.Button(
            self.inner_frame,
            text="Select Folders",
            font=('Arial', 12, 'bold'),
            fg='white',
            bg='#3498db',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=self.select_folders
        )
        select_btn.pack(pady=(15, 0))
        
        # Make drop area clickable
        for widget in [self.drop_frame, self.inner_frame, folder_icon, self.drop_text, self.drop_subtext]:
            widget.bind('<Button-1>', lambda e: self.select_folders() if not self.is_moving else None)
            widget.bind('<Enter>', lambda e: self.on_hover_enter() if not self.is_moving else None)
            widget.bind('<Leave>', lambda e: self.on_hover_leave() if not self.is_moving else None)
            widget.config(cursor='hand2' if not self.is_moving else 'arrow')
    
    def create_stats_cards(self, parent):
        """Create statistics cards."""
        stats_frame = tk.Frame(parent, bg='#0a0a0a')
        stats_frame.pack(fill='x', pady=(0, 20))
        
        cards_data = [
            {"id": "folders", "label": "Selected Folders", "value": "0", "icon": "📂"},
            {"id": "files", "label": "Total Files", "value": "0", "icon": "📄"},
            {"id": "size", "label": "Total Size", "value": "0 MB", "icon": "💾"}
        ]
        
        self.stat_cards = {}
        
        for i, card_data in enumerate(cards_data):
            card = tk.Frame(stats_frame, bg='#1a1a1a', relief='flat', bd=0)
            card.pack(side='left', fill='both', expand=True, padx=(0 if i == 0 else 5, 0))
            
            card_inner = tk.Frame(card, bg='#1a1a1a')
            card_inner.pack(expand=True, pady=15)
            
            icon_label = tk.Label(
                card_inner,
                text=f"{card_data['icon']} {card_data['label']}",
                font=('Arial', 10),
                fg='#7f8c8d',
                bg='#1a1a1a'
            )
            icon_label.pack()
            
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
        """Create progress tracking section."""
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
        
        # Progress bar
        progress_bg = tk.Frame(progress_container, bg='#1a1a1a', height=8)
        progress_bg.pack(fill='x', pady=(0, 5))
        
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
        
        self.eta_label = tk.Label(
            details_frame,
            text="",
            font=('Arial', 10),
            fg='#7f8c8d',
            bg='#0a0a0a'
        )
        self.eta_label.pack(side='right')
    
    def create_log_area(self, parent):
        """Create activity log area."""
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
        
        # Log text
        log_frame = tk.Frame(log_container, bg='#1a1a1a', relief='flat', bd=0)
        log_frame.pack(fill='both', expand=True)
        
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
        
        # Tags for colored text
        self.log_text.tag_config('info', foreground='#7f8c8d')
        self.log_text.tag_config('success', foreground='#2ecc71', font=('Consolas', 9, 'bold'))
        self.log_text.tag_config('error', foreground='#e74c3c', font=('Consolas', 9, 'bold'))
        self.log_text.tag_config('warning', foreground='#f39c12')
    
    def create_footer(self):
        """Create application footer."""
        footer = tk.Frame(self.root, bg='#0a0a0a', height=40)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        
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
    
    # Helper methods
    def log(self, message, tag='info'):
        """Add message to activity log."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert('end', f"[{timestamp}] {message}\n", tag)
        self.log_text.see('end')
        self.root.update()
    
    def clear_log(self):
        """Clear the activity log."""
        self.log_text.delete(1.0, tk.END)
    
    def on_hover_enter(self):
        """Handle mouse hover enter."""
        if not self.is_moving:
            self.drop_frame.config(bg='#2a2a2a')
            self.inner_frame.config(bg='#2a2a2a')
            for widget in self.inner_frame.winfo_children():
                widget.config(bg='#2a2a2a')
    
    def on_hover_leave(self):
        """Handle mouse hover leave."""
        if not self.is_moving:
            self.drop_frame.config(bg='#1a1a1a')
            self.inner_frame.config(bg='#1a1a1a')
            for widget in self.inner_frame.winfo_children():
                widget.config(bg='#1a1a1a')
    
    def setup_drag_drop(self):
        """Setup drag and drop functionality."""
        try:
            from tkinterdnd2 import TkinterDnD, DND_FILES
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.handle_drop)
        except:
            pass  # Drag and drop not available
    
    def handle_drop(self, event):
        """Handle file drop event."""
        if self.is_moving:
            return
        files = self.root.tk.splitlist(event.data)
        if files and os.path.isdir(files[0]):
            self.process_folder(files[0])
    
    def check_config(self):
        """Check rclone configuration."""
        is_configured, message = self.cloud_ops.check_config()
        
        if is_configured:
            self.log(f"✓ Google Drive configured - {message}", 'success')
        else:
            self.log(f"✗ {message}", 'error')
            self.drop_text.config(text="Configuration Required")
            self.drop_subtext.config(text="Run: rclone config")
            self.disable_drop_zone()
    
    def disable_drop_zone(self):
        """Disable the drop zone."""
        for widget in [self.drop_frame, self.inner_frame] + self.inner_frame.winfo_children():
            widget.config(cursor='arrow')
            widget.unbind('<Button-1>')
    
    def select_folders(self):
        """Open unified folder selection dialog with multi-selection support."""
        if self.is_moving:
            return
        
        # Show proper multi-select folder browser
        self.show_multiselect_folder_browser()
    
    def show_multiselect_folder_browser(self):
        """Show Windows Explorer-style folder browser with true multi-selection."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Folders")
        dialog.geometry("800x600")
        dialog.configure(bg='#f0f0f0')
        dialog.transient(self.root)
        dialog.resizable(True, True)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f'+{x}+{y}')
        
        # Variables
        self.current_browse_path = os.path.expanduser("~")
        self.selected_folders = set()
        self.last_selected_index = None
        
        # Top toolbar
        toolbar = tk.Frame(dialog, bg='#e0e0e0', height=40)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        # Back button
        back_btn = tk.Button(
            toolbar, text="← Back", 
            command=lambda: self.navigate_to_parent(path_var, tree),
            bg='#d0d0d0', relief='flat', padx=10
        )
        back_btn.pack(side='left', padx=5, pady=5)
        
        # Path entry
        path_var = tk.StringVar(value=self.current_browse_path)
        path_entry = tk.Entry(toolbar, textvariable=path_var, font=('Arial', 10))
        path_entry.pack(side='left', fill='x', expand=True, padx=5, pady=5)
        path_entry.bind('<Return>', lambda e: self.navigate_to_path(path_var.get(), tree))
        
        # Main content frame
        content = tk.Frame(dialog, bg='#f0f0f0')
        content.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Create Treeview for folder display
        tree_frame = tk.Frame(content, bg='white', relief='sunken', bd=1)
        tree_frame.pack(fill='both', expand=True)
        
        # Treeview with columns
        tree = ttk.Treeview(tree_frame, columns=('Type', 'Size'), show='tree headings', selectmode='extended')
        tree.heading('#0', text='Name', anchor='w')
        tree.heading('Type', text='Type', anchor='w')
        tree.heading('Size', text='Size', anchor='w')
        
        tree.column('#0', width=400, minwidth=200)
        tree.column('Type', width=100, minwidth=80)
        tree.column('Size', width=100, minwidth=80)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack tree and scrollbars
        tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Selection info
        info_frame = tk.Frame(content, bg='#f0f0f0', height=60)
        info_frame.pack(fill='x', pady=(5, 0))
        info_frame.pack_propagate(False)
        
        selected_label = tk.Label(info_frame, text="No folders selected", 
                                bg='#f0f0f0', font=('Arial', 10))
        selected_label.pack(anchor='w', padx=5, pady=5)
        
        # Button frame
        btn_frame = tk.Frame(dialog, bg='#f0f0f0')
        btn_frame.pack(fill='x', padx=10, pady=10)
        
        # OK and Cancel buttons
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                             bg='#e0e0e0', padx=20, pady=5)
        cancel_btn.pack(side='right', padx=5)
        
        ok_btn = tk.Button(btn_frame, text="Move to Cloud", 
                         command=lambda: self.confirm_folder_selection(dialog),
                         bg='#0078d4', fg='white', padx=20, pady=5)
        ok_btn.pack(side='right', padx=5)
        
        # Bind events for multi-selection
        tree.bind('<Button-1>', lambda e: self.on_tree_click(e, tree, selected_label))
        tree.bind('<Control-Button-1>', lambda e: self.on_ctrl_click(e, tree, selected_label))
        tree.bind('<Shift-Button-1>', lambda e: self.on_shift_click(e, tree, selected_label))
        tree.bind('<Double-Button-1>', lambda e: self.on_double_click(e, tree, path_var))
        tree.bind('<Button1-Motion>', lambda e: self.on_drag_motion(e, tree))
        tree.bind('<ButtonRelease-1>', lambda e: self.on_drag_release(e, tree, selected_label))
        
        # Load initial directory
        self.load_directory(self.current_browse_path, tree, path_var)
        
    def navigate_to_parent(self, path_var, tree):
        """Navigate to parent directory."""
        current = path_var.get()
        parent = os.path.dirname(current)
        if parent != current:  # Not at root
            path_var.set(parent)
            self.current_browse_path = parent
            self.load_directory(parent, tree, path_var)
    
    def navigate_to_path(self, path, tree):
        """Navigate to specified path."""
        if os.path.isdir(path):
            self.current_browse_path = path
            self.load_directory(path, tree, None)
    
    def load_directory(self, path, tree, path_var=None):
        """Load directory contents into treeview."""
        tree.delete(*tree.get_children())
        self.selected_folders.clear()
        
        try:
            items = []
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    try:
                        size = self.get_folder_size(item_path)
                        items.append((item, item_path, size))
                    except:
                        items.append((item, item_path, "Access Denied"))
            
            # Sort directories
            items.sort(key=lambda x: x[0].lower())
            
            # Add to tree
            for name, full_path, size in items:
                tree.insert('', 'end', text=f"📁 {name}", 
                          values=('Folder', size), tags=(full_path,))
                          
        except PermissionError:
            tree.insert('', 'end', text="Access Denied", values=('Error', ''))
        except Exception as e:
            tree.insert('', 'end', text=f"Error: {str(e)}", values=('Error', ''))
    
    def get_folder_size(self, folder_path):
        """Get ACCURATE folder size - no limits for safety."""
        try:
            total = 0
            file_count = 0
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    try:
                        file_path = os.path.join(root, file)
                        total += os.path.getsize(file_path)
                        file_count += 1
                    except:
                        pass
            
            # Format size
            if total > 1024**3:
                size_str = f"{total/(1024**3):.2f} GB"
            elif total > 1024**2:
                size_str = f"{total/(1024**2):.1f} MB"
            elif total > 1024:
                size_str = f"{total/1024:.1f} KB"
            else:
                size_str = f"{total} B"
                
            return f"{size_str} ({file_count:,} files)"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def on_tree_click(self, event, tree, selected_label):
        """Handle single click selection."""
        item = tree.identify_row(event.y)
        if item:
            # Clear previous selection
            tree.selection_remove(*tree.selection())
            self.selected_folders.clear()
            
            # Select this item
            tree.selection_add(item)
            folder_path = tree.item(item, 'tags')[0]
            self.selected_folders.add(folder_path)
            self.last_selected_index = tree.index(item)
            
            self.update_selection_display(selected_label)
    
    def on_ctrl_click(self, event, tree, selected_label):
        """Handle Ctrl+click for multi-selection."""
        item = tree.identify_row(event.y)
        if item:
            folder_path = tree.item(item, 'tags')[0]
            
            if item in tree.selection():
                # Deselect if already selected
                tree.selection_remove(item)
                self.selected_folders.discard(folder_path)
            else:
                # Add to selection
                tree.selection_add(item)
                self.selected_folders.add(folder_path)
                self.last_selected_index = tree.index(item)
            
            self.update_selection_display(selected_label)
    
    def on_shift_click(self, event, tree, selected_label):
        """Handle Shift+click for range selection."""
        item = tree.identify_row(event.y)
        if item and self.last_selected_index is not None:
            current_index = tree.index(item)
            start_index = min(self.last_selected_index, current_index)
            end_index = max(self.last_selected_index, current_index)
            
            # Clear current selection
            tree.selection_remove(*tree.selection())
            self.selected_folders.clear()
            
            # Select range
            children = tree.get_children()
            for i in range(start_index, end_index + 1):
                if i < len(children):
                    child = children[i]
                    tree.selection_add(child)
                    folder_path = tree.item(child, 'tags')[0]
                    self.selected_folders.add(folder_path)
            
            self.update_selection_display(selected_label)
    
    def on_double_click(self, event, tree, path_var):
        """Handle double-click to navigate into folder."""
        item = tree.identify_row(event.y)
        if item:
            folder_path = tree.item(item, 'tags')[0]
            if os.path.isdir(folder_path):
                path_var.set(folder_path)
                self.current_browse_path = folder_path
                self.load_directory(folder_path, tree, path_var)
    
    def on_drag_motion(self, event, tree):
        """Handle drag motion for selection rectangle."""
        # Basic drag selection - could be enhanced
        pass
    
    def on_drag_release(self, event, tree, selected_label):
        """Handle drag release."""
        # Update selection display after drag
        self.update_selection_display(selected_label)
    
    def update_selection_display(self, selected_label):
        """Update the selection count display."""
        count = len(self.selected_folders)
        if count == 0:
            selected_label.config(text="No folders selected")
        elif count == 1:
            folder_name = os.path.basename(list(self.selected_folders)[0])
            selected_label.config(text=f"Selected: {folder_name}")
        else:
            selected_label.config(text=f"Selected {count} folders")
    
    def confirm_folder_selection(self, dialog):
        """Confirm the folder selection and proceed."""
        if self.selected_folders:
            self.current_folders = list(self.selected_folders)
            dialog.destroy()
            self.process_folders()
        else:
            messagebox.showwarning("No Selection", "Please select at least one folder.")

    def show_folder_browser(self):
        """Show unified folder selection dialog with Windows Explorer-like interface."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Folders")
        dialog.geometry("700x500")
        dialog.configure(bg='#0a0a0a')
        dialog.transient(self.root)
        dialog.resizable(True, True)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f'+{x}+{y}')
        
        # Header
        header_frame = tk.Frame(dialog, bg='#0a0a0a')
        header_frame.pack(fill='x', padx=20, pady=20)
        
        tk.Label(
            header_frame,
            text="Select Folders",
            font=('Arial', 16, 'bold'),
            fg='white',
            bg='#0a0a0a'
        ).pack(side='left')
        
        tk.Label(
            header_frame,
            text="Use Ctrl+Click or Shift+Click to select multiple",
            font=('Arial', 10),
            fg='#7f8c8d',
            bg='#0a0a0a'
        ).pack(side='right')
        
        # Main content frame
        content_frame = tk.Frame(dialog, bg='#1a1a1a')
        content_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        # Path frame
        path_frame = tk.Frame(content_frame, bg='#2a2a2a', height=35)
        path_frame.pack(fill='x', padx=10, pady=10)
        path_frame.pack_propagate(False)
        
        self.current_path = os.path.expanduser("~")
        path_var = tk.StringVar(value=self.current_path)
        
        tk.Label(path_frame, text="Location:", bg='#2a2a2a', fg='white', font=('Arial', 9)).pack(side='left', padx=(10, 5), pady=8)
        path_entry = tk.Entry(path_frame, textvariable=path_var, bg='#3a3a3a', fg='white', relief='flat', bd=0)
        path_entry.pack(side='left', fill='x', expand=True, padx=(0, 10), pady=5)
        
        # Folder list frame
        list_frame = tk.Frame(content_frame, bg='#1a1a1a')
        list_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))
        
        # Create listbox with scrollbar
        list_container = tk.Frame(list_frame, bg='#2a2a2a')
        list_container.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_container, orient='vertical')
        scrollbar.pack(side='right', fill='y')
        
        # Listbox for folders (with multi-selection enabled)
        folders_listbox = tk.Listbox(
            list_container,
            bg='#2a2a2a',
            fg='white',
            font=('Arial', 10),
            selectbackground='#3498db',
            selectmode=tk.EXTENDED,  # Enable multi-selection
            relief='flat',
            bd=0,
            yscrollcommand=scrollbar.set
        )
        folders_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=folders_listbox.yview)
        
        # Storage for folder paths and selection
        folder_paths = []
        selected_folders = []
        
        def load_folders(path):
            """Load folders in the given path."""
            folders_listbox.delete(0, tk.END)
            folder_paths.clear()
            
            try:
                # Add parent directory option if not at root
                if path != os.path.dirname(path):
                    folders_listbox.insert(tk.END, ".. (Parent Directory)")
                    folder_paths.append(os.path.dirname(path))
                
                # List all directories
                items = []
                for item in os.listdir(path):
                    item_path = os.path.join(path, item)
                    if os.path.isdir(item_path):
                        items.append((item, item_path))
                
                # Sort directories
                items.sort(key=lambda x: x[0].lower())
                
                for folder_name, folder_path in items:
                    folders_listbox.insert(tk.END, f"📁 {folder_name}")
                    folder_paths.append(folder_path)
                    
            except PermissionError:
                folders_listbox.insert(tk.END, "Permission denied")
            except Exception as e:
                folders_listbox.insert(tk.END, f"Error: {str(e)}")
        
        def on_double_click(event):
            """Handle double-click to navigate into folder."""
            selection = folders_listbox.curselection()
            if selection:
                index = selection[0]
                if index < len(folder_paths):
                    new_path = folder_paths[index]
                    if os.path.isdir(new_path):
                        self.current_path = new_path
                        path_var.set(new_path)
                        load_folders(new_path)
        
        def on_path_change(event):
            """Handle manual path entry."""
            new_path = path_var.get()
            if os.path.isdir(new_path):
                self.current_path = new_path
                load_folders(new_path)
        
        def add_selected():
            """Add selected folders to selection."""
            selections = folders_listbox.curselection()
            for index in selections:
                if index < len(folder_paths):
                    folder_path = folder_paths[index]
                    if os.path.isdir(folder_path) and folder_path not in selected_folders:
                        selected_folders.append(folder_path)
            update_selection_display()
        
        def remove_selected():
            """Remove selected folders from selection."""
            to_remove = []
            for index in selection_listbox.curselection():
                if index < len(selected_folders):
                    to_remove.append(selected_folders[index])
            
            for folder in to_remove:
                selected_folders.remove(folder)
            update_selection_display()
        
        def update_selection_display():
            """Update the selection display."""
            selection_listbox.delete(0, tk.END)
            for folder in selected_folders:
                selection_listbox.insert(tk.END, os.path.basename(folder))
        
        def confirm_selection():
            """Confirm the folder selection."""
            if selected_folders:
                self.current_folders = selected_folders.copy()
                dialog.destroy()
                self.process_folders()
            else:
                messagebox.showwarning("No Selection", "Please select at least one folder.")
        
        # Bind events
        folders_listbox.bind('<Double-Button-1>', on_double_click)
        path_entry.bind('<Return>', on_path_change)
        
        # Selection area
        selection_frame = tk.Frame(content_frame, bg='#1a1a1a')
        selection_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        tk.Label(selection_frame, text="Selected Folders:", bg='#1a1a1a', fg='white', font=('Arial', 10, 'bold')).pack(anchor='w')
        
        selection_container = tk.Frame(selection_frame, bg='#2a2a2a', height=80)
        selection_container.pack(fill='x', pady=(5, 0))
        selection_container.pack_propagate(False)
        
        selection_listbox = tk.Listbox(
            selection_container,
            bg='#2a2a2a',
            fg='white',
            font=('Arial', 9),
            selectbackground='#3498db',
            relief='flat',
            bd=0,
            height=4
        )
        selection_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Button frame
        btn_frame = tk.Frame(content_frame, bg='#1a1a1a')
        btn_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        # Left side buttons
        left_buttons = tk.Frame(btn_frame, bg='#1a1a1a')
        left_buttons.pack(side='left')
        
        tk.Button(
            left_buttons,
            text="Add Selected",
            font=('Arial', 10),
            fg='white',
            bg='#27ae60',
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2',
            command=add_selected
        ).pack(side='left', padx=(0, 5))
        
        tk.Button(
            left_buttons,
            text="Remove",
            font=('Arial', 10),
            fg='white',
            bg='#e74c3c',
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2',
            command=remove_selected
        ).pack(side='left', padx=5)
        
        # Right side buttons
        right_buttons = tk.Frame(btn_frame, bg='#1a1a1a')
        right_buttons.pack(side='right')
        
        tk.Button(
            right_buttons,
            text="Cancel",
            font=('Arial', 10),
            fg='white',
            bg='#7f8c8d',
            relief='flat',
            bd=0,
            padx=15,
            pady=8,
            cursor='hand2',
            command=dialog.destroy
        ).pack(side='right', padx=(5, 0))
        
        tk.Button(
            right_buttons,
            text="Move to Cloud",
            font=('Arial', 10, 'bold'),
            fg='white',
            bg='#3498db',
            relief='flat',
            bd=0,
            padx=20,
            pady=8,
            cursor='hand2',
            command=confirm_selection
        ).pack(side='right', padx=(15, 5))
        
        # Load initial folders
        load_folders(self.current_path)
    
    def process_folders(self):
        """Process selected folders for upload."""
        if not self.current_folders:
            return
        
        # Update UI
        folder_count = len(self.current_folders)
        self.stat_cards['folders'].config(text=str(folder_count))
        
        if folder_count == 1:
            folder_name = os.path.basename(self.current_folders[0])
            self.drop_text.config(text=f"Analyzing: {folder_name}")
        else:
            self.drop_text.config(text=f"Analyzing {folder_count} folders...")
        
        self.drop_subtext.config(text="Please wait")
        
        # Analyze in background
        thread = threading.Thread(target=self._analyze_folders)
        thread.daemon = True
        thread.start()
    
    def _analyze_folders(self):
        """Analyze multiple folders in background thread."""
        total_size = 0
        total_files = 0
        total_ignored = 0
        
        # Load ignore patterns
        ignore_patterns = self.file_ops.load_ignore_patterns(self.config_path)
        
        start_time = time.time()
        
        for i, folder in enumerate(self.current_folders):
            self.root.after(0, lambda f=folder, idx=i+1, total=len(self.current_folders): 
                           self.log(f"[{idx}/{total}] Analyzing: {os.path.basename(f)}", 'info'))
            
            folder_size, folder_files, folder_ignored = self.file_ops.analyze_folder(folder, ignore_patterns)
            total_size += folder_size
            total_files += folder_files
            total_ignored += folder_ignored
        
        analysis_time = time.time() - start_time
        size_gb = total_size / (1024 * 1024 * 1024)
        
        self.root.after(0, self._show_analysis, total_files, size_gb, total_ignored, analysis_time)
    
    def _show_analysis(self, file_count, size_gb, ignored_count, analysis_time):
        """Show analysis results for folders."""
        # Update stats
        self.stat_cards['files'].config(text=f"{file_count:,}")
        
        size_text = f"{size_gb:.2f} GB" if size_gb >= 1 else f"{size_gb*1024:.0f} MB"
        self.stat_cards['size'].config(text=size_text)
        
        # Update drop zone
        folder_count = len(self.current_folders)
        if folder_count == 1:
            self.drop_text.config(text="Ready to move to cloud")
        else:
            self.drop_text.config(text=f"Ready to move {folder_count} folders")
        
        if ignored_count > 0:
            self.drop_subtext.config(text=f"Click to start • {ignored_count} files will be ignored")
            self.log(f"Analysis complete in {analysis_time:.1f}s", 'info')
            self.log(f"Files to move: {file_count:,} ({size_text}) from {folder_count} folders", 'info')
            self.log(f"Files to ignore: {ignored_count:,}", 'warning')
        else:
            self.drop_subtext.config(text="Click to start moving")
            self.log(f"Analysis complete in {analysis_time:.1f}s", 'info')
            self.log(f"Files to move: {file_count:,} ({size_text}) from {folder_count} folders", 'info')
        
        # Show confirmation
        self.root.after(500, self._confirm_move, file_count, size_gb)
    
    def _confirm_move(self, file_count, size_gb):
        """Show move confirmation dialog."""
        size_text = f"{size_gb:.2f} GB" if size_gb >= 1 else f"{size_gb*1024:.0f} MB"
        folder_count = len(self.current_folders)
        
        if folder_count == 1:
            folder_text = f"folder '{os.path.basename(self.current_folders[0])}'"
        else:
            folder_text = f"{folder_count} folders"
        
        result = messagebox.askyesno(
            "Confirm Move to Cloud",
            f"This will:\n\n"
            f"• Upload {file_count:,} files ({size_text}) from {folder_text} to Google Drive\n"
            f"• Delete them from your laptop after verification\n"
            f"• Free up {size_text} of space\n\n"
            f"Files will be moved to: gdrive:archived/\n\n"
            f"Continue?",
            icon='warning'
        )
        
        if result:
            self.start_move(file_count)
        else:
            self.reset_ui()
    
    def reset_ui(self):
        """Reset UI to initial state."""
        self.drop_text.config(text="Select folders to move to cloud")
        self.drop_subtext.config(text="Free up disk space instantly • Files moved, not copied")
        self.stat_cards['folders'].config(text="0")
        self.stat_cards['files'].config(text="0")
        self.stat_cards['size'].config(text="0 MB")
        self.log("Operation cancelled", 'info')
    
    def start_move(self, expected_count):
        """Start the move process for selected folders."""
        self.is_moving = True
        folder_count = len(self.current_folders)
        
        if folder_count == 1:
            self.drop_text.config(text="Moving to cloud...")
        else:
            self.drop_text.config(text=f"Moving {folder_count} folders to cloud...")
        
        self.drop_subtext.config(text="Do not close this window")
        
        # Update status
        self.status_icon.config(text="⬆", fg='#3498db')
        self.status_label.config(text="Moving to cloud...")
        
        # Disable interactions
        for widget in [self.drop_frame, self.inner_frame] + self.inner_frame.winfo_children():
            widget.config(cursor='wait')
        
        # Start upload
        thread = threading.Thread(target=self._move_process, args=(expected_count,))
        thread.daemon = True
        thread.start()
    
    def update_progress(self, percent, speed="", eta=""):
        """Update progress display."""
        self.progress_bar.place(relwidth=percent/100)
        self.progress_percent.config(text=f"{percent}%")
        
        if speed:
            self.speed_label.config(text=speed)
        if eta:
            self.eta_label.config(text=f"ETA: {eta}")
    
    def _move_process(self, expected_count):
        """Handle the complete move process for multiple folders."""
        self.start_time = time.time()
        
        try:
            # Upload multiple folders
            self.root.after(0, lambda: self.log("📤 Starting move to Google Drive...", 'info'))
            
            def progress_callback(message):
                self.root.after(0, lambda msg=message: self.log(msg, 'info'))
                # Update progress if it contains percentage
                if '%' in message:
                    try:
                        percent = int(message.split('%')[0].split()[-1])
                        self.root.after(0, lambda p=percent: self.update_progress(p))
                    except:
                        pass
            
            if len(self.current_folders) == 1:
                # Single folder upload
                success, result = self.cloud_ops.upload_folder(
                    self.current_folders[0], 
                    progress_callback=progress_callback,
                    ignore_file=self.config_path
                )
            else:
                # Multiple folder upload
                success, result = self.cloud_ops.upload_multiple_folders(
                    self.current_folders,
                    progress_callback=progress_callback,
                    ignore_file=self.config_path
                )
            
            if not success:
                error_msg = result.get('error', 'Upload failed')
                raise Exception(error_msg)
            
            self.root.after(0, lambda: self.log("✅ Upload completed successfully!", 'success'))
            self.root.after(0, lambda: self.log("🔍 Now verifying upload before deleting local files...", 'info'))
            self.root.after(0, self.update_progress, 100, "", "")
            
            # CRITICAL: Verify upload before any deletion
            self.root.after(500, self._verify_before_delete, expected_count)
            
        except Exception as e:
            error_msg = f"Exception during move: {str(e)}"
            self.root.after(0, lambda: self.log(f"EXCEPTION: {error_msg}", 'error'))
            self.root.after(0, self._move_failed, error_msg)
    
    def _verify_before_delete(self, expected_count):
        """CRITICAL: Verify upload is 100% complete before any deletion."""
        self.status_icon.config(text="🔍", fg='#2196F3')
        self.status_label.config(text="Verifying upload safety...")
        self.log("🔍 SAFETY CHECK: Verifying all files uploaded successfully...", 'info')
        
        thread = threading.Thread(target=self._verify_thread_safe, args=(expected_count,))
        thread.daemon = True
        thread.start()
    
    def _verify_thread_safe(self, expected_count):
        """SAFE verification thread - only delete if 100% verified."""
        try:
            all_verified = True
            verification_results = []
            
            for i, folder in enumerate(self.current_folders):
                folder_name = os.path.basename(folder)
                self.root.after(0, lambda fn=folder_name, idx=i+1, total=len(self.current_folders): 
                               self.log(f"[{idx}/{total}] Verifying: {fn}", 'info'))
                
                # Verify this folder
                success, result = self.cloud_ops.verify_upload(folder)
                verification_results.append({
                    'folder': folder,
                    'success': success,
                    'result': result
                })
                
                if not success:
                    all_verified = False
                    self.root.after(0, lambda fn=folder_name, err=result.get('error', 'Unknown error'): 
                                   self.log(f"❌ VERIFICATION FAILED for {fn}: {err}", 'error'))
                else:
                    cloud_count = result.get('cloud_count', 0)
                    cloud_size_gb = result.get('cloud_size_gb', 0)
                    self.root.after(0, lambda fn=folder_name, cc=cloud_count, cs=cloud_size_gb: 
                                   self.log(f"✅ {fn}: {cc:,} files, {cs:.2f}GB verified in cloud", 'success'))
            
            if all_verified:
                self.root.after(0, lambda: self.log("🎉 ALL FILES VERIFIED SUCCESSFULLY IN CLOUD!", 'success'))
                self.root.after(0, lambda: self.log("⚠️  SAFE TO DELETE: Starting local file deletion...", 'warning'))
                self.root.after(0, self._delete_local_safe)
            else:
                self.root.after(0, lambda: self.log("❌ VERIFICATION FAILED - NO FILES WILL BE DELETED", 'error'))
                self.root.after(0, lambda: self.log("📂 Your files are SAFE on your laptop", 'info'))
                self.root.after(0, self._upload_verified_but_incomplete)
                
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ VERIFICATION ERROR: {str(e)}", 'error'))
            self.root.after(0, lambda: self.log("📂 NO FILES DELETED - Your data is safe", 'info'))
            self.root.after(0, lambda: self._move_failed(f"Verification error: {str(e)}"))
    
    def _upload_verified_but_incomplete(self):
        """Handle case where upload succeeded but verification failed."""
        self.is_moving = False
        
        self.status_icon.config(text="⚠️", fg='#f39c12')
        self.status_label.config(text="Upload successful, verification incomplete")
        
        self.drop_text.config(text="Files uploaded but verification failed")
        self.drop_subtext.config(text="Check cloud manually - local files preserved for safety")
        
        # Re-enable interactions
        for widget in [self.drop_frame, self.inner_frame] + self.inner_frame.winfo_children():
            widget.config(cursor='hand2')
        
        # Reset progress
        self.progress_bar.place(relwidth=0)
        self.progress_percent.config(text="0%")
        self.progress_detail.config(text="")
    
    def _delete_local_safe(self):
        """SAFELY delete local files after 100% verification."""
        self.status_icon.config(text="🗑", fg='#e74c3c')
        self.status_label.config(text="Safely removing local files")
        
        folder_count = len(self.current_folders)
        if folder_count == 1:
            self.log("🗑 SAFE DELETE: Removing verified files from laptop...", 'warning')
        else:
            self.log(f"🗑 SAFE DELETE: Removing {folder_count} verified folders from laptop...", 'warning')
        
        self.progress_detail.config(text="Safely deleting verified files...")
        
        thread = threading.Thread(target=self._delete_thread_safe)
        thread.daemon = True
        thread.start()
    
    def _delete_thread_safe(self):
        """SAFELY delete files in background thread."""
        try:
            def delete_progress(percent, message):
                self.root.after(0, lambda: self.progress_detail.config(text=message))
            
            total_deleted = 0
            failed_deletions = []
            
            for i, folder in enumerate(self.current_folders):
                folder_name = os.path.basename(folder)
                self.root.after(0, lambda fn=folder_name, idx=i+1, total=len(self.current_folders): 
                               self.log(f"[{idx}/{total}] SAFE DELETE: {fn}", 'info'))
                
                success, message = self.file_ops.delete_folder(folder, delete_progress)
                
                if success:
                    total_deleted += 1
                    self.root.after(0, lambda fn=folder_name: self.log(f"✅ DELETED: {fn}", 'success'))
                else:
                    failed_deletions.append((folder_name, message))
                    self.root.after(0, lambda fn=folder_name, msg=message: 
                                   self.log(f"⚠ Failed to delete {fn}: {msg}", 'error'))
            
            # Calculate time and report results
            elapsed = time.time() - self.start_time
            elapsed_min = elapsed / 60
            
            total_folders = len(self.current_folders)
            
            if total_deleted == total_folders:
                self.root.after(0, lambda: self.log(f"🎉 SUCCESS: Moved {total_deleted}/{total_folders} folders to cloud", 'success'))
                self.root.after(0, lambda: self.log(f"⏱ Total time: {elapsed_min:.1f} minutes", 'info'))
            elif total_deleted > 0:
                self.root.after(0, lambda: self.log(f"⚠ Partial success: {total_deleted}/{total_folders} folders moved", 'warning'))
                self.root.after(0, lambda: self.log("Some files are in cloud but still on disk", 'warning'))
            else:
                self.root.after(0, lambda: self.log("⚠ No folders were deleted", 'error'))
                self.root.after(0, lambda: self.log("Files are safe in cloud but still on disk", 'warning'))
            
            self.root.after(0, self._move_complete_safe)
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"⚠ Delete error: {str(e)}", 'error'))
            self.root.after(0, self._move_complete_safe)
    
    def _move_complete_safe(self):
        """Handle safe move completion."""
        self.is_moving = False
        
        # Success animation
        self.status_icon.config(text="✨", fg='#2ecc71')
        self.status_label.config(text="Safe move complete!")
        self.update_progress(100)
        
        # Update drop zone
        folder_count = len(self.current_folders)
        if folder_count == 1:
            self.drop_text.config(text="✅ Files safely moved to cloud")
        else:
            self.drop_text.config(text=f"✅ {folder_count} folders safely moved")
        self.drop_subtext.config(text="Files verified before deletion • Your data is safe")
        
        # Re-enable interactions
        for widget in [self.drop_frame, self.inner_frame] + self.inner_frame.winfo_children():
            widget.config(cursor='hand2')
        
        # Reset after delay
        self.root.after(5000, self.reset_after_success)
    
    def _verify_upload(self, expected_count):
        """Verify upload completion for all folders."""
        self.status_icon.config(text="🔍", fg='#2196F3')
        self.status_label.config(text="Verifying upload")
        self.log("🔍 Verifying files in cloud...", 'info')
        
        thread = threading.Thread(target=self._verify_thread, args=(expected_count,))
        thread.daemon = True
        thread.start()
    
    def _verify_thread(self, expected_count):
        """Verify upload in background thread for all folders."""
        try:
            if len(self.current_folders) == 1:
                # Single folder verification
                success, result = self.cloud_ops.verify_upload(self.current_folders[0])
                
                if success:
                    cloud_count = result['cloud_count']
                    cloud_size = result['cloud_size_gb']
                    
                    self.root.after(0, lambda: self.log(
                        f"📊 Cloud verification: {cloud_count:,} files, {cloud_size:.2f}GB", 'info'
                    ))
                    self.root.after(0, lambda: self.log("✅ All files verified successfully!", 'success'))
                    self.root.after(0, lambda: self._delete_local())
                else:
                    raise Exception(result.get('error', 'Verification failed'))
            else:
                # Multiple folder verification
                success, result = self.cloud_ops.verify_multiple_uploads(self.current_folders)
                
                if success:
                    total_verified = len(result['results'])
                    self.root.after(0, lambda: self.log(
                        f"📊 Verified {total_verified} folders successfully", 'info'
                    ))
                    self.root.after(0, lambda: self.log("✅ All files verified successfully!", 'success'))
                    self.root.after(0, lambda: self._delete_local())
                else:
                    raise Exception(result.get('error', 'Verification failed'))
                
        except Exception as e:
            self.root.after(0, lambda: self._move_failed(f"Verification error: {str(e)}"))
    
    def _delete_local(self):
        """Delete local files after verification."""
        self.status_icon.config(text="🗑", fg='#e74c3c')
        self.status_label.config(text="Removing local files")
        
        folder_count = len(self.current_folders)
        if folder_count == 1:
            self.log("🗑 Deleting local files to free up space...", 'warning')
        else:
            self.log(f"🗑 Deleting {folder_count} local folders to free up space...", 'warning')
        
        self.progress_detail.config(text="Deleting files...")
        
        thread = threading.Thread(target=self._delete_thread)
        thread.daemon = True
        thread.start()
    
    def _delete_thread(self):
        """Delete files in background thread."""
        try:
            def delete_progress(percent, message):
                self.root.after(0, lambda: self.progress_detail.config(text=message))
            
            total_deleted = 0
            failed_deletions = []
            
            for i, folder in enumerate(self.current_folders):
                folder_name = os.path.basename(folder)
                self.root.after(0, lambda fn=folder_name, idx=i+1, total=len(self.current_folders): 
                               self.log(f"[{idx}/{total}] Deleting: {fn}", 'info'))
                
                success, message = self.file_ops.delete_folder(folder, delete_progress)
                
                if success:
                    total_deleted += 1
                    self.root.after(0, lambda fn=folder_name: self.log(f"✅ Deleted: {fn}", 'success'))
                else:
                    failed_deletions.append((folder_name, message))
                    self.root.after(0, lambda fn=folder_name, msg=message: 
                                   self.log(f"⚠ Failed to delete {fn}: {msg}", 'error'))
            
            # Calculate time and report results
            elapsed = time.time() - self.start_time
            elapsed_min = elapsed / 60
            
            total_folders = len(self.current_folders)
            
            if total_deleted == total_folders:
                self.root.after(0, lambda: self.log(f"✅ Successfully deleted {total_deleted}/{total_folders} folders", 'success'))
                self.root.after(0, lambda: self.log(f"⏱ Total time: {elapsed_min:.1f} minutes", 'info'))
            elif total_deleted > 0:
                self.root.after(0, lambda: self.log(f"⚠ Partially successful: {total_deleted}/{total_folders} folders deleted", 'warning'))
                self.root.after(0, lambda: self.log("Some files are safe in cloud but still on disk", 'warning'))
            else:
                self.root.after(0, lambda: self.log("⚠ No folders were deleted", 'error'))
                self.root.after(0, lambda: self.log("Files are safe in cloud but still on disk", 'warning'))
            
            # List failed deletions
            for folder_name, error_msg in failed_deletions:
                self.root.after(0, lambda fn=folder_name, msg=error_msg: 
                               self.log(f"Failed: {fn} - {msg}", 'error'))
            
            self.root.after(0, self._move_complete)
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"⚠ Delete error: {str(e)}", 'error'))
            self.root.after(0, self._move_complete)
    
    def _move_complete(self):
        """Handle move completion."""
        self.is_moving = False
        
        # Success animation
        self.status_icon.config(text="✨", fg='#2ecc71')
        self.status_label.config(text="Move complete!")
        self.update_progress(100)
        
        # Update drop zone
        folder_count = len(self.current_folders)
        if folder_count == 1:
            self.drop_text.config(text="Success! Space freed up")
        else:
            self.drop_text.config(text=f"Success! {folder_count} folders moved")
        self.drop_subtext.config(text="Drop more folders to continue")
        
        # Re-enable interactions
        for widget in [self.drop_frame, self.inner_frame] + self.inner_frame.winfo_children():
            widget.config(cursor='hand2')
        
        # Play success sound
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK)
        except:
            pass
        
        # Reset after delay
        self.root.after(5000, self.reset_after_success)
    
    def reset_after_success(self):
        """Reset UI after successful operation."""
        self.drop_text.config(text="Select folders to move to cloud")
        self.drop_subtext.config(text="Free up disk space instantly • Files moved, not copied")
        self.status_icon.config(text="✓", fg='#4CAF50')
        self.status_label.config(text="Ready to move files")
        self.progress_bar.place(relwidth=0)
        self.progress_percent.config(text="0%")
        self.progress_detail.config(text="")
        self.speed_label.config(text="")
        self.eta_label.config(text="")
    
    def _move_failed(self, error):
        """Handle move failure."""
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
    
    def show_settings(self):
        """Show settings dialog."""
        settings = tk.Toplevel(self.root)
        settings.title("Settings")
        settings.geometry("400x300")
        settings.configure(bg='#0a0a0a')
        settings.transient(self.root)
        
        # Center
        settings.update_idletasks()
        x = (settings.winfo_screenwidth() // 2) - (400 // 2)
        y = (settings.winfo_screenheight() // 2) - (300 // 2)
        settings.geometry(f'+{x}+{y}')
        
        # Content
        tk.Label(settings, text="Settings", font=('Arial', 16, 'bold'), 
                fg='white', bg='#0a0a0a').pack(pady=20)
        
        tk.Label(settings, text="Ignore file: config/.rcloneignore", 
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
            command=lambda: os.system(f'notepad {self.config_path}')
        )
        edit_btn.pack(pady=20)
    
    def run(self):
        """Start the application."""
        self.root.mainloop()