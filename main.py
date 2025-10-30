from tools.check_tags import check_tags
from tools.music_duplicates import find_duplicates, save_duplicate_log
from tools.music_rename import rename_tracks, save_rename_log
from tools.transcribe_audio import transcribe_audio

def main():
    print("\n🎵 SAGE 2.5 Music Agent 🎵")
    print("Choose a tool:")
    print("1) Inspect Tags")
    print("2) Detect Duplicates")
    print("3) Rename Tracks")
    print("4) Transcribe Audio")
    print("5) Exit")

    choice = input("\nWhat would you like to do? (1–5): ").strip()

    # ----- OPTION 1: Inspect Tags -----
    if choice == "1":
        raw_input = input("Enter the folder path to inspect: ").strip()
        folder = raw_input.replace("&", "").replace("'", "").replace('"', "").strip()
        check_tags(folder)
        check_tags(folder)

    # ----- OPTION 2: Detect Duplicates -----
    elif choice == "2":
        raw_input = input("Enter the folder path to scan for duplicates: ").strip()
        folder = raw_input.replace("&", "").replace("'", "").replace('"', "").strip()
        report = find_duplicates(folder)
        report = find_duplicates(folder)
        paths = save_duplicate_log(report)
        print(f"\n✅ Duplicates processed. Logs saved at:\n- {paths['json']}\n- {paths['txt']}")

    # ----- OPTION 3: Rename Tracks -----
    elif choice == "3":
        raw_input = input("Enter the folder path to scan for renames: ").strip()

        # Clean PowerShell drag-drop quirks (handles &, single, and double quotes)
        folder = raw_input
        folder = folder.replace("&", "").replace("'", "").replace('"', "").strip()

        # print(f"[DEBUG] Folder interpreted as: {repr(folder)}")  # for testing folder path issues
        test_run = input("Would you like to run a test (dry run)? (y/n): ").strip().lower() == "y"

        print("\n🔄 Scanning Folder...")
        print("💡 Files with missing tags will automatically use AI to infer names.")

        # The rename_tracks() function already handles both cases internally:
        # - Uses ID3 tags if they exist (local, fast)
        # - Falls back to AI only when tags are missing
        report = rename_tracks(folder, test_run=test_run)
        paths = save_rename_log(report)
        print(f"\n✅ Renames processed. Logs saved at:\n- {paths['json']}\n- {paths['txt']}")

    # ----- OPTION 4: Transcribe Audio (coming soon) -----
    elif choice == "4":
        raw_input = input("Enter the full path of the audio file: ").strip()
        file_path = raw_input.replace("&", "").replace("'", "").replace('"', "").strip()

        summarize_choice = input("Would you like to summarize the transcript after? (y/n): ").strip().lower() == "y"

        print("\n🎙️ Starting transcription...")
        transcribe_audio(file_path, summarize=summarize_choice)

    # ----- OPTION 5: Exit -----
    else:
        print("\n👋 Thank you, goodbye!")


if __name__ == "__main__":
    main()
    #run python main.py 
    #it will ask for a folder to scan for duplicates
    #make sure the folder format is like this: c:\Users\Michael\Music\Soundcloud Downloads\Interstellar Funk
    #no quotation marks or special characters
    #then it will run the duplicate detector and save the logs

    #when doing renaming, make sure to try test run to run a test first,
    #then once again without test run to actually rename the files
