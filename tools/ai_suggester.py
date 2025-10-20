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
#Configures Python’s logger to save warnings into logs/ai_suggest_errors.log
logging.basicConfig(filename="logs/ai_suggest_errors.log", level=logging.WARNING) 


# ---------------- Caching ---------------- #
# defines the location of the JSON file storing cached AI results
CACHE_PATH = "data/ai_cache.json"

# Checks if data directory exists, creates one if not
os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)

# Load existing cache (if any)
try: 
    with open(CACHE_PATH, "r", encoding="utf-8") as f: # Opens the file for reading and automatically closes it when done
        AI_CACHE = json.load(f) # Converts the JSON data in the file into a Python dictionary
except FileNotFoundError:
    AI_CACHE = {}  # empty cache on first run
except json.JSONDecodeError:
    AI_CACHE = {}  # corrupted or empty file fallback

"""
Using a try-except block here ensures that if the cache file is missing or corrupted,
the program won't crash. Instead, it will start with an empty cache. 
Using a dict because its good for fast lookups or updates.
"""

# Function to save cache
def save_cache():
    """this function saves current cache to disk."""
    with open(CACHE_PATH, "w", encoding="utf-8") as f:  # opens the file for writing
        json.dump(AI_CACHE, f, indent=2, ensure_ascii=False) # writes the dictionary to disk in valid JSON format


# ---------------- Core Function ---------------- #
def suggest_name_with_ai(filename: str, artist_hint: Optional[str] = None, title_hint: Optional[str] = None) -> Optional[str]:
    """
    SAGE suggests a clean, standardized filename in the format:
    'Artist - Title.mp3'

    Uses local saved cache before calling the OpenAI API.
    """

    # Normalize the filename (makes caching consistent across folders and capitalization)
    normalized = os.path.basename(filename).lower().strip()

    # Check cache before making API call - saves money and time
    if normalized in AI_CACHE:
        cached = AI_CACHE[normalized]
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
        if not hasattr(response, "choices") or not response.choices: # checks if an object has a given attribute
            print(f"⚠️ No AI response for {filename}")
            return None # If there’s no choices attribute or it’s empty, the model didn’t reply → return None

        content = response.choices[0].message.content # response.choices → list of possible completions (we take the first one)
        suggestion = content.strip() if content else None # removes whitespace and newlines
        if not suggestion:
            print(f"⚠️ Empty AI output for {filename}")
            return None

        # Normalize - converts to lowercase and checks if it ends with .mp3
        if not suggestion.lower().endswith(".mp3"):
            suggestion += ".mp3"

        # Save to cache
        AI_CACHE[normalized] = suggestion # store the suggestion in the cache dictionary
        save_cache()

        return suggestion
    
    #this exception handles any errors from the OpenAI API or other issues
    except Exception as e:
        logging.warning(f"AI rename failed for {filename}: {e}")
        print(f"⚠️ AI rename failed for {filename}: {e}")
        return None