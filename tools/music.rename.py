import os
from datetime import datetime
#re: regex for sanitizing filenames
import re

#mutagen: library for reading MP3 ID3 Tags
from mutagen.easyid3 import EasyID3
from mutagen import File # type: ignore[attr-defined] public API

#import schemas for type-safty and structured data
from schemas.music_schema import RenameReport, RenamedTrack, SkippedTrack


# ---------------- Normalize Tag Values ------------------
def _first_or_none(value):
    """Mutagen can return a list; pick first value or None."""
    if isinstance(value, list) and value: #if empty list
        return value[0]                   #return first item
    return value if value else None       #return value or None if empty


# ---------------- Get Tags with Fallback ------------------
def read_id3_artist_title(path: str):
    """
    This tries to read 'artist' and 'title' tags from an MP3 file.
    Returns (artist, title) or (None, None) if unavailable.
    """
    try:
        audio = EasyID3(path)                       # fast path for ID3-tagged MP3s
        artist = _first_or_none(audio.get("artist"))# may be list → normalize
        title  = _first_or_none(audio.get("title"))
        return artist, title
    except Exception:
        # If EasyID3 fails (no ID3, weird file), use generic parser
        try:
            mf = File(path, easy=True)              # generic loader with 'easy' tag map
            if mf is None or not getattr(mf, "tags", None):
                return None, None                   # no tags at all
            artist = _first_or_none(mf.tags.get("artist"))
            title  = _first_or_none(mf.tags.get("title"))
            return artist, title
        except Exception:
            return None, None  # unreadable or untagged
        
