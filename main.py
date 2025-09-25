from tools.music_duplicates import find_duplicates, save_duplicate_log
from tools.music_rename import rename_tracks

#DOES NOT SAVE LOGS - ONLY SHOWS IN CONSOLE ATM
def main():
    print("\n🎵 SAGE 2.5 Music Agent 🎵")
    print("Choose a tool:")
    print("1) Detect duplicates")
    print("2) Rename tracks")
    print("3) Exit")

    choice = input("\nEnter choice (1/2/3): ").strip()

    if choice == "1":
        folder = input("Enter the folder path to scan for duplicates: ").strip()
        report = find_duplicates(folder)
        paths = save_duplicate_log(report)
        print(f"\n✅ Duplicates processed. Logs saved at:\n- {paths['json']}\n- {paths['txt']}")

    elif choice == "2":
        folder = input("Enter the folder path to scan for renames: ").strip()
        dry_run = input("Dry run? (y/n): ").strip().lower() == "y"
        report = rename_tracks(folder, dry_run=dry_run)
        print(f"\n✅ Renames processed. Report:\n{report}")

    else:
        print("👋 Exiting... Goodbye!")


if __name__ == "__main__":
    main()
    #run python main.py 
    #it will ask for a folder to scan for duplicates
    #make sure the folder format is like this: c:\Users\Michael\Music\Soundcloud Downloads\Interstellar Funk
    #no quotation marks or special characters
    #then it will run the duplicate detector and save the logs

    #when doing renaming, make sure to try dry run to run a test first,
    #then once again without dry run to actually rename the files
