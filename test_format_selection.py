#!/usr/bin/env python3
"""
Test script to verify format selection is working correctly.
This will show what formats are available and what our selector chooses.
"""

import yt_dlp
import os
from format_selector import get_format_selector

def test_format_selection(url, quality='best'):
    """Test format selection for a given URL and quality"""
    print(f"\n=== Testing format selection for: {url} ===")
    print(f"Quality: {quality}")
    
    # Check if FFmpeg is available
    ffmpeg_available = False
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        ffmpeg_available = result.returncode == 0
    except:
        pass
    
    print(f"FFmpeg available: {ffmpeg_available}")
    
    # Get format selector
    format_selector = get_format_selector(quality, ffmpeg_available)
    print(f"Format selector: {format_selector}")
    
    # Test what yt-dlp would select
    ydl_opts = {
        'format': format_selector,
        'simulate': True,  # Don't actually download
        'no_warnings': True,
        'quiet': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'requested_formats' in info:
                print("\n--- Selected SEPARATE formats (will be merged) ---")
                for i, fmt in enumerate(info['requested_formats']):
                    print(f"Stream {i+1}: {fmt.get('format_id', 'unknown')} - {fmt.get('ext', 'unknown')} - {fmt.get('resolution', 'unknown')} - {fmt.get('filesize_approx', 'unknown')} bytes")
                    print(f"  URL: {fmt.get('url', 'unknown')[:100]}...")
            elif 'format_id' in info:
                print("\n--- Selected SINGLE format ---")
                print(f"Format: {info.get('format_id', 'unknown')} - {info.get('ext', 'unknown')} - {info.get('resolution', 'unknown')} - {info.get('filesize_approx', 'unknown')} bytes")
            
            print(f"\nSelected format ID: {info.get('format_id', 'unknown')}")
            print(f"Extension: {info.get('ext', 'unknown')}")
            print(f"Resolution: {info.get('resolution', 'unknown')}")
            print(f"Filesize: {info.get('filesize_approx', 'unknown')} bytes")
            
    except Exception as e:
        print(f"Error: {e}")

def list_available_formats(url):
    """List all available formats for a URL"""
    print(f"\n=== Available formats for: {url} ===")
    
    ydl_opts = {
        'listformats': True,
        'quiet': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    # Test URL (replace with the URL you want to test)
    test_url = input("Enter YouTube URL to test: ").strip()
    
    if not test_url:
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Default test URL
    
    # List available formats
    list_available_formats(test_url)
    
    # Test our format selectors
    qualities = ['best', '1080p', '720p', '480p']
    
    for quality in qualities:
        test_format_selection(test_url, quality)
