import os
from datetime import datetime
from faster_whisper import WhisperModel
from openai import OpenAI
from dotenv import load_dotenv

"""
This tool handles local transcription using Faster-Whisper.
After transcribing, it can optionally summarize the transcript using OpenAI.
"""

load_dotenv()
client = OpenAI()


# ------------------ Core Transcription ------------------ #
def transcribe_audio(file_path: str, summarize: bool = False):
    """
    Transcribes a given audio file using Faster-Whisper.
    Optionally summarizes the result using OpenAI.

    Args:
        file_path: Path to the audio file (.mp3, .wav, .m4a, etc.)
        summarize: Whether to generate a summarized version
    """

    