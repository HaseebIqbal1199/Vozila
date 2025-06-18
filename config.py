"""
Production configuration for YouTube Downloader
"""

import os
from datetime import timedelta

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # Cache configuration
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # File upload configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Security headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline' https://www.googletagmanager.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: https: http:; font-src 'self' data:; connect-src 'self' https:; media-src 'self' https: data:;"
    }
    
    # Rate limiting (removed for open access, but keeping config for future use)
    RATELIMIT_ENABLED = False
    
    # Download configuration
    DOWNLOAD_TIMEOUT = 300  # 5 minutes
    MAX_CONCURRENT_DOWNLOADS = 10
    
    # Cleanup configuration
    CLEANUP_INTERVAL = 1800  # 30 minutes
    MAX_FILE_AGE = 3600  # 1 hour
    
    # Production optimizations
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)
    
    @staticmethod
    def init_app(app):
        # Add security headers
        @app.after_request
        def after_request(response):
            for header, value in Config.SECURITY_HEADERS.items():
                response.headers[header] = value
            return response
        
        # Force HTTPS in production
        @app.before_request
        def force_https():
            from flask import request, redirect
            if not request.is_secure and request.headers.get('X-Forwarded-Proto') != 'https':
                if os.environ.get('FLASK_ENV') == 'production':
                    return redirect(request.url.replace('http://', 'https://'))

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    
    # Use more secure session configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database URL (if using database in future)
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to stderr in production
        import logging
        from logging import StreamHandler
        file_handler = StreamHandler()
        file_handler.setLevel(logging.WARNING)
        app.logger.addHandler(file_handler)

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True

class TestingConfig(Config):
    TESTING = True
    DEBUG = True

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
