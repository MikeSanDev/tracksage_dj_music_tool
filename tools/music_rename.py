# OS lets us walk through directories and join file paths
import os
from datetime import datetime
#re: regex for sanitizing filenames
import re
#typing: for type hints
from typing import Any, Optional, Union
#mutagen: library for reading MP3 ID3 Tags
from mutagen.easyid3 import EasyID3
#mutagen: library for reading WAV metadata
from mutagen.wave import WAVE  # enables reading basic WAV metadata
from mutagen import File # type: ignore[attr-defined] public API
from tools.ai_suggester import suggest_name_with_ai
from schemas.music_schema import RenameReport, RenamedTrack, SkippedTrack

# ---------------- Console Colors ---------------- 
# these are color codes for outputting colored text in the terminal
GREEN = "\033[92m"   # success
YELLOW = "\033[93m"  # warning / skipped
BLUE = "\033[94m"    # AI rename
RESET = "\033[0m"    # reset to default

# ---------------- Normalize Tag Values ------------------
def _first_or_none(value: Optional[Union[str, list[Any], bytes]]) -> Optional[str]:
    """
    Mutagen can return tag values as a string, list, bytes, or None.
    This helper ensures we always return a single clean string or None.
    """

    # If it's a list and not empty, return its first element as a string
    if isinstance(value, list) and value:
        return str(value[0])

    # If it's already a string, return it directly
    if isinstance(value, str):
        return value

    # If it's a bytes object (common in some WAV metadata), decode safely
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="ignore")
        except Exception:
            return None

    # Otherwise, return None for unsupported types or missing values
    return None

# ---------------- Get Tags with Fallback  ------------------
def read_audio_tags(path: str):
    """
    Reads 'artist' and 'title' tags from MP3 and WAV files.
    Returns (artist, title) or (None, None) if unavailable.
    """

    try:
        # ---------- MP3 PATH ----------
        if path.lower().endswith(".mp3"):
            audio = EasyID3(path)  # Reads standard ID3 metadata from MP3 files

            # Mutagen can return a list, string, or None — so we normalize
            artist_raw = audio.get("artist")
            title_raw = audio.get("title")

            artist = _first_or_none(artist_raw)  # ensure single string or None
            title = _first_or_none(title_raw)
            return artist, title  # returns tuple (artist, title) or (None, None)

        # ---------- WAV PATH ----------
        elif path.lower().endswith(".wav"):
            audio = WAVE(path)  # Mutagen’s WAV parser - reads RIFF chunks from the WAV header
            tags = getattr(audio, "tags", None)  # safely access tag data if it exists

            if not tags:
                return None, None  # WAV files often have no tags (especially DJ exports)

            # WAV files store metadata in INFO chunks using different field names:
            #  - IART = artist name
            #  - INAM = track name (title)
            # If unavailable, we try lowercase equivalents (in case of alternate tag sets)
            artist_raw = tags.get("IART") or tags.get("artist")
            title_raw = tags.get("INAM") or tags.get("title")

            # Normalize to single strings (handles None, list, or bytes)
            artist = _first_or_none(artist_raw)
            title = _first_or_none(title_raw)
            return artist, title

        # ---------- UNSUPPORTED OR OTHER FORMATS ----------
        else:
            return None, None  # skip files that aren't MP3 or WAV

    except Exception:
        # Generic fallback: if anything goes wrong (e.g., unreadable tags, corrupted file),
        # return None for both values so the AI fallback can step in.
        return None, None


