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

            # Extract video info without downloading
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                video_info = ydl.extract_info(url, download=False)
                formats = video_info.get('formats', [])

                # Find the best video format based on resolution
                best_video = max(
                    (fmt for fmt in formats if fmt.get('vcodec') != 'none'), 
                    key=lambda x: x.get('height', 0), 
                    default=None
                )
                
                # Find the best audio format
                best_audio = max(
                    (fmt for fmt in formats if fmt.get('acodec') != 'none'),
                    key=lambda x: x.get('abr', 0),
                    default=None
                )

                if not best_video:
                    return JsonResponse({'error': 'No video formats available'}, status=400)

            # Set yt-dlp options for the selected formats
            options = {
                'outtmpl': output_path,
                'progress_hooks': [progress_hook],
                'postprocessors': [{
                    'key': 'FFmpegMerger',  # Ensure video and audio are merged
                }]
            }

            if mode == 'video':
                options['format'] = best_video['format_id']
            elif mode == 'audio':
                options['format'] = best_audio['format_id'] if best_audio else 'bestaudio'
            else:  # Default is 'both'
                options['format'] = f"{best_video['format_id']}+{best_audio['format_id']}"

            # Start downloading
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download([url])

            # Prepare the filename
            filename = ydl.prepare_filename(video_info)

            # Serve the file as a downloadable attachment
            with open(filename, 'rb') as file:
                response = HttpResponse(file, content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(filename)}"'

            # Clean up the downloaded file
            os.remove(filename)

            return response

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

    
# This function will allow you to send progress data to the frontend.
def get_progress(request):
    try:
        if download_progress['total'] > 0:
            progress = (download_progress['current'] / download_progress['total']) * 100
        else:
            progress = 0
        # print(f"Progress sent: {progress}%")
        return JsonResponse({'progress': progress}, status=200)
    except Exception as e:
        print(f"Error fetching progress: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)