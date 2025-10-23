import os
from datetime import datetime
from faster_whisper import WhisperModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

"""
Transcribe Audio

This tool handles local transcription using Faster-Whisper.
After transcribing, it can optionally summarize the transcript using OpenAI.

"""