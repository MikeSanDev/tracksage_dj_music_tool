# Pydantic is used to define and validate structured data
from pydantic import BaseModel
# List is imported to let us say "this field is a list of X objects"
from typing import List

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
