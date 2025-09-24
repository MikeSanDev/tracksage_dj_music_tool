from tools.music_duplicates import find_duplicates, save_duplicate_log
# from tools.music_rename import rename_tracks, save_rename_log

if __name__ == "__main__":
    folder = input("Enter the folder path to scan for duplicates: ")
    report = find_duplicates(folder)              # run duplicate detector
    paths = save_duplicate_log(report)            # save JSON + TXT logs
    print(f"✅ Duplicates processed. Logs saved at:\n- {paths['json']}\n- {paths['txt']}")