import os
from pytube import YouTube
import re

def clean_file_name(file_name):
    # Define a regular expression pattern that matches invalid characters
    invalid_chars = r'[\/:*?"<>|]'

    # Use re.sub to replace invalid characters with an empty string
    cleaned_file_name = re.sub(invalid_chars, '', file_name)

    return cleaned_file_name
def download_youtube_audio(url, output_path="sounds"):
    try:
        # Create a YouTube object
        yt = YouTube(url)

        # Select the best stream with audio
        audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
        mp3_name = clean_file_name(f"{yt.title}.mp3") 

        # Define the MP3 file path
        mp3_file = os.path.join(output_path, mp3_name)
        # Check if the MP3 file already exists
        if mp3_name in os.listdir(output_path):
            print(f"MP3 file already exists: {mp3_file}")
            return mp3_file

        # Download the audio stream
        audio_stream.download(output_path=output_path)

        # Rename the downloaded file to have an .mp3 extension if it's not already in MP3 format
        downloaded_file = os.path.join(output_path, audio_stream.default_filename)
        if not downloaded_file.endswith(".mp3"):
            mp3_file = os.path.splitext(downloaded_file)[0] + ".mp3"
            os.rename(downloaded_file, mp3_file)
        else:
            mp3_file = downloaded_file

        print(f"Audio downloaded as: {mp3_file}")
        return mp3_file

    except Exception as e:
        print(f"An error occurred: {str(e)}")