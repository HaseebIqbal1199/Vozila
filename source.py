from flask import Flask, render_template, request, jsonify, send_file, abort
from flask_caching import Cache
import yt_dlp
import os
import re
import json
import tempfile
import threading
import time
from urllib.parse import urlparse, parse_qs
import zipfile
from datetime import datetime, timedelta
import hashlib
import uuid
from dotenv import load_dotenv
import subprocess
import sys
import shutil
from format_selector import get_format_selector

# Load environment variables
load_dotenv()

# FFmpeg handling functions
def find_ffmpeg():
    """Find FFmpeg executable in common locations"""
    # Check if running on Linux/Unix (Render uses Ubuntu)
    if os.name == 'posix':
        # Linux/Unix paths (Render uses Ubuntu)
        possible_paths = [
            'ffmpeg',  # Should be in PATH on Render
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/render/project/src/ffmpeg',  # Custom Render path if needed
            '/app/vendor/ffmpeg/ffmpeg'  # Common Docker/container path
        ]
    else:
        # Windows paths
        possible_paths = [
            r'C:\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files\ffmpeg\bin\ffmpeg.exe',
            r'C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe',
            'ffmpeg.exe',  # If it's in PATH
            'ffmpeg'       # Fallback
        ]
    
    for path in possible_paths:
        try:
            result = subprocess.run([path, '-version'], 
                                  stdout=subprocess.PIPE, 
                                  stderr=subprocess.PIPE, 
                                  timeout=5)
            if result.returncode == 0:
                print(f"Found FFmpeg at: {path}")
                return path
        except Exception as e:
            print(f"Failed to check FFmpeg at {path}: {e}")
            continue
    
    print("FFmpeg not found in any common locations")
    return None

def check_ffmpeg():
    """Check if FFmpeg is available"""
    return find_ffmpeg() is not None

