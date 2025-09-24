# Pydantic is used to define and validate structured data
from pydantic import BaseModel
# List is imported to let us say "this field is a list of X objects"
from typing import List, Optional


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