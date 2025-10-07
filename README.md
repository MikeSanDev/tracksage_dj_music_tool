# 🎵 SAGE 2.5 Music Agent  

SAGE 2.5 is a local-first **music file management agent** that helps you:  

- ✅ **Detect and remove duplicate MP3s** (using file hashing + smart filename heuristics)  
- ✅ **Rename MP3s** based on their ID3 tags (`Artist - Title`)  
- 📂 **Log all operations** into machine-readable JSON and human-readable TXT for transparency  
- 🛡️ **Safe Trash system** – no files are permanently deleted; duplicates are moved into `trash/` with a timestamp  

This is a personal utility project designed for learning about agents, automation, and structured data while solving a real-world pain point: keeping large music libraries clean.  

---

## ⚙️ Features  

### 1. Duplicate Detector  
- Scans a folder (recursively) for `.mp3` files.  
- Computes an **MD5 hash** of file contents (so even renamed copies are caught).  
- Uses filename heuristics to decide which file to **keep** (e.g., prefers clean names like `Track.mp3` over `Track - Copy (1).mp3`).  
- Moves duplicates into `trash/<timestamp>/` for review.  
- Logs all results to both JSON and TXT.
DEMO:
![sage_duplicate](https://github.com/user-attachments/assets/ae164190-c40b-4c74-8ec6-28b45f81410a)


### 2. Renamer  
- Reads ID3 tags (`artist`, `title`) using [`mutagen`](https://mutagen.readthedocs.io/).  
- Renames files into the format:

  - Sanitizes names to remove illegal characters (`<>:"/\|?*`).  
  - Ensures uniqueness (`Song.mp3`, `Song (1).mp3`, etc.).  
  - Has a **Dry Run mode** to preview changes before committing.  
  - Logs renamed/skipped files into JSON and TXT.  
DEMO:
![sage_rename](https://github.com/user-attachments/assets/a2fe9bd9-7a5e-40dd-a76f-a65300f84adf)

---

## 📂 Project Structure  
```sage2.5_music_agent/
├── agents/ # (future agents can live here)
├── logs/ # JSON + TXT logs saved here
├── schemas/
│ └── music_schema.py # Pydantic models for structured reports
├── tools/
│ ├── music_duplicates.py # Duplicate detection logic
│ └── music_rename.py # Track renaming logic
├── trash/ # Duplicates moved here with timestamps
├── main.py # CLI entrypoint
├── requirements.txt # Main dependencies
└── venv/ # Local virtual environment (gitignored)
```
1. **Clone the repo**
   ```
   git clone https://github.com/yourusername/sage2.5_music_agent.git
   cd sage2.5_music_agent
   
2. **Create a virtual environment**
```python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

3. **Install dependencies**
```
pip install -r requirements.txt
```

5. **Run the app**
```
python main.py
```

🖥️ Usage

When you run python main.py, you’ll see a menu:
```
🎵 SAGE 2.5 Music Agent 🎵
Choose a tool:
1) Detect duplicates
2) Rename tracks
3) Exit
```
### 1. Detect Duplicates
- Enter the path to the folder you want to scan.  
- Duplicates will be moved to `trash/<timestamp>/`.  
- Logs saved under:
  - `logs/duplicates_<timestamp>.json`
  - `logs/duplicates_<timestamp>.txt`

### 2. Rename Tracks
- Enter the folder path to scan for MP3 renames.  
- Choose Dry Run:
  - `y` → preview changes
  - `n` → apply changes  
- Renamed files will overwrite their filenames.  
- Logs saved under:
  - `logs/renamed_<timestamp>.json`
  - `logs/renamed_<timestamp>.txt`
  - 
📑 Example Logs
- Checkout Example logs in the logs_example.txt file.

**This is a personal learning project. Free to use, modify, or extend.**
</br>
👷‍♂️**This project is still under construction.**👷‍♂️
