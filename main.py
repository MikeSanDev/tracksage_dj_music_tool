from tools.music_duplicates import find_duplicates, save_duplicate_log
from tools.music_rename import rename_tracks, save_rename_log

def main():
    print("\n🎵 SAGE 2.5 Music Agent 🎵")
    print("Choose a tool:")
    print("1) Detect Duplicates")
    print("2) Rename Tracks")
    print("3) Exit")

    choice = input("\nWhat would you like to do? (1/2/3): ").strip()

    if choice == "1":
        folder = input("Enter the folder path to scan for duplicates: ").strip() #Can drag and drop folder or type directly ex: c:\Users\Music\Playlist\Soundcloud Downloads
        report = find_duplicates(folder)
        paths = save_duplicate_log(report)
        print(f"\n✅ Duplicates processed. Logs saved at:\n- {paths['json']}\n- {paths['txt']}")

    elif choice == "2":
        folder = input("Enter the folder path to scan for renames: ").strip()
        test_run = input("Would you like me to print a test log? (y/n): ").strip().lower() == "y"

        print("\n🔄 Scanning Folder...")
        print("💡 Files with missing tags will automatically use AI to infer names.")

        # The rename_tracks() function already handles both cases internally:
        # - Uses ID3 tags if they exist (local, fast)
        # - Falls back to AI only when tags are missing
        report = rename_tracks(folder, test_run=test_run)
        paths = save_rename_log(report)

    else:
        print("Thank you, Goodbye!")


if __name__ == "__main__":
    main()
    #run python main.py 
    #it will ask for a folder to scan for duplicates
    #make sure the folder format is like this: c:\Users\Michael\Music\Soundcloud Downloads\Interstellar Funk
    #no quotation marks or special characters
    #then it will run the duplicate detector and save the logs

    #when doing renaming, make sure to try test run to run a test first,
    #then once again without test run to actually rename the files
