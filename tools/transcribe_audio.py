import os
from datetime import datetime
from faster_whisper import WhisperModel #WhisperModel is a class from the faster-whisper library
from openai import OpenAI
from dotenv import load_dotenv

"""
This tool handles local transcription using Faster-Whisper.
After transcribing, it can optionally summarize the transcript using OpenAI.
"""

load_dotenv()
client = OpenAI()


# ------------------ Core Transcription ------------------ #
def transcribe_audio(file_path: str, summarize: bool = False): #since summary is optional, default is False 
    """
    Transcribes a given audio file using Faster-Whisper.
    Optionally summarizes the result using OpenAI.

    Args:
        file_path: Path to the audio file (.mp3, .wav, .m4a, etc.)
        summarize: Whether to generate a summarized version
    """

  # Load model (tiny = fastest, good for speech) 'base', 'small', 'medium', 'large-v2' are other options
    model = WhisperModel("tiny", device="cpu", compute_type="int8") #can change device to GPU if available

    # log file paths - for transcript and summary
    timestamp = datetime.now().strftime("%m_%d_%Y_%H-%M-%S")
    base_name = os.path.splitext(os.path.basename(file_path))[0] #extract file name from path without extension (.mp3, .wav, etc.)
    output_dir = "logs"
    os.makedirs(output_dir, exist_ok=True)

    txt_path = os.path.join(output_dir, f"transcribed_{base_name}_{timestamp}.txt")
    summary_path = os.path.join(output_dir, f"ai_summary_{base_name}_{timestamp}.txt")

    print(f"\n🎙️ Transcribing: {file_path}\n(This may take a few minutes for long files...)")
