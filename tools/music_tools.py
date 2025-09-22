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


# ---------------- Helper: File Hashing ----------------
'''This function opens the file in binary mode and reads it in chunks to avoid memory issues with large files.
it then feeds the chunks into the hash function to return a unique hash value representing the file's contents.'''

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

# ---------------- Main Function: Find and Move Duplicates ----------------

def find_duplicates(folder: str, trash_dir: str = "trash") -> DuplicateReport:
    """
    Scan a folder for duplicate MP3s and move them to Trash.
    Returns a structured DuplicateReport (defined in schemas/music_schema.py).
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