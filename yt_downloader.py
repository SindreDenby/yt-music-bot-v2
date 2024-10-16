import os
from pytube import YouTube
import re

def clean_file_name(file_name):
    # Define a regular expression pattern that matches invalid characters
    invalid_chars = r'[\/:*?"<>|]'

    # Use re.sub to replace invalid characters with an empty string
    cleaned_file_name = re.sub(invalid_chars, '', file_name)

    return cleaned_file_name

def get_url_title(url):
    try:
        yt = YouTube(url)

        return yt.title

    except Exception as e:
        print(f"An error occurred: {str(e)}")

def get_list_of_titles(url_list):
    return [get_url_title(i) for i in url_list]

def is_valid_url(url):
    """
    Returns true if url is valid yt video
    """
    try:
        yt = YouTube(url)

        if yt.title == None: return False

        return True
    except Exception as e:
        print(f"An error occurred: {str(e)}")


def download_youtube_audio(url: str, output_path="sounds"):
    try:
        # Create a YouTube object
        yt = YouTube(url)

        # Select the best stream with audio
        audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
        mp3_name = f"{clean_file_name(yt.title)}.mp3" 

        # Define the MP3 file path
        mp3_file = os.path.join(output_path, mp3_name)
        # Check if the MP3 file already exists
        if mp3_name in os.listdir(output_path):
            print(f"MP3 file already exists: {mp3_file}")
            return mp3_file

        # Download the audio stream
        audio_stream.download(output_path=output_path, filename=mp3_name)

        print(f"Audio downloaded as: {mp3_file}")
        return mp3_file

    except Exception as e:
        print(f"An error occurred: {str(e)}")