"""
check_tags.py
-------------
Simple utility to read and print MP3 tags using Mutagen.
"""

import os
from mutagen.easyid3 import EasyID3
from mutagen import File  # fallback for non-ID3 files # type: ignore[attr-defined]


def check_tags(folder: str):
    """
    Scan a folder for .mp3 files and print their Artist and Title tags.

    Steps:
      1. Walk through all files in the folder.
      2. For each .mp3, try to read ID3 tags with EasyID3.
      3. If tags missing, try generic Mutagen parser.
      4. Print results to the console.
    """

    print(f"\n📂 Scanning folder: {folder}")

    for root, _, files in os.walk(folder):
        for file in files:
            if not file.lower().endswith(".mp3"):
                continue  # skip non-MP3 files

            path = os.path.join(root, file)
            print(f"\n🎵 {file}")
            print("-" * 40)

            try:
                # Try to read standard ID3 tags (artist/title/album)
                audio = EasyID3(path)
                artist_tags = audio.get("artist")
                title_tags = audio.get("title")

                artist = ", ".join(artist_tags) if artist_tags else "<no artist>"
                title = ", ".join(title_tags) if title_tags else "<no title>"
                print(f"Artist : {artist}")
                print(f"Title  : {title}")

            except Exception:
                # Fallback for files missing EasyID3 headers
                mf = File(path, easy=True)
                if mf and mf.tags:
                    artist_tags = mf.tags.get("artist")
                    title_tags = mf.tags.get("title")

                    artist = ", ".join(artist_tags) if artist_tags else "<no artist>"
                    title = ", ".join(title_tags) if title_tags else "<no title>"
                    print(f"Artist : {artist}")
                    print(f"Title  : {title}")
                else:
                    print("⚠️  No readable tags found.")

    print("\n✅ Tag inspection complete.\n")