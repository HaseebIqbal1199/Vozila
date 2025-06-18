#!/usr/bin/env python3
"""
Debug script to check available video qualities for a YouTube URL
Run this to see what qualities are actually available for download
"""

import yt_dlp
import sys

def check_video_quality(url):
    """Check available qualities for a YouTube video"""
    print(f"Checking available formats for: {url}")
    print("="*60)
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'listformats': False,  # We'll process formats manually
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            print(f"Title: {info.get('title', 'Unknown')}")
            print(f"Duration: {info.get('duration', 'Unknown')} seconds")
            print(f"Uploader: {info.get('uploader', 'Unknown')}")
            print("-"*60)
            
            if 'formats' in info:
                print("Available Video Qualities:")
                video_formats = []
                audio_formats = []
                
                for fmt in info['formats']:
                    if fmt.get('vcodec') != 'none' and fmt.get('height'):
                        # Video format
                        filesize = fmt.get('filesize')
                        filesize_str = f"{filesize / (1024*1024):.1f}MB" if filesize else "Unknown size"
                        
                        video_formats.append({
                            'height': fmt['height'],
                            'format_id': fmt['format_id'],
                            'ext': fmt.get('ext', 'unknown'),
                            'filesize': filesize_str,
                            'fps': fmt.get('fps', 'Unknown'),
                            'vcodec': fmt.get('vcodec', 'Unknown'),
                            'acodec': fmt.get('acodec', 'none')
                        })
                    elif fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                        # Audio-only format
                        audio_formats.append({
                            'format_id': fmt['format_id'],
                            'ext': fmt.get('ext', 'unknown'),
                            'abr': fmt.get('abr', 'Unknown'),
                            'acodec': fmt.get('acodec', 'Unknown')
                        })
                
                # Sort video formats by height (quality)
                video_formats.sort(key=lambda x: x['height'], reverse=True)
                
                print("\n📹 VIDEO FORMATS:")
                for fmt in video_formats:
                    print(f"  {fmt['height']}p | ID: {fmt['format_id']} | "
                          f"Format: {fmt['ext']} | Size: {fmt['filesize']} | "
                          f"FPS: {fmt['fps']} | Codec: {fmt['vcodec']}")
                
                print("\n🎵 AUDIO-ONLY FORMATS:")
                for fmt in audio_formats[:5]:  # Show top 5 audio formats
                    print(f"  Quality: {fmt['abr']}kbps | ID: {fmt['format_id']} | "
                          f"Format: {fmt['ext']} | Codec: {fmt['acodec']}")                # Show what our app would select for each quality
                print("\n🎯 WHAT OUR APP WOULD SELECT (VERCEL-COMPATIBLE):")
                quality_tests = ['2160p', '1440p', '1080p', '720p', '480p', '360p']
                
                for quality in quality_tests:
                    # Use the new Vercel-compatible format selection logic from source.py
                    if quality == '2160p':
                        format_selector = 'best/bestvideo+bestaudio'
                    elif quality == '1440p':
                        format_selector = 'best[height>=1440][height<=2160]/best[height>=1440]/bestvideo[height>=1440][height<=2160]+bestaudio/best[height>=1440]'
                    elif quality == '1080p':
                        format_selector = 'best[height>=1080][height<=1440]/best[height>=1080]/bestvideo[height>=1080][height<=1440]+bestaudio/best[height>=1080]'
                    elif quality == '720p':
                        format_selector = 'best[height>=720][height<=1080]/best[height>=720]/bestvideo[height>=720][height<=1080]+bestaudio/best[height>=720]'
                    elif quality == '480p':
                        format_selector = 'best[height>=480][height<=720]/best[height>=480]/bestvideo[height>=480][height<=720]+bestaudio/best[height>=480]'
                    elif quality == '360p':
                        format_selector = 'best[height>=360][height<=480]/best[height>=360]/bestvideo[height>=360][height<=480]+bestaudio/best[height>=360]'
                    
                    try:
                        test_opts = {**ydl_opts, 'format': format_selector, 'quiet': True, 'abort_on_error': False}
                        with yt_dlp.YoutubeDL(test_opts) as test_ydl:
                            test_info = test_ydl.extract_info(url, download=False)
                            selected_format = test_info.get('format_id', 'Unknown')
                            selected_height = test_info.get('height', 'Unknown')
                            selected_ext = test_info.get('ext', 'unknown')
                            filesize = test_info.get('filesize')
                            filesize_str = f" ({filesize / (1024*1024):.1f}MB)" if filesize else ""
                            print(f"  {quality} request → Would download: {selected_height}p ({selected_ext}) | Format: {selected_format}{filesize_str}")
                    except Exception as e:
                        print(f"  {quality} request → Error: {e}")
                        
            else:
                print("❌ No formats found!")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_quality.py <YouTube_URL>")
        print("Example: python debug_quality.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'")
    else:
        url = sys.argv[1]
        check_video_quality(url)
