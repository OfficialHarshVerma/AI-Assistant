from urllib.parse import urlparse, parse_qs
from pathlib import Path

def extract_youtube_details(url):
    parsed_url = urlparse(url.strip())

    if parsed_url.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        video_id = parse_qs(parsed_url.query).get("v", [None])[0]

    elif parsed_url.hostname == "youtu.be":
        video_id = parsed_url.path.lstrip("/").split("/")[0]

    else:
        raise ValueError("Invalid YouTube URL.")

    if not video_id:
        raise ValueError("Could not extract the YouTube video ID.")

    video_url = f"https://www.youtube.com/watch?v={video_id}"

    return video_url, video_id




def identify(url):
    user_input = url.strip().strip('"').strip("'")

    parsed_url = urlparse(user_input)

    # Check whether the input is an HTTP/HTTPS URL
    if parsed_url.scheme in ("http","https") and parsed_url.netloc:
        return "url", user_input

        # Otherwise, check whether it is an existing local file
    video_path = Path(user_input).expanduser()

    if video_path.is_file():
        return "local", video_path

    raise ValueError("Input is neither a valid URL nor an existing file path.")
