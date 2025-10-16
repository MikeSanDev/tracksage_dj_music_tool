import os
from datetime import datetime
#re: regex for sanitizing filenames
import re
#typing: for type hints
from typing import Any, Optional, Union
#mutagen: library for reading MP3 ID3 Tags
from mutagen.easyid3 import EasyID3
from mutagen import File # type: ignore[attr-defined] public API
from tools.ai_suggester import suggest_name_with_ai

#import schemas for type-safty and structured data
from schemas.music_schema import RenameReport, RenamedTrack, SkippedTrack


# ---------------- Normalize Tag Values ------------------
def _first_or_none(value: Optional[Union[str, list[Any]]]) -> Optional[str]:  #the optional is shorthand for Union[str, None] - either return a string or none
    """
    Mutagen can return a string, a list of strings, or None.
    This function makes sure we always get a single string or None.
    """
    # If it's a list and not empty, return its first element
    if isinstance(value, list) and value:
        return str(value[0])
    # If it's already a string, return it as-is
    if isinstance(value, str):
        return value
    # Otherwise, return None (no valid value)
    return None

# ---------------- Get Tags with Fallback ------------------
def read_id3_artist_title(path: str):
    """
    This tries to read 'artist' and 'title' tags from an MP3 file.
    Returns (artist, title) or (None, None) if unavailable.
    """
    try: 
        audio = EasyID3(path) # fast path for ID3-tagged MP3s
        artist = _first_or_none(audio.get("artist")) #reads tag values
        title  = _first_or_none(audio.get("title"))
        return artist, title #returns tuple of strings or none
    except Exception: #fallback for non-MP3 or non-ID3 files
        # If EasyID3 fails (no ID3, weird file), we use this generic parser
        try:
            mf = File(path, easy=True)  #mutagen's generic file parser - checks for any tags
            if mf is None or not getattr(mf, "tags", None):
                return None, None                   # no tags at all
            artist = _first_or_none(mf.tags.get("artist"))
            title  = _first_or_none(mf.tags.get("title"))
            return artist, title
        except Exception:
            return None, None  # unreadable or untagged

"""     
-mf = File(path, easy=True)  #mutagen's generic file parser - checks for any tags
-it looks the file, guesses the format (Mp3, FLAC, etc.), and returns a file object
-if mutagen can't identify the file type, it returns None
-getattr(mf, "tags", None) checks if the 'tags' attribute exists in the file object, 
-if not return None instead of crashing
-Some MP3s do not have EasyID3 tags but do have generic tags.
-Some are not MP3s at all (you could accidentally scan FLAC/OGG/WAV), but with File(..., easy=True), you still get artist/title.
"""  


# ---------------- Sanitize Filename Component ----------------
INVALID_CHARS = r'<>:"/\\|?*'  # forbidden in Windows filenames


def sanitize_component(text: str) -> str:
    """
    Make a filename component safe and clean:
    - Replace forbidden characters with '-'
    - Collapse multiple spaces
    - Strip trailing spaces/dots (Windows quirk)
    - Normalize casing (ALL CAPS -> Title Case)
    """
    if not text:  # catches None, "", or anything falsy
        return ""

    # Replace forbidden characters (like < > : " / \ | ? *)
    text = re.sub(f"[{re.escape(INVALID_CHARS)}]", "-", text)

    # Collapse multiple spaces and trim leading/trailing whitespace
    text = re.sub(r"\s+", " ", text).strip()

    # Normalize casing: convert ALL CAPS → Title Case
    if text.isupper():
        text = text.title()

    # Strip any trailing dots or spaces (Windows quirk)
    return text.rstrip(" .")

# ---------------- Ensure Unique Path ----------------
def uniquify_path(target_path: str) -> str:
    """
    If a file already exists at target_path, append ' (1)', ' (2)', ... until unique.
    """
    if not os.path.exists(target_path):
        return target_path
    base, ext = os.path.splitext(target_path)
    i = 1
    while True:
        candidate = f"{base} ({i}){ext}"
        if not os.path.exists(candidate):
            return candidate
        i += 1