def install_ffmpeg_windows():
    """Install FFmpeg on Windows using winget or chocolatey"""
    try:
        # Try winget first
        result = subprocess.run(['winget', 'install', 'ffmpeg', '--accept-source-agreements'], 
                              capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            return True
        # Try chocolatey as fallback
        subprocess.run(['choco', 'install', 'ffmpeg', '-y'], timeout=300)
        return check_ffmpeg()
    except:
        return False

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Caching only (rate limiting removed for open access)
cache = Cache(app, config={'CACHE_TYPE': 'simple'})

# Global variables for download tracking
download_progress = {}
download_files = {}

# Cookie storage for manual uploads
uploaded_cookies = {}

def save_cookies_to_file(cookies_content, download_id):
    """Save uploaded cookies to a temporary file"""
    try:
        # Create cookies directory if it doesn't exist
        cookies_dir = os.path.join(tempfile.gettempdir(), 'youtube_downloader_cookies')
        os.makedirs(cookies_dir, exist_ok=True)
        
        # Save cookies to a file
        cookie_file = os.path.join(cookies_dir, f'cookies_{download_id}.txt')
        
        # Handle different cookie formats
        if cookies_content.strip().startswith('{'):
            # JSON format - convert to Netscape format
            try:
                import json
                cookie_data = json.loads(cookies_content)
                netscape_content = "# Netscape HTTP Cookie File\n"
                for cookie in cookie_data:
                    domain = cookie.get('domain', '.youtube.com')
                    flag = 'TRUE' if domain.startswith('.') else 'FALSE'
                    path = cookie.get('path', '/')
                    secure = 'TRUE' if cookie.get('secure', False) else 'FALSE'
                    expiration = cookie.get('expirationDate', 0)
                    name = cookie.get('name', '')
                    value = cookie.get('value', '')
                    netscape_content += f"{domain}\t{flag}\t{path}\t{secure}\t{int(expiration)}\t{name}\t{value}\n"
                
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    f.write(netscape_content)
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as plain text
                with open(cookie_file, 'w', encoding='utf-8') as f:
                    f.write(cookies_content)
        else:
            # Assume Netscape format
            with open(cookie_file, 'w', encoding='utf-8') as f:
                f.write(cookies_content)
        
        return cookie_file
    except Exception as e:
        print(f"Error saving cookies: {e}")
        return None

def cleanup_cookie_file(cookie_file):
    """Clean up temporary cookie file"""
    try:
        if cookie_file and os.path.exists(cookie_file):
            os.remove(cookie_file)
    except Exception as e:
        print(f"Error cleaning up cookie file: {e}")

class DownloadProgress:
    def __init__(self, download_id):
        self.download_id = download_id
        self.progress = 0
        self.status = 'starting'
        self.title = ''
        self.error = None
        self.is_merging = False
        self.merge_progress = 0
        self.start_time = time.time()
        
    def hook(self, d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d:
                # When merging, only show 80% during download phase
                max_progress = 80 if self.will_need_merging() else 100
                self.progress = int((d['downloaded_bytes'] / d['total_bytes']) * max_progress / 100)
            elif 'total_bytes_estimate' in d:
                max_progress = 80 if self.will_need_merging() else 100
                self.progress = int((d['downloaded_bytes'] / d['total_bytes_estimate']) * max_progress / 100)
            self.status = 'downloading'
        elif d['status'] == 'finished':
            if self.will_need_merging():
                self.progress = 80
                self.status = 'merging'
                self.is_merging = True
            else:
                self.progress = 100
                self.status = 'completed'
            self.title = d.get('info_dict', {}).get('title', 'Downloaded')
    
    def will_need_merging(self):
        """Check if this download will need FFmpeg merging"""
        # This will be set by the download function
        return getattr(self, '_needs_merging', False)
    
    def set_merging_needed(self, needs_merging):
        """Set whether this download needs merging"""
        self._needs_merging = needs_merging
    
    def update_merge_progress(self, progress):
        """Update merging progress (0-100)"""
        if self.is_merging:
            # Map merge progress from 80% to 100%
            self.progress = 80 + int(progress * 0.2)
            if progress >= 100:
                self.progress = 100
                self.status = 'completed'
                self.is_merging = False

def is_valid_youtube_url(url):
    """Validate YouTube URL"""
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    playlist_regex = re.compile(
        r'(https?://)?(www\.)?youtube\.com/playlist\?list=([a-zA-Z0-9_-]+)')
    return youtube_regex.match(url) or playlist_regex.match(url)

def get_video_info(url):
    """Get video information without downloading - with multiple fallback strategies"""
    
    # List of client strategies to try in order
    client_strategies = [
        # Strategy 1: tv_embedded (most reliable for bypassing restrictions)
        {
            'name': 'tv_embedded',
            'player_client': 'tv_embedded',
            'player_skip': 'webpage',
        },
        # Strategy 2: web_embedded (good for public videos)
        {
            'name': 'web_embedded', 
            'player_client': 'web_embedded',
            'player_skip': 'webpage',
        },
        # Strategy 3: mweb (mobile web, good fallback)
        {
            'name': 'mweb',
            'player_client': 'mweb',
            'player_skip': 'configs',
        },
        # Strategy 4: android (last resort)
        {
            'name': 'android',
            'player_client': 'android',
            'player_skip': 'webpage',
        }
    ]
    
    # User agents to rotate
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
    
    import random
    
    # Try each client strategy
    for i, strategy in enumerate(client_strategies):
        try:
            print(f"Trying strategy {i+1}: {strategy['name']}")
            
            selected_ua = random.choice(user_agents)
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'force_json': True,
                # Use current strategy
                'extractor_args': {
                    'youtube': {
                        'player_client': strategy['player_client'],
                        'player_skip': strategy['player_skip'],
                        # Additional bypass options
                        'skip': ['dash', 'hls'] if i < 2 else [],  # Skip for first two strategies
                        'innertube_host': 'studio.youtube.com' if i == 0 else None,
                        'comment_sort': ['top']
                    }
                },
                # Enhanced headers
                'http_headers': {
                    'User-Agent': selected_ua,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                    'Referer': 'https://www.youtube.com/',
                    'Origin': 'https://www.youtube.com'
                },
                # Bypass restrictions
                'age_limit': None,
                'geo_bypass': True,
                'geo_bypass_country': 'US',
                # Rate limiting (increase delay for each retry)
                'sleep_interval': 2 + i,
                'max_sleep_interval': 5 + i * 2,
                # Retry settings
                'retries': 2,
                'fragment_retries': 2,
                # Skip unavailable fragments
                'skip_unavailable_fragments': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                print(f"Success with strategy: {strategy['name']}")
                return info
                
        except Exception as e:
            print(f"Strategy {strategy['name']} failed: {str(e)[:100]}...")
            # Continue to next strategy
            continue
    
    # If all strategies failed, raise the last error
    raise Exception("All extraction strategies failed. Video may be unavailable, private, or region-blocked.")

def get_video_info_old(url):
    """Get video information without downloading"""
    try:
        # Rotate user agents to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
        ]
        import random
        selected_ua = random.choice(user_agents)
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'force_json': True,
            # Use alternative YouTube clients that don't require PO tokens
            'extractor_args': {
                'youtube': {
                    # Use tv_embedded client as primary (doesn't require PO tokens)
                    'player_client': 'tv_embedded,web_embedded,mweb',
                    # Skip webpage requests to avoid cookie rotation
                    'player_skip': 'webpage',
                    # Additional bypass options
                    'skip': ['dash', 'hls'],
                    'innertube_host': 'studio.youtube.com',
                    'comment_sort': ['top']
                }
            },
            # Enhanced headers to mimic real browser
            'http_headers': {
                'User-Agent': selected_ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.youtube.com/',
                'Origin': 'https://www.youtube.com'
            },
            # Cookie handling
            'cookiefile': None,
            # Bypass restrictions
            'age_limit': None,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            # Rate limiting to avoid triggering bot protection
            'sleep_interval': 2,
            'max_sleep_interval': 5,
            # Retry settings
            'retries': 3,
            'fragment_retries': 3,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        print(f"Error getting video info: {e}")
        return None

def download_video(url, quality, download_id, output_path):
    """Download video in background thread"""
    try:
        progress_tracker = DownloadProgress(download_id)
        download_progress[download_id] = progress_tracker        # Find FFmpeg path  
        ffmpeg_path = find_ffmpeg()
        
        # Get format selector using the helper function
        format_selector = get_format_selector(quality, bool(ffmpeg_path))
              # Detect if this format selection will need merging
        needs_merging = ffmpeg_path and ('+' in format_selector)
        progress_tracker.set_merging_needed(needs_merging)
        
        # Enhanced progress hook for FFmpeg merging
        def enhanced_progress_hook(d):
            progress_tracker.hook(d)
            if d['status'] == 'finished' and needs_merging:
                # Start simulating merge progress
                def simulate_merge_progress():
                    import time
                    for i in range(0, 101, 5):
                        if progress_tracker.status == 'completed':
                            break
                        progress_tracker.update_merge_progress(i)
                        time.sleep(0.1)  # Faster merge simulation
                  # Run merge simulation in background
                import threading
                merge_thread = threading.Thread(target=simulate_merge_progress)
                merge_thread.daemon = True
                merge_thread.start()
          # Enhanced user agent rotation for downloads
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        import random
        selected_ua = random.choice(user_agents)
        
        ydl_opts = {
            'format': format_selector,
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [enhanced_progress_hook],
            'extractaudio': quality == 'audio',
            'audioformat': 'mp3' if quality == 'audio' else None,
            # Ensure we get the best quality possible
            'writeinfojson': False,
            'writeautomaticsub': False,
            'writesubtitles': False,
            'keepvideo': False,  # Don't keep original video files after merging
            # FFmpeg configuration
            'ffmpeg_location': ffmpeg_path if ffmpeg_path else None,            # Enhanced headers to mimic real browser
            'http_headers': {
                'User-Agent': selected_ua,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0',
                'Referer': 'https://www.youtube.com/',
                'Origin': 'https://www.youtube.com'
            },
            # Use alternative YouTube clients that don't require PO tokens
            'extractor_args': {
                'youtube': {
                    # Use tv_embedded client as primary (doesn't require PO tokens)
                    'player_client': 'tv_embedded,web_embedded,mweb',
                    # Skip webpage requests to avoid cookie rotation
                    'player_skip': 'webpage',
                    # Additional bypass options
                    'skip': ['dash', 'hls'],
                    'innertube_host': 'studio.youtube.com',
                    'comment_sort': ['top']
                }
            },
            # Cookie handling - Use manual cookies if available
            'cookiefile': uploaded_cookies.get(download_id),            # Enhanced retry and delay settings
            'retries': 5,
            'fragment_retries': 5,
            'sleep_interval': 3,
            'max_sleep_interval': 8,
            # Additional bypass options
            'no_warnings': True,
            'ignoreerrors': False,# Bypass geo-restrictions
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            
            # Output format settings for merging
            'merge_output_format': 'mp4',
            'prefer_free_formats': False,  # Don't prefer free formats - we want highest quality            # Post-processors - minimal setup for reliability
            'postprocessors': [] if not ffmpeg_path else [],
            
            # Ensure proper audio codec selection during merging
            'postprocessor_args': {
                'ffmpeg': [
                    '-c:v', 'copy',  # Copy video stream (no re-encoding)
                    '-c:a', 'aac',   # Convert audio to AAC
                    '-b:a', '192k',  # Audio bitrate 192k
                    '-movflags', '+faststart'  # Optimize for streaming
                ] if ffmpeg_path else []
            },
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Store file information
            if 'entries' in info:  # Playlist
                files = []
                for entry in info['entries']:
                    if entry:
                        filename = ydl.prepare_filename(entry)
                        if os.path.exists(filename):
                            files.append(filename)
                download_files[download_id] = files
            else:  # Single video
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    download_files[download_id] = [filename]
                    
    except Exception as e:
        error_message = str(e)
        print(f"Download error: {e}")
        download_progress[download_id].status = 'error'
        
        # Provide helpful error messages
        if 'not available' in error_message.lower() and 'format' in error_message.lower():
            download_progress[download_id].error = "Requested quality not available. Try selecting 'Best Available Quality' or a lower quality."
        elif '403' in error_message or 'forbidden' in error_message.lower():
            download_progress[download_id].error = "Video access restricted. Try uploading YouTube cookies for age-restricted content."
        elif 'private' in error_message.lower():
            download_progress[download_id].error = "This video is private. You may need to upload YouTube cookies to access it."
        elif 'not available' in error_message.lower():
            download_progress[download_id].error = "Video not available. This may be due to geographic restrictions."
        else:
            download_progress[download_id].error = f"Download failed: {error_message}"
        
        # Clean up cookie file if it exists
        if download_id in uploaded_cookies:
            cleanup_cookie_file(uploaded_cookies[download_id])
            del uploaded_cookies[download_id]

# Alternative download function for problematic videos
def download_video_alternative(url, quality, download_id, output_path):
    """Alternative download method with different extractor strategies"""
    try:
        progress_tracker = DownloadProgress(download_id)
        download_progress[download_id] = progress_tracker        # Quality mapping - OPTIMIZED for highest quality downloads
        # Using best format selection with proper fallbacks
        if quality == 'audio':
            format_selector = 'bestaudio[ext=m4a]/bestaudio/best[vcodec=none]'
        elif quality == '144p':
            format_selector = 'bestvideo[height<=144]+bestaudio/best[height<=144]'
        elif quality == '360p':
            format_selector = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
        elif quality == '480p':
            format_selector = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
        elif quality == '720p':
            format_selector = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif quality == '1080p':
            format_selector = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        else:  # 'best' or any other value
            # This will get the best available quality, including 4K/2160p
            format_selector = 'bestvideo+bestaudio/best'
          # Enhanced fallback strategies - specifically designed to bypass 403 errors
        strategies = [
            # Strategy 1: Use web client with 403-resistant settings
            {
                'format': format_selector,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web'],
                        'player_skip': ['configs'],
                        'include_hls_manifest': False,  # Disable HLS to avoid 403
                    }
                },
                'http_headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'},
                'youtube_include_hls_manifest': False,
                'merge_output_format': 'mp4',
                'prefer_free_formats': False,
            },
            # Strategy 2: Use android client (often bypasses 403 restrictions)
            {
                'format': format_selector,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['android'],
                        'include_hls_manifest': False,
                    }
                },
                'http_headers': {'User-Agent': 'com.google.android.youtube/17.31.35 (Linux; U; Android 11) gzip'},
                'youtube_include_hls_manifest': False,
                'merge_output_format': 'mp4',
            },
            # Strategy 3: Use TV client for maximum compatibility
            {
                'format': format_selector.replace('bestvideo+bestaudio', 'best'),  # TV client prefers single files
                'extractor_args': {
                    'youtube': {
                        'player_client': ['tv'],
                        'include_hls_manifest': False,
                    }
                },
                'youtube_include_hls_manifest': False,
                'merge_output_format': 'mp4',
            },
            # Strategy 4: Use lower quality single-file format as last resort
            {
                'format': 'best[height<=720]/best',  # Lower quality but more reliable
                'extractor_args': {
                    'youtube': {
                        'player_client': ['web'],
                        'include_hls_manifest': False,
                    }
                },
                'youtube_include_hls_manifest': False,
                'merge_output_format': 'mp4',
            }
        ]
        
        for i, strategy in enumerate(strategies):
            try:
                ydl_opts = {
                    **strategy,
                    'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                    'progress_hooks': [progress_tracker.hook],
                    'extractaudio': quality == 'audio',
                    'audioformat': 'mp3' if quality == 'audio' else None,
                    'retries': 2,
                    'ignoreerrors': False,
                    'no_warnings': True,
                    'geo_bypass': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                      # Store file information
                    if 'entries' in info:
                        files = []
                        for entry in info['entries']:
                            if entry:
                                filename = ydl.prepare_filename(entry)
                                if os.path.exists(filename):
                                    files.append(filename)
                        download_files[download_id] = files
                    else:
                        filename = ydl.prepare_filename(info)
                        if os.path.exists(filename):
                            download_files[download_id] = [filename]
                    return  # Success!
                
            except Exception as e:
                error_message = str(e).lower()
                
                # Provide specific feedback for 403 errors
                if '403' in error_message or 'forbidden' in error_message:
                    progress_tracker.status = 'downloading'
                    progress_tracker.error = f"Strategy {i+1}: Access restricted, trying alternative method..."
                    print(f"Strategy {i+1} failed with 403 error: {e}")
                    print(f"Trying strategy {i+2} of {len(strategies)}...")
                else:
                    print(f"Strategy {i+1} failed: {e}")
                
                if i == len(strategies) - 1:  # Last strategy
                    # Provide user-friendly error messages
                    if '403' in error_message or 'forbidden' in error_message:
                        final_error = "This video is restricted and cannot be downloaded. This may be due to geographic restrictions, age restrictions, or copyright protection."
                    else:
                        final_error = f"Download failed: {str(e)}"
                    raise Exception(final_error)
                continue
                
    except Exception as e:
        error_message = str(e)
        print(f"All download strategies failed: {e}")
        download_progress[download_id].status = 'error'
        
        # Provide helpful error messages to users
        if '403' in error_message.lower() or 'forbidden' in error_message.lower():
            download_progress[download_id].error = "Video access restricted. This video may be geographically blocked, age-restricted, or have enhanced copyright protection."
        elif 'private' in error_message.lower():
            download_progress[download_id].error = "This video is private and cannot be downloaded."
        elif 'not available' in error_message.lower():
            download_progress[download_id].error = "This video is not available for download."
        else:
            download_progress[download_id].error = f"Download failed: {error_message}"

def debug_available_formats(url):
    """Debug function to show available formats for a video"""
    try:
        ydl_opts = {
            'listformats': True,
            'quiet': False,
            'no_warnings': False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if 'formats' in info:
                print("Available formats:")
                for fmt in info['formats']:
                    if fmt.get('height'):
                        print(f"Format ID: {fmt['format_id']}, Quality: {fmt.get('height')}p, "
                              f"Ext: {fmt.get('ext')}, Size: {fmt.get('filesize', 'Unknown')}")
            return info.get('formats', [])
    except Exception as e:
        print(f"Debug error: {e}")
        return []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_info():
    """Get video/playlist information"""
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    # Check cache first
    url_hash = hashlib.md5(url.encode()).hexdigest()
    cached_info = cache.get(f'info_{url_hash}')
    if cached_info:
        return jsonify(cached_info)
    
    info = get_video_info(url)
    if not info:
        return jsonify({'error': 'Failed to get video information'}), 400
    
    result = {
        'title': info.get('title', 'Unknown'),
        'duration': info.get('duration', 0),
        'view_count': info.get('view_count', 0),
        'uploader': info.get('uploader', 'Unknown'),
        'thumbnail': info.get('thumbnail', ''),
        'is_playlist': 'entries' in info,
        'entry_count': len(info.get('entries', [])) if 'entries' in info else 1
    }
    
    # Cache for 1 hour
    cache.set(f'info_{url_hash}', result, timeout=3600)
    
    return jsonify(result)

@app.route('/api/download', methods=['POST'])
def start_download():
    """Start download process"""
    data = request.get_json()
    url = data.get('url', '').strip()
    quality = data.get('quality', 'best')
    cookies_content = data.get('cookies', '').strip()
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    if not is_valid_youtube_url(url):
        return jsonify({'error': 'Invalid YouTube URL'}), 400
    
    # Generate unique download ID
    download_id = str(uuid.uuid4())
    
    # Handle cookies if provided
    if cookies_content:
        cookie_file = save_cookies_to_file(cookies_content, download_id)
        if cookie_file:
            uploaded_cookies[download_id] = cookie_file
      # Create temporary directory for this download
    temp_dir = tempfile.mkdtemp(prefix=f'yt_download_{download_id}_')
    
    # Start download in background thread with robust fallback
    def download_with_robust_fallback():
        try:
            # First try the new robust fallback method
            cookies_file = uploaded_cookies.get(download_id)
            download_video_with_fallback(url, quality, download_id, temp_dir, cookies_file)
        except Exception as e:
            print(f"All fallback methods failed: {e}")
            if download_id in download_progress:
                download_progress[download_id].status = 'error'
                download_progress[download_id].error = f"Download failed: {str(e)}"
    
    thread = threading.Thread(target=download_with_robust_fallback)
    thread.daemon = True
    thread.start()
    
    return jsonify({'download_id': download_id})

@app.route('/api/progress/<download_id>')
def get_progress(download_id):
    """Get download progress"""
    if download_id not in download_progress:
        return jsonify({'error': 'Download not found'}), 404
    
    progress = download_progress[download_id]
    
    # Enhanced status messages
    status_messages = {
        'starting': 'Preparing download...',
        'downloading': 'Downloading video...' if not progress.is_merging else 'Downloaded, preparing to merge...',
        'merging': 'Merging video and audio streams...',
        'completed': 'Download completed!',
        'error': 'Download failed'
    }
    
    return jsonify({
        'progress': progress.progress,
        'status': progress.status,
        'status_message': status_messages.get(progress.status, progress.status),
        'title': progress.title,
        'error': progress.error,
        'is_merging': progress.is_merging
    })

@app.route('/api/download/<download_id>')
def download_file(download_id):
    """Download completed files"""
    if download_id not in download_files:
        return jsonify({'error': 'Download not found or not completed'}), 404
    
    files = download_files[download_id]
    
    if len(files) == 1:
        # Single file download
        if os.path.exists(files[0]):
            return send_file(files[0], as_attachment=True)
    else:
        # Multiple files - create zip
        zip_path = tempfile.mktemp(suffix='.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for file_path in files:
                if os.path.exists(file_path):
                    zipf.write(file_path, os.path.basename(file_path))
        return send_file(zip_path, as_attachment=True, download_name='playlist.zip')
    
    return jsonify({'error': 'Files not found'}), 404

@app.route('/api/supported-sites')
@cache.cached(timeout=86400)  # Cache for 24 hours
def supported_sites():
    """Get list of supported sites"""
    try:
        with yt_dlp.YoutubeDL() as ydl:
            extractors = ydl._get_extractors()
            sites = []
            for extractor in extractors:
                if hasattr(extractor, 'IE_NAME') and hasattr(extractor, 'IE_DESC'):
                    sites.append({
                        'name': extractor.IE_NAME,
                        'description': extractor.IE_DESC
                    })
            return jsonify(sites[:50])  # Return first 50 for performance
    except:
        return jsonify([])

@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt for SEO"""
    return send_file('static/robots.txt', mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    """Serve sitemap.xml for SEO"""
    return send_file('static/sitemap.xml', mimetype='application/xml')

# Cleanup old downloads periodically
def cleanup_old_downloads():
    """Clean up old download data"""
    current_time = time.time()
    to_remove = []
    
    for download_id, progress in download_progress.items():
        # Remove downloads older than 1 hour
        if progress.get('start_time') and current_time - progress.get('start_time', 0) > 3600:
            to_remove.append(download_id)
    
    for download_id in to_remove:
        download_progress.pop(download_id, None)
        download_files.pop(download_id, None)
        uploaded_cookies.pop(download_id, None)
        print(f"Cleaned up old download: {download_id}")

# Start cleanup thread
def run_periodic_cleanup():
    """Run cleanup every 30 minutes"""
    while True:
        time.sleep(1800)  # 30 minutes
        cleanup_old_downloads()

cleanup_thread = threading.Thread(target=run_periodic_cleanup)
cleanup_thread.daemon = True
cleanup_thread.start()

@app.route('/api/upload-cookies', methods=['POST'])
def upload_cookies():
    """Upload cookies for restricted video access"""
    try:
        data = request.get_json()
        cookies_content = data.get('cookies', '').strip()
        download_id = data.get('download_id', str(uuid.uuid4()))
        
        if not cookies_content:
            return jsonify({'error': 'Cookies content is required'}), 400
        
        # Save cookies to temporary file
        cookie_file = save_cookies_to_file(cookies_content, download_id)
        if cookie_file:
            uploaded_cookies[download_id] = cookie_file
            return jsonify({
                'success': True,
                'download_id': download_id,
                'message': 'Cookies uploaded successfully'
            })
        else:
            return jsonify({'error': 'Failed to save cookies'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Cookie upload failed: {str(e)}'}), 500

def download_video_with_fallback(url, quality, download_id, output_path, cookies=None):
    """Download video with multiple fallback strategies"""
    
    # Client strategies for downloads
    client_strategies = [
        {
            'name': 'tv_embedded',
            'player_client': 'tv_embedded',
            'player_skip': 'webpage',
        },
        {
            'name': 'web_embedded', 
            'player_client': 'web_embedded',
            'player_skip': 'webpage',
        },
        {
            'name': 'mweb',
            'player_client': 'mweb',
            'player_skip': 'configs',
        }
    ]
    
    progress_tracker = DownloadProgress(download_id)
    download_progress[download_id] = progress_tracker
    
    # Find FFmpeg path  
    ffmpeg_path = find_ffmpeg()
    
    # Get format selector using the helper function
    format_selector = get_format_selector(quality, bool(ffmpeg_path))
    
    # Detect if this format selection will need merging
    needs_merging = ffmpeg_path and ('+' in format_selector)
    progress_tracker.set_merging_needed(needs_merging)
    
    # Enhanced progress hook for FFmpeg merging
    def enhanced_progress_hook(d):
        progress_tracker.hook(d)
        if d['status'] == 'finished' and needs_merging:
            # Start simulating merge progress
            def simulate_merge_progress():
                import time
                for i in range(0, 101, 5):
                    if progress_tracker.status == 'completed':
                        break
                    progress_tracker.update_merge_progress(i)
                    time.sleep(0.1)
                
            import threading
            merge_thread = threading.Thread(target=simulate_merge_progress)
            merge_thread.daemon = True
            merge_thread.start()
    
    # Try each strategy
    for i, strategy in enumerate(client_strategies):
        try:
            print(f"Download attempt {i+1} with {strategy['name']}")
            
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            
            import random
            selected_ua = random.choice(user_agents)
            
            ydl_opts = {
                'format': format_selector,
                'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
                'progress_hooks': [enhanced_progress_hook],
                'extractaudio': quality == 'audio',
                'audioformat': 'mp3' if quality == 'audio' else None,
                'writeinfojson': False,
                'writeautomaticsub': False,
                'writesubtitles': False,
                'keepvideo': False,
                'ffmpeg_location': ffmpeg_path if ffmpeg_path else None,
                
                # Use current strategy
                'extractor_args': {
                    'youtube': {
                        'player_client': strategy['player_client'],
                        'player_skip': strategy['player_skip'],
                        'skip': ['dash', 'hls'] if i < 2 else [],
                        'innertube_host': 'studio.youtube.com' if i == 0 else None,
                        'comment_sort': ['top']
                    }
                },
                
                'http_headers': {
                    'User-Agent': selected_ua,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Cache-Control': 'max-age=0',
                    'Referer': 'https://www.youtube.com/',
                    'Origin': 'https://www.youtube.com'
                },
                
                'cookiefile': cookies,
                'retries': 3,
                'fragment_retries': 3,
                'sleep_interval': 3 + i,
                'max_sleep_interval': 8 + i * 2,
                'no_warnings': True,
                'ignoreerrors': False,
                'geo_bypass': True,
                'geo_bypass_country': 'US',
                'merge_output_format': 'mp4',
                'prefer_free_formats': False,
                'postprocessors': [] if not ffmpeg_path else [],
                'postprocessor_args': {
                    'ffmpeg': [
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-b:a', '192k',
                        '-movflags', '+faststart'
                    ] if ffmpeg_path else []
                },
                'skip_unavailable_fragments': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Store file information
                if 'entries' in info:  # Playlist
                    files = []
                    for entry in info['entries']:
                        if entry:
                            filename = ydl.prepare_filename(entry)
                            if os.path.exists(filename):
                                files.append(filename)
                    download_files[download_id] = files
                else:  # Single video
                    filename = ydl.prepare_filename(info)
                    if os.path.exists(filename):
                        download_files[download_id] = [filename]
                
                print(f"Download successful with strategy: {strategy['name']}")
                progress_tracker.status = 'completed'
                return
                        
        except Exception as e:
            print(f"Strategy {strategy['name']} failed: {str(e)[:100]}...")
            # Continue to next strategy
            continue
    
    # If all strategies failed
    progress_tracker.status = 'error'
    progress_tracker.error = "All download strategies failed. Video may be unavailable, private, or region-blocked."