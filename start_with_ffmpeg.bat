@echo off
echo Starting YouTube Downloader SaaS App...
echo.
echo FFmpeg Status:
ffmpeg -version >nul 2>&1
if %errorlevel%==0 (
    echo ✅ FFmpeg is available - High quality merging enabled
) else (
    echo ❌ FFmpeg not found - Single file formats only
)
echo.
echo Starting Flask server on http://localhost:3000
echo Press Ctrl+C to stop the server
echo.
cd /d "%~dp0"
python source.py
pause
