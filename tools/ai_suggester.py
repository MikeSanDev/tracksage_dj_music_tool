
"""
AI Rename Suggester
-------------------
This module acts as a *helper* for the rename tool.

When a track has missing or unreliable tags, this script asks an AI model
to infer the most likely "Artist - Title.mp3" name based on the filename
and any tag fragments that exist.

Example use:
    from tools.ai_suggester import suggest_name_with_ai
    new_name = suggest_name_with_ai("Daft_Punk-Face2Face.mp3")
"""

import os
import logging
from typing import Optional
from openai import OpenAI  # ← we'll use OpenAI GPT-4o-mini
from dotenv import load_dotenv 

# --- OpenAI client  ---
load_dotenv()
client = OpenAI()
logging.basicConfig(filename="logs/ai_suggest_errors.log", level=logging.WARNING)


def suggest_name_with_ai(filename: str, artist_hint: Optional[str] = None, title_hint: Optional[str] = None) -> Optional[str]:
    """
    Suggest a clean, standardized filename in the format:
    'Artist - Title.mp3'
    """

     # 1️⃣ Prepare the AI prompt with examples and context
    base_prompt = f"""
    You are an expert in cleaning and standardizing MP3 filenames.
    Given a raw filename and any partial tags, suggest the best formatted name
    in the exact format: Artist - Title.mp3

    Rules:
    - Capitalize each word correctly.
    - Preserve remix/cover info, e.g., 'song_remix' → 'Song (Remix)'.
    - Keep featuring artists like 'feat.' intact.
    - Remove unnecessary underscores, brackets, or symbols.
    - DO NOT add text that isn't clearly part of the name.
    - Return only the final name, nothing else.

    Examples:
    - Input: "daftpunk-face2face.mp3" → Output: "Daft Punk - Face to Face.mp3"
    - Input: "theweeknd_save_your_tears(remix).mp3" → Output: "The Weeknd - Save Your Tears (Remix).mp3"
    - Input: "songtitle(feat_dojacat)" → Output: "Unknown Artist - Song Title (feat. Doja Cat).mp3"

    Now, here is the file to clean:
    Filename: {filename}
    Artist hint: {artist_hint or 'None'}
    Title hint: {title_hint or 'None'}
    """

    try:
        # Send it to GPT-4o-mini for lightweight, fast inference
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant for cleaning and formatting music filenames."},
                {"role": "user", "content": base_prompt}
            ],
            temperature=0.3,  # lower = more consistent naming
        )

        # Extract the AI’s suggestion (strip newlines/spaces just in case)
        content = response.choices[0].message.content
        if content is not None:
            suggestion = content.strip()
        else:
            print(f"⚠️ AI response did not contain a suggestion for {filename}.")
            return None

        # Add .mp3 if missing
        if not suggestion.lower().endswith(".mp3"):
            suggestion += ".mp3"

        return suggestion

    except Exception as e:
        print(f"⚠️ AI rename failed for {filename}: {e}")
        return None