"""
- EasyID3(path) → reads ID3v2 tags from MP3 files (standard in most audio apps)
- WAVE(path) → parses RIFF metadata from .wav files; most WAVs don’t include these tags
- getattr(audio, "tags", None) → prevents attribute errors if no tags exist
- Some WAVs only contain “INFO” chunks (IART, INAM) rather than typical ID3 fields
- If tags are missing, we gracefully return (None, None) → triggering AI rename fallback
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

# ---------------- Helper: Check if already correct ----------------
def already_correct_name(file_path: str, artist: str, title: str) -> bool:
    """
    Returns True if the file's current name already matches the clean
    'Artist - Title.mp3' pattern (case-insensitive, ignores extension).
    """
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    expected = f"{artist} - {title}".strip()
    return base_name.lower().strip() == expected.lower().strip()

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

    src_path = os.path.join(root, file) # full path to the *original source file
    dst_path = os.path.join(root, new_name) # full path for the *new destination file
    both paths are set to the same folder - only the filename changes
    """

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    renamed, skipped = [], []  # collect results

    # Walk the folder tree
    for root, _, files in os.walk(folder):
        for file in files:
            if not (file.lower().endswith(".mp3") or file.lower().endswith(".wav")):
                continue  # skip non-mp3 files

            src_path = os.path.join(root, file)

            # 1) Read tags (artist + title) - If tags are missing, try AI fallback instead of skipping
            artist, title = read_audio_tags(src_path)
            if not artist or not title: 
                ai_suggestion = suggest_name_with_ai(file, artist_hint=artist, title_hint=title)
                if ai_suggestion:
                    # Preserve the original file extension (.mp3, .wav, etc.)
                    ext = os.path.splitext(file)[1]
                    ai_suggestion = f"{ai_suggestion}{ext}"

                    dst_path = os.path.join(root, ai_suggestion)
                    dst_path = uniquify_path(dst_path)
                    if not test_run:
                        os.rename(src_path, dst_path)
                    print(f"{BLUE}🤖 AI Rename:{RESET} {os.path.basename(file)} → {os.path.basename(dst_path)}")
                    renamed.append(RenamedTrack(
                        original=src_path,
                        new_path=dst_path,
                        artist=artist or "AI Suggested",
                        title=title or "AI Suggested"
                    ))
                    continue

                else:
                    skipped.append(SkippedTrack(original=src_path, reason="missing tags + AI failed"))
                    print(f"{YELLOW}⚠️ Skipped (missing tags + AI failed):{RESET} {os.path.basename(file)}")
                    continue

            # 2) Sanitize & build new name
            safe_artist = sanitize_component(str(artist or "")) #handles None by converting to empty string
            safe_title = sanitize_component(str(title or ""))
            new_name = pattern.format(artist=safe_artist, title=safe_title).strip()
            if not new_name:
                skipped.append(SkippedTrack(original=src_path, reason="empty name after sanitize"))
                continue

            # Preserve the original file extension (e.g. .mp3, .wav)
            ext = os.path.splitext(file)[1]
            new_name = f"{new_name}{ext}" if not new_name.lower().endswith(ext.lower()) else new_name


            dst_path = os.path.join(root, new_name)

            # 3) Skip if already correctly named
            if already_correct_name(file, safe_artist, safe_title):
                skipped.append(SkippedTrack(original=src_path, reason="already formatted correctly"))
                print(f"{YELLOW}⚠️ Skipped (missing tags + AI failed):{RESET} {os.path.basename(file)}")
                continue

            # 4) Skip if destination file already exists (don’t create duplicates)
            if os.path.exists(dst_path):
                skipped.append(SkippedTrack(original=src_path, reason="target file already exists"))
                continue


            # 5) Rename (unless test_run)
            if not test_run:
                os.rename(src_path, dst_path)
                print(f"{GREEN}✅ Renamed:{RESET} {os.path.basename(file)} → {os.path.basename(dst_path)}")


            renamed.append(RenamedTrack(
                original=src_path,
                new_path=dst_path,
                artist=str(artist) if artist is not None else "",
                title=str(title) if title is not None else ""
            ))

    print("\n" + "-" * 60)
    print(f"{GREEN}✅ Renamed: {len(renamed)}{RESET}")
    print(f"{YELLOW}⚠️ Skipped: {len(skipped)}{RESET}")
    print("-" * 60 + "\n")

    '''
    # prints a summary report to the console
    ------------------------------------------------------------
    ✅ Renamed: 1
    ⚠️ Skipped: 1
    ------------------------------------------------------------
    '''

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