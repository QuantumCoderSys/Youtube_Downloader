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
            'format': 'bestvideo+bestaudio/best',  # Highest resolution video with best audio
        }
        
        if mode == 'audio':
            options['format'] = 'bestaudio'
        elif mode == 'video':
            options['format'] = 'bestvideo+bestaudio/best'  # Highest quality video and audio

        # Start downloading the video
        print("Starting download with yt-dlp...")
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            print(f"Download started: {filename}")

        # Once download is complete, return the file as an attachment
        print(f"Returning file: {filename}")

        # Clean up the downloaded file
        os.remove(filename)
        print(f"File {filename} removed after download.")

    except Exception as e:
        print(f"Error during download: {str(e)}")