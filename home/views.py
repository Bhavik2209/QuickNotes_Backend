# ytexplains/home/views.py
import json
from django.http import JsonResponse
from youtube_transcript_api import YouTubeTranscriptApi, _errors
from django.views.decorators.csrf import csrf_exempt
import re
from .utils import get_gemini_response

def chunk_transcript(transcript, max_length=1000):
    """
    Chunk the transcript into smaller parts based on max_length.
    """
    chunks = []
    current_chunk = []

    for entry in transcript:
        current_chunk.append(entry['text'])
        if len(' '.join(current_chunk)) > max_length:
            chunks.append(' '.join(current_chunk))
            current_chunk = []

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

@csrf_exempt
def fetch_youtube_transcript(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            print(data)
            youtube_urls = data.get('urls', [])
            print(f"Received URL: {youtube_urls}")

            if not youtube_urls:
                return JsonResponse({'error': 'YouTube URL not provided'}, status=400)
            all_transcripts = [] 
            for youtube_url in youtube_urls:
                # Extract video ID from the URL
                video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', youtube_url)
                if not video_id_match:
                    return JsonResponse({'error': f'Invalid YouTube URL: {youtube_url}'}, status=400)

                video_id = video_id_match.group(1)
                print(f"Extracted Video ID: {video_id}")

                # Try fetching the transcript in English first
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                except _errors.NoTranscriptFound:
                    print("English transcript not found. Trying Hindi...")
                    # Try fetching the transcript in Hindi if English is not available
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])

                # Chunk the transcript
                transcript_chunks = chunk_transcript(transcript)
                all_transcripts.extend(transcript_chunks)  # Add the chunks to the list
            # Combine all transcripts into a single response
            combined_transcript = "\n\n".join(all_transcripts)
            response = get_gemini_response(combined_transcript)
            print(response)
            
            
            return JsonResponse(response)

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        except Exception as e:
            error_message = str(e)
            return JsonResponse({'error': f"An unexpected error occurred: {error_message}"}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)