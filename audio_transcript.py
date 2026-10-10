from pathlib import Path
import yt_dlp
import whisper
import os
import json
import sys
import glob

def get_app_path():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent

# Convert seconds into MM:SS format
def timechanger(timestamp):
    total_seconds = int(timestamp)
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"



def get_transcript(id,url):

    video_id = id
    video_url = url

    folder_path = get_app_path()
    transcript_folder = folder_path / "transcript_files"
    audio_folder = folder_path / "audio_files"

    transcript_file = transcript_folder / f"transcript_{video_id}.json"

    if os.path.exists(transcript_file):

        with open(transcript_file, "r", encoding="utf-8") as file:
            transcript = json.load(file)

        print("Cached transcript found. Reusing it.")

    else:
        print("No cached transcript found. We need to create it.")

        # Search for existing audio files
        audio_files = glob.glob(str(audio_folder / f"audio_{video_id}.*"))
        audio_file = None

        for candidate in audio_files:
            if candidate.lower().endswith((".part", ".ytdl")):
                continue

            if os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
                audio_file = candidate
                break

        # Download audio only if it wasn't found locally
        if audio_file is None:

            print("No cached audio found. Downloading...")

            ydl_opts = {
                "format": "bestaudio",
                "outtmpl": str(audio_folder / "audio_%(id)s.%(ext)s"),
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            # Search again after downloading
            audio_files = glob.glob(str(audio_folder / f"audio_{video_id}.*"))

            for candidate in audio_files:
                if candidate.lower().endswith((".part", ".ytdl")):
                    continue

                if os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
                    audio_file = candidate
                    break

            if audio_file is None:
                raise FileNotFoundError(
                    "Audio download completed, but no audio file was found."
                )

            print(f"Audio downloaded: {audio_file}")

        else:
            print(f"Cached audio found. Reusing: {audio_file}")

        # IMPORTANT: This part runs whether audio was downloaded or reused

        print("Loading Whisper model...")
        model = whisper.load_model("base")

        print("Transcribing audio...")
        result = model.transcribe(audio_file)

        # Extract timestamps and text
        transcript = []

        for segment in result["segments"]:
            transcript.append({
                "start": timechanger(segment["start"]),
                "end": timechanger(segment["end"]),
                "text": segment["text"].strip()
            })

        # Save the transcript for future runs
    with open(transcript_file, "w", encoding="utf-8") as file:
        json.dump(
            transcript,
            file,
            ensure_ascii=False,
            indent=4
        )

    print(f"Transcript saved: {transcript_file}")


    # Display the transcript, whether loaded or newly created
    for segment in transcript:
        print(
            f"[{segment['start']} - {segment['end']}] "
            f"{segment['text']}"
        )

    return transcript


# For Local Videos ------------------->>>>>
def get_transcript_from_local(video_path,video_id=None):
    video_path = Path(video_path).expanduser().resolve()

    if not video_path.is_file():
        raise FileNotFoundError(f"Video not found: {video_path}")

    if video_id is None:
        video_id = video_path.stem

    folder_path = get_app_path()
    transcript_folder = folder_path / "transcript_files"
    audio_folder = folder_path / "audio_files"

    transcript_file = transcript_folder / f"transcript_{video_id}.json"

    if transcript_file.exists():
        with open(transcript_file,'r',encoding="utf-8") as file:
            transcript = json.load(file)

        print("Transcript found in cache")
        return transcript

    # Transcript not found
    print('Initiating Whisper Model')
    model = whisper.load_model('base')

    print("Transcripting the audio...")
    result = model.transcribe(str(video_path))

    transcript = []

    for segments in result["segments"]:
        transcript.append(
            {
                "start":timechanger(segments['start']),
                "end":timechanger(segments['end']),
                "text": segments['text'].strip()
            }
        )


    # saving the transcript file
    with open(transcript_file,"w",encoding="utf-8") as file:
        json.dump(transcript,file,ensure_ascii=False,indent=4)

    print(f"Transcript saved: {transcript_file}")

    return transcript

# python  audio_transcript.py