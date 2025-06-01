#!/usr/bin/env python3
"""File operations module for local file management."""

import os
import shutil
import fnmatch
from pathlib import Path
from typing import Callable, Optional, List, Tuple


class FileOperations:
    """Handles local file operations like deletion and cleanup."""
    
    @staticmethod
    def load_ignore_patterns(ignore_file_path: str) -> List[str]:
        """Load ignore patterns from file."""
        patterns = []
        if os.path.exists(ignore_file_path):
            with open(ignore_file_path, 'r') as f:
                patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return patterns
    
    @staticmethod
    def matches_pattern(path: str, pattern: str) -> bool:
        """Check if path matches ignore pattern."""
        path_parts = path.replace('\\', '/').split('/')
        pattern_parts = pattern.replace('\\', '/').split('/')
        
        # Handle ** patterns
        if '**' in pattern:
            return fnmatch.fnmatch(path.replace('\\', '/'), pattern.replace('\\', '/'))
        
        # Simple pattern matching
        for part, pat in zip(path_parts, pattern_parts):
            if not fnmatch.fnmatch(part, pat):
                return False
        return True
    
    @staticmethod
    def analyze_folder(folder: str, ignore_patterns: List[str]) -> Tuple[int, int, int]:
        """Analyze folder and return (total_size, file_count, ignored_count)."""
        total_size = 0
        file_count = 0
        ignored_count = 0
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder)
                
                # Check if file should be ignored
                is_ignored = any(FileOperations.matches_pattern(relative_path, pattern) 
                               for pattern in ignore_patterns)
                
                if is_ignored:
                    ignored_count += 1
                else:
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except:
                        pass
        
        return total_size, file_count, ignored_count
    
    @staticmethod
    def delete_folder(folder: str, progress_callback: Optional[Callable] = None) -> tuple[bool, str]:
        """Delete a folder and all its contents with progress tracking."""
        try:
            # Count total items for progress
            total_items = sum(1 for _ in Path(folder).rglob('*'))
            deleted = 0
            
            # Delete files first
            for item in Path(folder).rglob('*'):
                if item.is_file():
                    try:
                        item.unlink()
                        deleted += 1
                        
                        if progress_callback and deleted % 100 == 0:
                            percent = int((deleted / total_items) * 100)
                            progress_callback(percent, f"Deleting... {percent}%")
                    except Exception as e:
                        # Log but continue
                        pass
            
            # Remove the directory tree
            shutil.rmtree(folder)
            
            return True, f"Deleted {total_items:,} items"
            
        except Exception as e:
            return False, f"Delete error: {str(e)}"
    
    @staticmethod
    def get_folder_size(folder: str) -> int:
        """Get total size of a folder in bytes."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except:
                    pass
        return total_size
    
    @staticmethod
    def format_size(bytes_size: int) -> str:
        """Format bytes to human readable size."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"