# ---------------- Rename Tracks ------------------
def rename_tracks(folder: str, pattern: str = "{artist} - {title}", test_run: bool = False) -> RenameReport:
    """
    Rename all .mp3 files in a folder using ID3 tags.
    - pattern: controls the naming scheme (default "Artist - Title")
    - test_run: if True, show what *would* happen but does not rename
    Returns: RenameReport with renamed_tracks + skipped_tracks
    """

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    renamed, skipped = [], []  # collect results

    # Walk the folder tree
    for root, _, files in os.walk(folder):
        for file in files:
            if not file.lower().endswith(".mp3"):
                continue  # skip non-mp3 files

            src_path = os.path.join(root, file)

            # 1) Read tags (artist + title) - If tags are missing, try AI fallback instead of skipping
            artist, title = read_id3_artist_title(src_path)
            if not artist or not title: 
                ai_suggestion = suggest_name_with_ai(file, artist_hint=artist, title_hint=title)
                if ai_suggestion:
                    dst_path = os.path.join(root, ai_suggestion)
                    dst_path = uniquify_path(dst_path)
                    if not test_run:
                        os.rename(src_path, dst_path)
                    renamed.append(RenamedTrack(
                        original=src_path,
                        new_path=dst_path,
                        artist=artist or "AI Suggested",
                        title=title or "AI Suggested"
                    ))
                    continue
                else:
                    skipped.append(SkippedTrack(original=src_path, reason="missing tags + AI failed"))
                    continue

            # 2) Sanitize & build new name
            safe_artist = sanitize_component(str(artist or "")) #handles None by converting to empty string
            safe_title = sanitize_component(str(title or ""))
            new_name = pattern.format(artist=safe_artist, title=safe_title).strip()
            if not new_name:
                skipped.append(SkippedTrack(original=src_path, reason="empty name after sanitize"))
                continue
            if not new_name.lower().endswith(".mp3"):
                new_name += ".mp3"

            dst_path = os.path.join(root, new_name)

            # 3) Skip if already matches
            if os.path.normcase(src_path) == os.path.normcase(dst_path):
                skipped.append(SkippedTrack(original=src_path, reason="already matches target name"))
                continue

            # 4) Ensure uniqueness
            dst_path = uniquify_path(dst_path)

            # 5) Rename (unless test_run)
            if not test_run:
                os.rename(src_path, dst_path)

            renamed.append(RenamedTrack(
                original=src_path,
                new_path=dst_path,
                artist=str(artist) if artist is not None else "",
                title=str(title) if title is not None else ""
            ))

    return RenameReport(
        folder=folder,
        timestamp=timestamp,
        renamed_tracks=renamed,     # matches the schema
        skipped_tracks=skipped    
    )

# ---------------- Save Logs: JSON + TXT ------------------
def save_rename_log(report: RenameReport, log_dir: str = "logs"):
    """
    Save the RenameReport to disk in two formats:
      1) JSON  - machine-readable, good for automation/AI training
      2) TXT   - human-readable audit trail
    Returns dict of paths so caller can print or use them.
    """
    os.makedirs(log_dir, exist_ok=True)

    base_name = f"renamed_{report.timestamp}"
    json_path = os.path.join(log_dir, f"{base_name}.json")
    txt_path  = os.path.join(log_dir, f"{base_name}.txt")

    # JSON log
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(report.model_dump_json(indent=2))

    # TXT log
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"Rename Report\n")
        f.write(f"Folder   : {report.folder}\n")
        f.write(f"Run      : {report.timestamp}\n")
        f.write(f"Renamed  : {len(report.renamed_tracks)} file(s)\n")
        f.write(f"Skipped  : {len(report.skipped_tracks)} file(s)\n")
        f.write("-" * 60 + "\n\n")

        # Log renamed files
        for i, entry in enumerate(report.renamed_tracks, start=1):
            f.write(f"[{i}] {entry.original}\n")
            f.write(f"    → {entry.new_path}\n")
            f.write(f"    Tags: {entry.artist} - {entry.title}\n\n")

        # Log skipped files
        if report.skipped_tracks:
            f.write("Skipped files:\n")
            for i, entry in enumerate(report.skipped_tracks, start=1):
                f.write(f"[{i}] {entry.original} (Reason: {entry.reason})\n")
        else:
            f.write("No files were skipped.\n")

    return {"json": json_path, "txt": txt_path}