# ytexplains/home/views.py
import json
from django.http import JsonResponse
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
from django.views.decorators.csrf import csrf_exempt
import re
from .utils import get_gemini_response

def chunk_transcript(transcript, max_length=1000):
    """
    Chunk the transcript into smaller parts based on max_length.
    Returns both chunked text and timestamps.
    """
    chunks = []
    current_chunk = []
    current_length = 0

    for entry in transcript:
        text = entry['text'].strip()
        if current_length + len(text) > max_length and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = [text]
            current_length = len(text)
        else:
            current_chunk.append(text)
            current_length += len(text)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def extract_video_id(url):
    """
    Extract video ID from various YouTube URL formats.
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',  # Standard and shortened
        r'(?:embed\/)([0-9A-Za-z_-]{11})',   # Embed URLs
        r'(?:shorts\/)([0-9A-Za-z_-]{11})',  # Shorts
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@csrf_exempt
def fetch_youtube_transcript(request):
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Only POST method is allowed'
        }, status=405)

    try:
        data = json.loads(request.body)
        youtube_urls = data.get('urls', [])
        
        if not youtube_urls:
            return JsonResponse({
                'success': False,
                'error': 'No YouTube URLs provided'
            }, status=400)

        # Convert single URL to list if necessary
        if isinstance(youtube_urls, str):
            youtube_urls = [youtube_urls]

        all_transcripts = []
        failed_urls = []

        for youtube_url in youtube_urls:
            video_id = extract_video_id(youtube_url)
            if not video_id:
                failed_urls.append({
                    'url': youtube_url,
                    'error': 'Invalid YouTube URL format'
                })
                continue

            try:
                # Try English first, then Hindi
                try:
                    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                except NoTranscriptFound:
                    try:
                        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['hi'])
                    except NoTranscriptFound:
                        raise NoTranscriptFound("No transcript found in English or Hindi")

                # Process transcript chunks
                transcript_chunks = chunk_transcript(transcript)
                all_transcripts.extend(transcript_chunks)

            except (TranscriptsDisabled, NoTranscriptFound) as e:
                failed_urls.append({
                    'url': youtube_url,
                    'error': 'No subtitles available for this video'
                })
            except VideoUnavailable:
                failed_urls.append({
                    'url': youtube_url,
                    'error': 'Video is unavailable'
                })
            except Exception as e:
                failed_urls.append({
                    'url': youtube_url,
                    'error': str(e)
                })

        if not all_transcripts and failed_urls:
            return JsonResponse({
                'success': False,
                'error': 'Could not fetch any transcripts',
                'failed_urls': failed_urls
            }, status=400)

        # Combine transcripts and get Gemini response
        try:
            combined_transcript = "\n\n".join(all_transcripts)
            gemini_response = get_gemini_response(combined_transcript)
            
            response_data = {
                'success': True,
                'response': gemini_response
            }
            
            # Include failed URLs if any
            if failed_urls:
                response_data['failed_urls'] = failed_urls
                
            return JsonResponse(response_data)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error processing with Gemini: {str(e)}',
                'transcripts_retrieved': len(all_transcripts) > 0,
                'failed_urls': failed_urls
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data in request'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)