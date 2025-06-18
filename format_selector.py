def get_format_selector(quality, ffmpeg_available):
    """Get the appropriate format selector for the given quality and FFmpeg availability"""
    
    if quality == 'audio':
        return 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio'
    
    if ffmpeg_available:
        # With FFmpeg - prioritize separate high-quality streams, then single files as fallback
        if quality == '144p':
            return 'bestvideo[height<=144]+bestaudio/best[height<=144][ext=mp4]/best[height<=144]'
        elif quality == '360p':
            return 'bestvideo[height<=360]+bestaudio/best[height<=360][ext=mp4]/best[height<=360]'
        elif quality == '480p':
            return 'bestvideo[height<=480]+bestaudio/best[height<=480][ext=mp4]/best[height<=480]'
        elif quality == '720p':
            return 'bestvideo[height<=720]+bestaudio/best[height<=720][ext=mp4]/best[height<=720]'
        elif quality == '1080p':
            return 'bestvideo[height<=1080]+bestaudio/best[height<=1080][ext=mp4]/best[height<=1080]'
        else:  # 'best'
            return 'bestvideo+bestaudio/best[ext=mp4]/best'
    else:
        # Without FFmpeg - prefer single MP4 files
        if quality == '144p':
            return 'best[height<=144][ext=mp4]/best[height<=144]'
        elif quality == '360p':
            return 'best[height<=360][ext=mp4]/best[height<=360]'
        elif quality == '480p':
            return 'best[height<=480][ext=mp4]/best[height<=480]'
        elif quality == '720p':
            return 'best[height<=720][ext=mp4]/best[height<=720]'
        elif quality == '1080p':
            return 'best[height<=1080][ext=mp4]/best[height<=1080]'
        else:  # 'best'
            return 'best[ext=mp4]/best'
