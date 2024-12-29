from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import yt_dlp
import os
from tempfile import gettempdir
import logging

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
        
        # Print the current progress
        print(f"Downloaded: {download_progress['current']} bytes of {download_progress['total']} bytes.")
        
    elif d['status'] == 'finished':
        print(f"Download Finished: {d.get('filename')}")
        download_progress = {'current': 0, 'total': 0}  # Reset progress

# Download video and provide progress
def download_video(request):
    if request.method == 'POST':
        url = request.POST.get('url')
        mode = request.POST.get('mode', 'both')

        if not url:
            return JsonResponse({'error': 'No URL provided'}, status=400)

        try:
            # Temporary directory to store the downloaded file
            temp_dir = gettempdir()
            output_path = os.path.join(temp_dir, '%(title)s.%(ext)s')

            # Set up yt_dlp options
            options = {
                'outtmpl': output_path,
                'progress_hooks': [progress_hook],
                'format': 'best'  # Default format for both audio and video
            }
            
            if mode == 'audio':
                options['format'] = 'bestaudio'
            elif mode == 'video':
                options['format'] = 'bestvideo'

            # Start downloading the video
            print("Starting download with yt-dlp...")
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                print(f"Download started: {filename}")

            # Once download is complete, return the file as an attachment
            print(f"Returning file: {filename}")
            response = HttpResponse(open(filename, 'rb'), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(filename)}"'

            # Reset the progress after the download is complete
            global download_progress
            download_progress = {'current': 0, 'total': 0}

            return response

        except Exception as e:
            print(f"Error during download: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

# This function will allow you to send progress data to the frontend.
def get_progress(request):
    try:
        if download_progress['total'] > 0:
            progress = (download_progress['current'] / download_progress['total']) * 100
        else:
            progress = 0
        print(f"Progress sent: {progress}%")
        return JsonResponse({'progress': progress}, status=200)
    except Exception as e:
        print(f"Error fetching progress: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)