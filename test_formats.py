#!/usr/bin/env python3
"""
Quick test script to verify format selection is working correctly
"""

import yt_dlp
import tempfile
import os

def test_format_selection():
    """Test different quality selections"""
    test_url = "https://www.youtube.com/watch?v=nh4Ql8nc3Gc"
    
    # Test different quality settings
    qualities = ['best', '1080p', '720p', '480p', '360p']
    
    for quality in qualities:
        print(f"\n🎯 Testing quality: {quality}")
        print("-" * 50)
        
        # Simulate the same logic as in source.py
        ffmpeg_available = True  # Assume FFmpeg is available
        
        if quality == '360p':
            if ffmpeg_available:
                format_selector = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
            else:
                format_selector = 'best[height<=360]/best'
        elif quality == '480p':
            if ffmpeg_available:
                format_selector = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            else:
                format_selector = 'best[height<=480]/best'
        elif quality == '720p':
            if ffmpeg_available:
                format_selector = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            else:
                format_selector = 'best[height<=720]/best'
        elif quality == '1080p':
            if ffmpeg_available:
                format_selector = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            else:
                format_selector = 'best[height<=1080]/best'
        else:  # 'best'
            if ffmpeg_available:
                format_selector = 'bestvideo+bestaudio/best'
            else:
                format_selector = 'best'
        
        print(f"Format selector: {format_selector}")
        
        # Test what format would be selected
        ydl_opts = {
            'format': format_selector,
            'quiet': True,
            'no_warnings': True,
            'simulate': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            },
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                
                selected_format = info.get('format_id', 'Unknown')
                selected_ext = info.get('ext', 'Unknown')
                width = info.get('width', '?')
                height = info.get('height', '?')
                filesize = info.get('filesize')
                
                if filesize:
                    filesize_mb = f"{filesize / (1024*1024):.1f}MB"
                else:
                    filesize_mb = 'Unknown'
                
                print(f"✅ Selected: Format {selected_format} ({selected_ext})")
                print(f"   Resolution: {width}x{height}")
                print(f"   File size: {filesize_mb}")
                
                # Check if it's using separate streams (high quality) or combined (lower quality)
                if '+' in selected_format:
                    print(f"   📊 Using separate video+audio streams (HIGH QUALITY)")
                elif selected_format == '18':
                    print(f"   ⚠️ Using combined stream (MEDIUM QUALITY)")
                else:
                    print(f"   ℹ️ Using single stream")
                
        except Exception as e:
            print(f"❌ Error: {str(e)[:60]}...")

if __name__ == "__main__":
    test_format_selection()
