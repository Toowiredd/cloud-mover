#!/usr/bin/env python3
"""
Quick test to check if rclone is working
"""

import subprocess
import os

def test_rclone():
    rclone_path = "rclone.exe"
    
    print("=== Testing rclone setup ===")
    
    # Check if rclone exists
    if not os.path.exists(rclone_path):
        print(f"❌ rclone.exe not found at {rclone_path}")
        return False
    
    print(f"✅ rclone.exe found at {rclone_path}")
    
    # Check version
    try:
        result = subprocess.run([rclone_path, 'version'], capture_output=True, text=True, timeout=10)
        print(f"✅ rclone version: {result.stdout.split('rclone')[1].split()[0] if 'rclone' in result.stdout else 'unknown'}")
    except Exception as e:
        print(f"❌ Error getting rclone version: {e}")
        return False
    
    # List remotes
    try:
        result = subprocess.run([rclone_path, 'listremotes'], capture_output=True, text=True, timeout=10)
        print(f"📋 Available remotes: {result.stdout.strip()}")
        
        if 'gdrive:' not in result.stdout:
            print("❌ 'gdrive' remote not configured")
            print("Run: rclone config")
            return False
        else:
            print("✅ 'gdrive' remote found")
            
    except Exception as e:
        print(f"❌ Error listing remotes: {e}")
        return False
    
    # Test connection
    try:
        print("🔍 Testing Google Drive connection...")
        result = subprocess.run([rclone_path, 'lsf', 'gdrive:', '--max-depth', '1'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✅ Google Drive connection successful")
            print(f"📁 Found {len(result.stdout.strip().split()) if result.stdout.strip() else 0} items in root")
            return True
        else:
            print(f"❌ Google Drive connection failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False

if __name__ == "__main__":
    success = test_rclone()
    if success:
        print("\n🎉 rclone setup is working!")
    else:
        print("\n❌ rclone setup has issues - fix these before running the app")
    
    input("\nPress Enter to exit...")