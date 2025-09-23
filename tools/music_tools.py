# OS lets us walk through directories and join file paths
import os
# Hashlib lets us create a hash of a file's contents (MD5)
import hashlib
# Shutil lets us move files
import shutil
# Datetime lets us get the current date and time
from datetime import datetime
#Import our schemas to define the output structure
from schemas.music_schema import DuplicateEntry, DuplicateReport
import json  # standard lib: reading/writing JSON

# ---------------- Helper: File Hashing ----------------
'''
This function opens the file in binary mode and reads it in chunks to avoid memory issues with large files.
it then feeds the chunks into the hash function to return a unique hash value representing 
the file's contents.'''

#Chunksize for reading bigger files (MP3) in pieces vs block_size 
def get_file_hash(path, chunk_size=8192):
    """Compute MD5 hash for a file by reading it in chunks (safe for large files)."""
    h = hashlib.md5()  #creates hash object
    with open(path, 'rb') as f:  # open in binary mode
        #creates lamda function to read file in chunks and loops until returns with sentinel value of b'' or 'empty bytes'
        for chunk in iter(lambda: f.read(chunk_size), b''):
            h.update(chunk) #Feeds chunk to hash object
            #.hexdigest() returns the hash as a hexadecimal string | example output: '5d41402abc4b2a76b9719d911017c592' for 'hello'
    return h.hexdigest()

# *Sentinel value* = a marker that means “stop” (in our case b'' = end of file).

# ---------------- Find and Move Duplicates Function ----------------

def find_duplicates(folder: str, trash_dir: str = "trash") -> DuplicateReport:
    """
    -Scan a folder for duplicate MP3s and move them to Trash.
    -Returns a structured DuplicateReport (defined in schemas/music_schema.py).
    """
    # Dictionary to store "file hash → original file path" if the same hash appears again, it's a duplicate
    seen = {}
    # List to collect DuplicateEntry objects for each duplicate found - each item is will be a DuplicateEntry object.
    duplicates_removed = []

    # Every run creates a fresh subfolder inside trash/ with a timestamp ex. trash/2025-09-16_21-30-00/
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    session_trash = os.path.join(trash_dir, timestamp)
    os.makedirs(session_trash, exist_ok=True)

     # Walk through the folder recursively
    for root, _, files in os.walk(folder): # Walks through every folder and subfolder
        for file in files:
            if file.lower().endswith(".mp3"):  # only checks mp3 files
                # Full file path
                path = os.path.join(root, file)
                # Compute hash of the file - calls the helper(get_file_hash) to return the file's hash
                file_hash = get_file_hash(path)

                # Detect and handle duplicates
                if file_hash in seen: # Duplicate found → move it to Trash
                                    new_path = os.path.join(session_trash, file)
                                    shutil.move(path, new_path) # Physically moves the duplicate file into Trash

                                    # Logs this duplicate as a DuplicateEntry
                                    duplicates_removed.append(
                                        DuplicateEntry(
                                            original=seen[file_hash],   # the "keeper"
                                            duplicate=path,             # the file we’re removing
                                            dupe_moved_to=new_path,     # where it was moved
                                            hash=file_hash              # fingerprint of the file
                                        )
                                    )
                else:
                                    # if first time seeing this file → keep it
                                    seen[file_hash] = path

    # Return a structured report of the operation
    return DuplicateReport(
        folder=folder,
        timestamp=timestamp,
        duplicates_removed=duplicates_removed
    )

# ---------------- Save Logs: JSON + TXT ------------------
# A helper that will save the report to a JSON file and a human-readable TXT file to save_duplicate_log.py
# JSON is great for structured data, TXT is easy for humans to read

def save_duplicate_log(report: DuplicateReport, log_dir: str = "logs"): #report ensures input follows schema, log_dir saves logs in logs/ folder
    """
    Save the DuplicateReport to disk in two formats:
      1) JSON  - machine-readable, great for parsing/automation
      2) TXT   - human-readable audit trail
    Returns dict of paths so caller can print or use them.
    """

    # 1) Checks if log directory exists (create it if missing, ignore if it already exists)
    os.makedirs(log_dir, exist_ok=True)

    # 2) Build consistent file names using the report timestamp
    #    Ex: logs/duplicates_2025-09-16_21-30-00.json
    base_name = f"duplicates_{report.timestamp}"
    json_path = os.path.join(log_dir, f"{base_name}.json")
    txt_path  = os.path.join(log_dir, f"{base_name}.txt")

     # 3) Write JSON log
    #    - .model_dump_json(indent=2) is a Pydantic method that turns the report into JSON
    with open(json_path, "w", encoding="utf-8") as f: # opens file in write mode, creates if not exists
        f.write(report.model_dump_json(indent=2)) # writes the file in JSON format

     # 4) Write human-readable TXT log
    #    - Keep it skimmable: header + one block per duplicate
    with open(txt_path, "w", encoding="utf-8") as f:
        # Header: what folder, when, and a quick count
        f.write(f"Duplicate Report\n")
        f.write(f"Folder   : {report.folder}\n")
        f.write(f"Run      : {report.timestamp}\n")
        f.write(f"Found    : {len(report.duplicates_removed)} duplicate(s)\n")
        f.write("-" * 60 + "\n\n") #prints a line of 60 dashes for separation

     # Body: one section per duplicate moved to Trash, loops through each entry in duplicates_removed list
        for i, entry in enumerate(report.duplicates_removed, start=1): #gives each entry a number starting from 1
            f.write(f"[{i}] HASH     : {entry.hash}\n")
            f.write(f"    ORIGINAL : {entry.original}\n")
            f.write(f"    DUPLICATE: {entry.duplicate}\n")
            f.write(f"    MOVED TO : {entry.dupe_moved_to}\n\n")

          # Friendly note if nothing was found (still useful to have the log!)
        if not report.duplicates_removed:
            f.write("No duplicates were detected in this run.\n")

    # 5) Return paths so the caller can print them or use them further
    return {"json": json_path, "txt": txt_path} 