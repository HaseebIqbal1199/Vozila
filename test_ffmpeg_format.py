#!/usr/bin/env python3
"""
Test format selection with FFmpeg available
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from format_selector import get_format_selector
import yt_dlp

def test_with_ffmpeg():
    """Test format selection with FFmpeg"""
    url = "https://www.youtube.com/watch?v=ULi6SmLifVg"
    
    # Test with FFmpeg available
    format_selector = get_format_selector('1080p', ffmpeg_available=True)
    print(f"Format selector with FFmpeg: {format_selector}")
    
    # Test yt-dlp with FFmpeg format
    ydl_opts = {
        'format': format_selector,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'merge_output_format': 'mp4',
        'postprocessors': [],
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            print(f"Title: {info.get('title', 'N/A')}")
            print(f"Duration: {info.get('duration', 'N/A')} seconds")
            
            # Check if we have separate formats that need merging
            requested_formats = info.get('requested_formats')
            if requested_formats:
                print("--- Selected MULTIPLE formats (video + audio) ---")
                for i, fmt in enumerate(requested_formats):
                    print(f"Format {i+1}: {fmt.get('format_id')} - {fmt.get('ext')} - {fmt.get('resolution', 'audio only')} - {fmt.get('filesize', 'unknown size')} bytes")
                    if fmt.get('vcodec') and fmt.get('vcodec') != 'none':
                        print(f"  Video codec: {fmt.get('vcodec')}")
                    if fmt.get('acodec') and fmt.get('acodec') != 'none':
                        print(f"  Audio codec: {fmt.get('acodec')}")
            else:
                print("--- Selected SINGLE format ---")
                print(f"Format: {info.get('format_id')} - {info.get('ext')} - {info.get('resolution', 'unknown')} - {info.get('filesize', 'unknown')} bytes")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_with_ffmpeg()
