from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import yt_dlp
import os
from tempfile import gettempdir
import logging
import threading


# Global variable to store download progress
download_progress = {'current': 0, 'total': 0}

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Home page view
def home(request):
    return render(request, 'downloader/home.html')
def progress_hook(d):
    """Hook function to update progress."""
    global download_progress
    if d['status'] == 'downloading':
        download_progress['current'] = d.get('downloaded_bytes', 0)
        download_progress['total'] = d.get('total_bytes', 0)
        print(f"Progress: {download_progress['current']} / {download_progress['total']}")
    elif d['status'] == 'finished':
        print(f"Download Finished: {d.get('filename')}")
        download_progress = {'current': 0, 'total': 0}  # Reset progress


# This function will allow you to send progress data to the frontend.
def get_progress(request):
    try:
        if download_progress['total'] > 0:
            progress = (download_progress['current'] / download_progress['total']) * 100
        else:
            progress = 0
        return JsonResponse({'progress': progress}, status=200)
    except Exception as e:
        print(f"Error fetching progress: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)






def download_video(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        mode = request.POST.get('mode', 'both')

        if not url:
            return JsonResponse({'error': 'No URL provided'}, status=400)

        try:
            # Start downloading the video in a separate thread
            download_thread = threading.Thread(target=download_video_thread, args=(url, mode))
            download_thread.start()

            return JsonResponse({'status': 'Download started'}, status=200)

        except Exception as e:
            print(f"Error during download: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def download_video_thread(url, mode):
    try:
        # Temporary directory to store the downloaded file
        temp_dir = gettempdir()
        output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')

        # Set up yt-dlp options
        options = {
            'outtmpl': output_path,
            'progress_hooks': [progress_hook],
        }

        # Adjust format and postprocessing based on mode
        if mode == 'audio':
            options['format'] = 'bestaudio/best'  # Download best audio
            options['postprocessors'] = [  # Convert to MP3 after download
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',  # Adjust quality as needed
                }
            ]
        elif mode == 'video':
            options['format'] = 'bestvideo+bestaudio[ext=mp4]/best[ext=mp4]'  # Best video and audio, MP4 container
        else:  # For both, default to highest quality available
            options['format'] = 'bestvideo+bestaudio/best'

        # Start downloading the video/audio
        print("Starting download with yt-dlp...")
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            print(f"Download complete: {filename}")

    except Exception as e:
        print(f"Error during download: {str(e)}")