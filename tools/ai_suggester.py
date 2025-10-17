# OS lets us walk through directories and join file paths
import os
# lets you read/write structured data to disk (e.g. cache file)
import json
# standard library for saving warning/error messages to a log file.
import logging
# a type hint meaning “this value can either be of the given type or None.”
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

"""
AI Rename Suggester
-------------------
This module acts as a *helper* for the rename tool.

When a track has missing or unreliable tags, this script asks an AI model
to infer the most likely "Artist - Title.mp3" name based on the filename
and any tag fragments that exist.

Example:
    from tools.ai_suggester import suggest_name_with_ai
    new_name = suggest_name_with_ai("Daft_Punk-Face2Face.mp3")
    print(new_name)  # → "Daft Punk - Face to Face.mp3"
"""

# --- Setup: environment + client + logging ---
load_dotenv()
client = OpenAI()
logging.basicConfig(filename="logs/ai_suggest_errors.log", level=logging.WARNING)

# ---------------- Caching ---------------- #
CACHE_PATH = "data/ai_cache.json"

# Checks if data directory exists, creates one if not
os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

# Load existing cache (if any)
try: 
    with open(CACHE_PATH, "r", encoding="utf-8") as f: # load cache from file
        AI_CACHE = json.load(f)
except FileNotFoundError:
    AI_CACHE = {}  # empty cache on first run
except json.JSONDecodeError:
    AI_CACHE = {}  # corrupted or empty file fallback

# Function to save cache
def save_cache():
    """Persist current cache to disk."""
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(AI_CACHE, f, indent=2, ensure_ascii=False)


# ---------------- Core Function ---------------- #
def suggest_name_with_ai(filename: str, artist_hint: Optional[str] = None, title_hint: Optional[str] = None) -> Optional[str]:
    """
    SAGE suggests a clean, standardized filename in the format:
    'Artist - Title.mp3'

    Uses local saved cache before calling the OpenAI API.
    """

    # Checks cache first before making API call - to save money and time
    if filename in AI_CACHE:
        cached = AI_CACHE[filename]
        print(f"🔁 Using cached AI suggestion for: {filename}")
        return cached

    # AI prompt
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

    Filename: {filename}
    Artist hint: {artist_hint or 'None'}
    Title hint: {title_hint or 'None'}
    """

    try:
        # Send request to GPT-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant for cleaning and formatting music filenames."},
                {"role": "user", "content": base_prompt},
            ],
            temperature=0.3,
        )

        # Validate response
        if not hasattr(response, "choices") or not response.choices:
            print(f"⚠️ No AI response for {filename}")
            return None

        content = response.choices[0].message.content
        suggestion = content.strip() if content else None
        if not suggestion:
            print(f"⚠️ Empty AI output for {filename}")
            return None

        # Normalize 
        if not suggestion.lower().endswith(".mp3"):
            suggestion += ".mp3"

        # Save to cache
        AI_CACHE[filename] = suggestion
        save_cache()

        return suggestion
    
    #this exception handles any errors from the OpenAI API or other issues
    except Exception as e:
        logging.warning(f"AI rename failed for {filename}: {e}")
        print(f"⚠️ AI rename failed for {filename}: {e}")
        return None