#!/usr/bin/env python3
"""Cloud operations module for handling rclone interactions."""

import os
import subprocess
import json
import time
from pathlib import Path
from typing import Dict, Tuple, Optional, List


class CloudOperations:
    """Handles all cloud-related operations using rclone."""
    
    def __init__(self, rclone_path: str = "rclone.exe"):
        self.rclone_path = rclone_path
        self.remote_name = "gdrive"
        self.archive_folder = "archived"
        
    def check_config(self) -> Tuple[bool, str]:
        """Check if rclone is configured properly."""
        try:
            # Check if rclone exists
            if not os.path.exists(self.rclone_path):
                return False, "rclone.exe not found"
                
            # Check remotes
            result = subprocess.run(
                [self.rclone_path, 'listremotes'], 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            print(f"DEBUG: rclone listremotes output: {result.stdout}")
            print(f"DEBUG: rclone listremotes stderr: {result.stderr}")
            
            if f'{self.remote_name}:' not in result.stdout:
                return False, f"{self.remote_name} remote not configured. Available: {result.stdout.strip()}"
                
            # Test connection
            test = subprocess.run(
                [self.rclone_path, 'about', f'{self.remote_name}:', '--json'],
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            print(f"DEBUG: rclone about return code: {test.returncode}")
            print(f"DEBUG: rclone about stdout: {test.stdout}")
            print(f"DEBUG: rclone about stderr: {test.stderr}")
            
            if test.returncode == 0:
                data = json.loads(test.stdout)
                total_gb = data.get('total', 0) / (1024**3)
                used_gb = data.get('used', 0) / (1024**3)
                free_gb = total_gb - used_gb
                return True, f"{free_gb:.1f}GB free of {total_gb:.1f}GB"
            else:
                return False, "Token may need refresh"
                
        except Exception as e:
            return False, str(e)
    
    def analyze_folder(self, folder: str, ignore_file: str = None) -> Dict:
        """Analyze folder to get file count and size."""
        total_size = 0
        file_count = 0
        ignored_count = 0
        
        # Load ignore patterns
        ignore_patterns = []
        if ignore_file and os.path.exists(ignore_file):
            with open(ignore_file, 'r') as f:
                ignore_patterns = [
                    line.strip() for line in f 
                    if line.strip() and not line.startswith('#')
                ]
        
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, folder)
                
                # Check if file should be ignored
                is_ignored = any(
                    self._matches_pattern(relative_path, pattern) 
                    for pattern in ignore_patterns
                )
                
                if is_ignored:
                    ignored_count += 1
                else:
                    try:
                        total_size += os.path.getsize(file_path)
                        file_count += 1
                    except:
                        pass
        
        return {
            'file_count': file_count,
            'ignored_count': ignored_count,
            'total_size': total_size,
            'size_gb': total_size / (1024**3)
        }
    
    def upload_folder(self, local_folder: str, progress_callback=None, 
                     ignore_file: str = None) -> Tuple[bool, Dict]:
        """Upload folder to cloud with progress tracking."""
        folder_name = os.path.basename(local_folder)
        destination = f"{self.remote_name}:{self.archive_folder}/{folder_name}"
        
        try:
            cmd = [self.rclone_path, 'copy', local_folder, destination]
            
            if ignore_file and os.path.exists(ignore_file):
                cmd.extend(['--exclude-from', ignore_file])
                
            cmd.extend([
                '--transfers', '4',
                '--progress',
                '--stats', '2s',
                '--stats-one-line',
                '--log-level', 'INFO',
                '--verbose'
            ])
            
            if progress_callback:
                progress_callback(f"Executing: {' '.join(cmd)}")
                progress_callback(f"Moving from: {local_folder}")
                progress_callback(f"Moving to: {destination}")
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True, 
                bufsize=1
            )
            
            # Monitor progress
            while True:
                # Read both stdout and stderr
                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()
                
                if not stdout_line and not stderr_line and process.poll() is not None:
                    break
                    
                if stdout_line and progress_callback:
                    progress_callback(f"OUT: {stdout_line.strip()}")
                    
                if stderr_line and progress_callback:
                    progress_info = self._parse_progress(stderr_line)
                    if progress_info:
                        progress_callback(f"Moving files... {progress_info['percent']}%")
                    elif stderr_line.strip():
                        progress_callback(f"ERR: {stderr_line.strip()}")
            
            process.wait()
            
            if process.returncode != 0:
                # Get any remaining output
                remaining_stdout, remaining_stderr = process.communicate()
                error_msg = f"rclone failed with code {process.returncode}"
                if remaining_stderr:
                    error_msg += f": {remaining_stderr}"
                if progress_callback:
                    progress_callback(f"ERROR: {error_msg}")
                return False, {"error": error_msg}
                
            if progress_callback:
                progress_callback("✅ Move completed successfully!")
            return True, {"success": "Upload completed successfully"}
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def verify_upload(self, local_folder: str, cloud_destination: str = None) -> Tuple[bool, Dict]:
        """Verify files were uploaded correctly."""
        if not cloud_destination:
            folder_name = os.path.basename(local_folder)
            cloud_destination = f"{self.remote_name}:{self.archive_folder}/{folder_name}"
            
        try:
            # Get cloud file count and size
            result = subprocess.run(
                [self.rclone_path, 'size', cloud_destination, '--json'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                return False, {"error": "Failed to check cloud files"}
                
            data = json.loads(result.stdout)
            
            # Run integrity check
            check_cmd = [self.rclone_path, 'check', local_folder, cloud_destination, '--one-way']
            check_result = subprocess.run(check_cmd, capture_output=True, text=True)
            
            verification_passed = check_result.returncode == 0
            
            return verification_passed, {
                'cloud_count': data.get('count', 0),
                'cloud_size_gb': data.get('bytes', 0) / (1024**3),
                'verification_passed': verification_passed
            }
            
        except Exception as e:
            return False, {"error": str(e)}
    
    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Simple pattern matching for ignore files."""
        import fnmatch
        path_parts = path.replace('\\', '/').split('/')
        pattern_parts = pattern.replace('\\', '/').split('/')
        
        for part, pat in zip(path_parts, pattern_parts):
            if pat.startswith('**'):
                return True
            if not fnmatch.fnmatch(part, pat):
                return False
        return True
    
    def _parse_progress(self, line: str) -> Optional[Dict]:
        """Parse rclone progress output."""
        if 'Transferred:' in line and '%' in line:
            try:
                # Extract percentage
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
                
                return {
                    'percent': percent,
                    'speed': speed,
                    'eta': eta
                }
            except:
                pass
        return None
    
    def upload_multiple_folders(self, folders: List[str], progress_callback=None, 
                               ignore_file: str = None) -> Tuple[bool, Dict]:
        """Upload multiple folders to cloud storage."""
        total_folders = len(folders)
        upload_results = []
        
        try:
            for i, folder in enumerate(folders):
                folder_name = os.path.basename(folder)
                
                if progress_callback:
                    progress_callback(f"Uploading folder {i+1}/{total_folders}: {folder_name}")
                
                # Upload individual folder
                success, result = self.upload_folder(
                    folder, 
                    progress_callback=lambda msg, f=folder_name: progress_callback(f"{f}: {msg}") if progress_callback else None,
                    ignore_file=ignore_file
                )
                
                upload_results.append({
                    'folder': folder,
                    'success': success,
                    'result': result
                })
                
                if not success:
                    return False, {
                        'error': f"Failed to upload {folder_name}",
                        'results': upload_results
                    }
            
            return True, {
                'message': f"Successfully uploaded {total_folders} folders",
                'results': upload_results
            }
            
        except Exception as e:
            return False, {'error': str(e), 'results': upload_results}
    
    def verify_multiple_uploads(self, folders: List[str]) -> Tuple[bool, Dict]:
        """Verify multiple folder uploads."""
        verification_results = []
        
        for folder in folders:
            success, result = self.verify_upload(folder)
            verification_results.append({
                'folder': folder,
                'success': success,
                'result': result
            })
            
            if not success:
                return False, {
                    'error': f"Verification failed for {os.path.basename(folder)}",
                    'results': verification_results
                }
        
        return True, {
            'message': f"All {len(folders)} folders verified successfully",
            'results': verification_results
        }