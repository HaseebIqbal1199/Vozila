#!/usr/bin/env python3
"""
Test script to demonstrate the improved progress tracking
"""

import requests
import time
import json

def test_progress_tracking():
    """Test the improved progress tracking with FFmpeg merging"""
    base_url = "http://localhost:3000"
    
    # Test URL - Rick Roll 4K video (has separate video/audio streams)
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("🧪 Testing Improved Progress Tracking")
    print("=" * 50)
    
    # Start download
    print(f"📥 Starting download: {test_url}")
    response = requests.post(f"{base_url}/api/download", json={
        "url": test_url,
        "quality": "1080p"  # This will trigger FFmpeg merging
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to start download: {response.text}")
        return
    
    data = response.json()
    download_id = data["download_id"]
    print(f"✅ Download started with ID: {download_id}")
    print()
    
    # Track progress
    print("📊 Progress Tracking:")
    print("-" * 30)
    
    last_status = ""
    while True:
        try:
            progress_response = requests.get(f"{base_url}/api/progress/{download_id}")
            if progress_response.status_code != 200:
                print(f"❌ Failed to get progress: {progress_response.text}")
                break
                
            progress_data = progress_response.json()
            
            # Only print when status changes or every 10%
            current_status = f"{progress_data['status']}_{progress_data['progress']//10*10}"
            if current_status != last_status:
                status_icon = {
                    'starting': '🔄',
                    'downloading': '⬇️',
                    'merging': '🔧',
                    'completed': '✅',
                    'error': '❌'
                }.get(progress_data['status'], '📄')
                
                status_msg = progress_data.get('status_message', progress_data['status'])
                print(f"{status_icon} {progress_data['progress']:3d}% | {status_msg}")
                
                if progress_data.get('is_merging'):
                    print("   🎬 FFmpeg is merging video and audio streams...")
                
                last_status = current_status
            
            if progress_data['status'] in ['completed', 'error']:
                break
                
            time.sleep(1)
            
        except requests.RequestException as e:
            print(f"❌ Network error: {e}")
            break
        except KeyboardInterrupt:
            print("\n⏸️ Interrupted by user")
            break
    
    print()
    if progress_data['status'] == 'completed':
        print("🎉 Download completed successfully!")
        print(f"📁 Video title: {progress_data.get('title', 'Unknown')}")
        print(f"🔗 Download link: {base_url}/api/download/{download_id}")
    else:
        print("❌ Download failed or was interrupted")
        if progress_data.get('error'):
            print(f"   Error: {progress_data['error']}")

if __name__ == "__main__":
    test_progress_tracking()
