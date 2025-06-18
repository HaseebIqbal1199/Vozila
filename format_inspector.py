#!/usr/bin/env python3
"""
YouTube Format Inspector
Debug script to analyze available formats for a YouTube video
"""

import yt_dlp
import sys

def inspect_video_formats(url):
    """Inspect available formats for a YouTube video"""
    print(f"🔍 Inspecting formats for: {url}")
    print("=" * 80)
    
    # Configuration for getting all available formats
    ydl_opts = {
        'listformats': True,
        'quiet': False,
        'no_warnings': False,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        },
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("\n📊 EXTRACTING VIDEO INFO...")
            info = ydl.extract_info(url, download=False)
            
            print(f"\n📽️ VIDEO DETAILS:")
            print(f"Title: {info.get('title', 'Unknown')}")
            print(f"Duration: {info.get('duration', 0)} seconds")
            print(f"Uploader: {info.get('uploader', 'Unknown')}")
            
            if 'formats' in info:
                print(f"\n📋 AVAILABLE FORMATS ({len(info['formats'])} total):")
                print("-" * 80)
                print(f"{'ID':<6} {'EXT':<5} {'RESOLUTION':<12} {'FPS':<4} {'SIZE':<10} {'CODEC':<15} {'NOTE'}")
                print("-" * 80)
                
                for fmt in info['formats']:
                    format_id = fmt.get('format_id', 'N/A')
                    ext = fmt.get('ext', 'N/A')
                    resolution = f"{fmt.get('width', '?')}x{fmt.get('height', '?')}" if fmt.get('width') else fmt.get('resolution', 'audio only')
                    fps = fmt.get('fps', 'N/A')
                    filesize = fmt.get('filesize')
                    if filesize:
                        filesize_mb = f"{filesize / (1024*1024):.1f}MB"
                    else:
                        filesize_mb = 'Unknown'
                    
                    vcodec = fmt.get('vcodec', 'N/A')
                    acodec = fmt.get('acodec', 'N/A')
                    codec = f"{vcodec[:7]}/{acodec[:7]}" if vcodec != 'N/A' else acodec[:15]
                    
                    note = fmt.get('format_note', '')
                    
                    print(f"{format_id:<6} {ext:<5} {resolution:<12} {str(fps):<4} {filesize_mb:<10} {codec:<15} {note}")
                
                print("\n🎯 TESTING DIFFERENT FORMAT SELECTORS:")
                print("-" * 80)
                
                # Test different format selectors
                test_selectors = [
                    'best',
                    'best[height<=1080]',
                    'best[height<=720]',
                    'best[height<=480]',
                    'bestvideo+bestaudio/best',
                    'best[ext=mp4]',
                    'best[height>=720]',
                ]
                
                for selector in test_selectors:
                    try:
                        test_opts = {
                            'format': selector,
                            'quiet': True,
                            'no_warnings': True,
                            'simulate': True,
                            'http_headers': ydl_opts['http_headers'],
                        }
                        
                        with yt_dlp.YoutubeDL(test_opts) as test_ydl:
                            test_info = test_ydl.extract_info(url, download=False)
                            selected_format = test_info.get('format_id', 'Unknown')
                            selected_ext = test_info.get('ext', 'Unknown')
                            selected_res = f"{test_info.get('width', '?')}x{test_info.get('height', '?')}" if test_info.get('width') else 'audio only'
                            
                            print(f"'{selector}' -> Format {selected_format} ({selected_ext}, {selected_res})")
                    
                    except Exception as e:
                        print(f"'{selector}' -> ERROR: {str(e)[:50]}...")
                
            else:
                print("\n❌ No formats found!")
                
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    # Use the same URL from the logs
    test_url = "https://www.youtube.com/watch?v=nh4Ql8nc3Gc"
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    inspect_video_formats(test_url)
