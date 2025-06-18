#!/usr/bin/env python3
"""Test script to verify the YouTube downloader works correctly"""

import requests
import json
import time

def test_download():
    """Test downloading a video"""
    # Use a reliable test video URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
    
    print("🧪 Testing YouTube downloader...")
    print(f"📹 Test URL: {test_url}")
    
    # Start download
    response = requests.post('http://localhost:3000/download', json={
        'url': test_url,
        'quality': '720p'
    })
    
    if response.status_code != 200:
        print(f"❌ Download request failed: {response.status_code}")
        print(response.text)
        return False
    
    data = response.json()
    if data['status'] != 'success':
        print(f"❌ Download failed: {data.get('message', 'Unknown error')}")
        return False
    
    download_id = data['download_id']
    print(f"✅ Download started. ID: {download_id}")
    
    # Monitor progress
    print("📊 Monitoring progress...")
    while True:
        progress_response = requests.get(f'http://localhost:3000/progress/{download_id}')
        if progress_response.status_code != 200:
            print(f"❌ Progress check failed: {progress_response.status_code}")
            break
            
        progress_data = progress_response.json()
        status = progress_data.get('status', 'unknown')
        progress = progress_data.get('progress', 0)
        
        print(f"   Status: {status}, Progress: {progress}%")
        
        if status == 'completed':
            print("✅ Download completed successfully!")
            break
        elif status == 'error':
            print(f"❌ Download failed: {progress_data.get('error', 'Unknown error')}")
            break
        elif status == 'not_found':
            print("❌ Download not found")
            break
        
        time.sleep(2)
    
    return True

if __name__ == '__main__':
    try:
        test_download()
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
