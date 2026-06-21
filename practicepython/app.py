from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
import yt_dlp
from pydub import AudioSegment
from pathlib import Path


app = Flask(__name__)
CORS(app) # Allows your frontend web page to talk to this backend safely

DOWNLOADS_DIR = str(Path.home() / "Downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def download_and_convert_single_item(item, session_dir):
    video_id = item['url'].split("=")[-1]
    temp_output_template = os.path.join(session_dir, f"temp_{video_id}.%(ext)s")
    
    item_opts = {
        'format': 'bestaudio/best',
        'outtmpl': temp_output_template,
        'quiet': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(item_opts) as ydl:
            info = ydl.extract_info(item['url'], download=True)
            downloaded_ext = info['ext']
            temp_file_path = os.path.join(session_dir, f"temp_{video_id}.{downloaded_ext}")

        # Ensure a clean filename for web file unu service
        clean_filename = "".join([c for c in item['target_filename'] if c.isalpha() or c.isdigit() or c in ' .-_ ']).rstrip()
        final_wav_filename = f"{clean_filename}.wav"
        final_wav_path = os.path.join(session_dir, final_wav_filename)
        
        audio = AudioSegment.from_file(temp_file_path, format=downloaded_ext)
        audio.export(final_wav_path, format="wav", parameters=["-acodec", "pcm_s16le"])
        
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
        return {"status": "success", "filename": final_wav_filename, "title": item['original_title']}
    except Exception as e:
        return {"status": "failed", "title": item['original_title'], "error": str(e)}


@app.route('/api/process-playlist', methods=['POST'])
def process_playlist():
    data = request.json
    playlist_url = data.get('url')
    
    if not playlist_url:
        return jsonify({"error": "No URL provided"}), 400

    # 1. Fetch playlist metadata info
  # Updated options configuration dictionary
    ydl_opts = {
        'format': 'bestaudio/best',
        'extract_flat': False,     # Disabled so yt-dlp deep-scans video data details
        'skip_download': True,     # Keeps it from downloading raw video files right now

        # Tells yt-dlp to save directly to your Downloads folder using the video title
        'outtmpl' : f'{DOWNLOADS_DIR}/%(title)s.%(ext)s',
        
        # Explicitly maps your Lubuntu Node.js engine to the extractor pipeline
        'extractor_args': {
            'youtube': {
                'js_runtimes': 'node'
            }
        }
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            playlist_dict = ydl.extract_info(playlist_url, download=False)
            if 'entries' not in playlist_dict:
                return jsonify({"error": "Not a valid playlist link"}), 400
            raw_videos = playlist_dict['entries']
        except Exception as e:
            return jsonify({"error": f"Failed to fetch metadata: {str(e)}"}), 500

    # Create a unique session folder for this specific request so users don't mix up files
    session_id = str(uuid.uuid4())
    session_dir = os.path.join(DOWNLOADS_DIR, session_id)
    os.makedirs(session_dir, exist_ok=True)

    # 2. Build the queue
    queue_to_process = []
    for index, video in enumerate(raw_videos):
        queue_to_process.append({
            "url": f"https://www.youtube.com/watch?v={video['id']}",
            "original_title": video['title'],
            "target_filename": f"{str(index + 1).zfill(2)}_{video['title']}"
        })

    # 3. Parallel Process (Since we are on a desktop/server environment now, we can bump workers to 5!)
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(download_and_convert_single_item, item, session_dir): item 
            for item in queue_to_process
        }
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({
        "session_id": session_id,
        "results": results
    })

# Endpoint allowing users to download their finished WAV files from the browser
@app.route('/downloads/<session_id>/<filename>', methods=['GET'])
def download_file(session_id, filename):
    return send_from_directory(os.path.join(DOWNLOADS_DIR, session_id), filename, as_attachment=True)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port=5000, debug=True)
