# 🎥 Vozilla

A professional SaaS-level YouTube video and playlist downloader with premium UI and advanced features.

![Vozilla](https://img.shields.io/badge/Vozilla-YouTube%20Downloader-blue?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-green?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-2.3+-red?style=for-the-badge&logo=flask)
![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)

## ✨ Features

- **🚀 Lightning Fast Downloads** - Optimized for maximum speed and reliability
- **🎯 4K+ Quality Support** - Downloads up to 4K resolution and beyond
- **📑 Playlist Support** - Download entire playlists with one click
- **🔒 100% Secure** - No data stored, completely anonymous and private
- **📱 Responsive Design** - Works perfectly on all devices
- **🎨 Premium UI** - Modern, clean, and professional interface
- **⚡ Real-time Progress** - Live download progress with FFmpeg merging tracking
- **🔄 Multiple Formats** - MP4, MP3, and various quality options
- **🍪 Cookie Support** - Manual cookie upload for restricted/private videos
- **🛡️ Bypass Restrictions** - Advanced strategies to bypass 403 errors and SABR streaming
- **📊 SEO Optimized** - Full SEO implementation with structured data
- **🚫 No Rate Limits** - Unlimited downloads for all users

## 🚀 Quick Start

### Method 1: Easy Start (Windows)
1. Double-click `start.bat`
2. Wait for installation to complete
3. Open http://localhost:3000 in your browser

### Method 2: Manual Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/HaseebIqbal1199/Vozila.git
   cd Vozila
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python source.py
   ```

5. **Open in browser**
   ```
   http://localhost:3000
   ```

## 🛠️ Advanced Setup

### With FFmpeg (Recommended)
For best quality downloads with video/audio merging:

1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Add FFmpeg to your PATH or place `ffmpeg.exe` in the project folder
3. Run using: `start_with_ffmpeg.bat`

### Environment Variables
Create a `.env` file in the project root:
```env
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-here
```

## 🚀 Deployment

### Railway Deployment (Recommended)
1. Push your code to GitHub
2. Connect to [Railway](https://railway.app)
3. Deploy directly from GitHub
4. Add your custom domain

See `DEPLOYMENT_GUIDE.md` for detailed instructions.

### Manual Deployment
```bash
# Install production dependencies
pip install -r requirements.txt

# Run with Gunicorn
gunicorn --bind 0.0.0.0:3000 source:app
```

## 📊 SEO & Marketing

Vozilla comes with enterprise-level SEO optimization:
- ✅ Complete meta tags and structured data
- ✅ Open Graph and Twitter Card support
- ✅ Robots.txt and sitemap.xml
- ✅ Performance optimized

Run SEO analysis:
```bash
python seo_analyzer.py yourdomain.com
```

## 🛡️ Security Features

- **No Data Storage** - Downloads are temporary and auto-deleted
- **Privacy First** - No user tracking or data collection
- **Secure Headers** - HTTPS redirect and security headers
- **Rate Limiting** - (Disabled for open access)
- **Cookie Support** - For accessing restricted content

## 🎯 Technical Details

### Supported Formats
- **Video**: MP4, WebM, MKV (up to 4K)
- **Audio**: MP3, M4A, FLAC
- **Quality**: 144p to 4K+ (when available)

### Advanced Features
- **Format Selection** - Smart quality selection with fallbacks
- **Progress Tracking** - Real-time download and merge progress
- **Error Handling** - Comprehensive error recovery
- **Multi-Client** - Support for different YouTube clients
- **Async Processing** - Non-blocking download processing

### Technology Stack
- **Backend**: Python Flask
- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript
- **Video Processing**: yt-dlp, FFmpeg
- **Deployment**: Railway, Gunicorn
- **SEO**: Structured Data, Meta Tags

## 📖 API Documentation

### Get Video Info
```javascript
POST /api/info
{
  "url": "https://youtube.com/watch?v=..."
}
```

### Start Download
```javascript
POST /api/download
{
  "url": "https://youtube.com/watch?v=...",
  "quality": "best",
  "cookies": "optional_cookies_string"
}
```

### Check Progress
```javascript
GET /api/progress/{download_id}
```

### Download File
```javascript
GET /api/download/{download_id}
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Amazing YouTube downloader library
- [FFmpeg](https://ffmpeg.org/) - Video processing powerhouse
- [Flask](https://flask.palletsprojects.com/) - Lightweight web framework
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework

## 📞 Support

- **Documentation**: Check the `DEPLOYMENT_GUIDE.md` and `MARKETING_GUIDE.md`
- **Issues**: Report bugs via GitHub Issues
- **SEO Analysis**: Use the included `seo_analyzer.py`
- **Deployment**: Follow `DEPLOYMENT_SUCCESS.md`

---

**⭐ Star this repository if you find it useful!**

Made with ❤️ for the YouTube downloading community.
