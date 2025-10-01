# Pydantic is used to define and validate structured data
from pydantic import BaseModel
# List is imported to let us say "this field is a list of X objects"
from typing import List, Optional


# ------------------------ Duplication/Manipulation Models  ------------------------
# We will be using schemas to define the structure of our logs and reports
# This way we can ensure consistency and make it easier to generate and parse these logs

# ---------------- Duplicate Logs ----------------
# Each duplicate will be represented as an object following this structure
class DuplicateEntry(BaseModel):
    original: str      # the file we keep (the first copy found)
    duplicate: str     # the file detected as a duplicate
    dupe_moved_to: str # the new path where the duplicate is moved (Trash folder)
    hash: str          # the MD5 hash of the file contents (used to detect duplicates)

# The full report of one duplicate-scan session
class DuplicateReport(BaseModel):
    folder: str                   # which folder we scanned
    timestamp: str                # when the scan happened (YYYY-MM-DD_HH-MM-SS)
    duplicates_removed: List[DuplicateEntry]  # all the duplicates we found and moved


# ---------------- Track Manipulation ----------------
# Each renamed track will be represented as an object following this structure
class RenamedTrack(BaseModel):
    original: str        # original full path
    new_path: str        # final full path after rename
    artist: str          # ID3 artist used
    title: str           # ID3 title used

# Skipped tracks (not renamed) will be represented like this
class SkippedTrack(BaseModel):
    original: str        # original full path
    reason: str          # reason it was skipped (e.g. missing tags)

# The full report of one rename session
class RenameReport(BaseModel):
    folder: str                     # which folder we scanned
    timestamp: str                  # when the operation happened (YYYY-MM-DD_HH-MM-SS)
    renamed_tracks: List[RenamedTrack]  # all the tracks we successfully renamed
    skipped_tracks: List[SkippedTrack]   # all the tracks we skipped and why





# ------------------------ AI Schema Models ------------------------
# These models capture the structure of AI suggestions and decisions made during processing
# They help log what the AI recommended and what actions were taken.

# ---------------- AI Suggestions ----------------
# Each AI suggestion will be represented as an object following this structure
class AISuggestion(BaseModel):
    file: str             # the file path we analyzed
    current_name: str     # existing filename
    ai_suggested: str     # AI's suggested rename (e.g. "Daft Punk - Face to Face.mp3")
    accepted: bool        # whether we applied it or not
    reason: Optional[str] # optional note (e.g. "tags missing, AI filled in")
    

# ---------------- Unified Session Report ----------------
# This combines duplication, renaming, and AI suggestions into one session report
class SessionReport(BaseModel):
    folder: str
    timestamp: str
    duplicates: Optional[DuplicateReport] = None # one of these can be None if that operation wasn't performed
    renames: Optional[RenameReport] = None # one of these can be None if that operation wasn't performed
    ai_suggestions: List[AISuggestion] = [] # all AI suggestions made during this session