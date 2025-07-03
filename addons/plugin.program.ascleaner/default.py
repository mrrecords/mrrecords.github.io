import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
import os
import shutil

addon = xbmcaddon.Addon()
HOME = xbmcvfs.translatePath("special://home")
TEMP = xbmcvfs.translatePath("special://temp")
CACHE = xbmcvfs.translatePath("special://cache")
THUMBS = xbmcvfs.translatePath("special://userdata/Thumbnails")
PACKAGES = os.path.join(HOME, "addons", "packages")
ADDON_DATA = xbmcvfs.translatePath("special://userdata/addon_data")
ADDONS = xbmcvfs.translatePath("special://home/addons")

def count_files(path):
    count = 0
    for dirpath, _, filenames in os.walk(path):
        count += len(filenames)
    return count

def get_size(path):
    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            try:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
            except:
                pass
    return round(total / (1024 * 1024), 2)

    total = 0
    for dirpath, _, filenames in os.walk(path):
        for f in filenames:
            try:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
            except:
                pass
    return round(total / (1024 * 1024), 2)

def delete_folder_contents(path, protect_files=None):
    try:
        if not xbmcvfs.exists(path):
            return
        for root, dirs, files in os.walk(path):
            for file in files:
                file_path = os.path.join(root, file)
                if protect_files and os.path.basename(file_path) in protect_files:
                    continue
                try:
                    os.remove(file_path)
                except:
                    pass
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    shutil.rmtree(dir_path, ignore_errors=True)
                except:
                    pass
    except:
        pass

def clean_thumbnails_safely():
    try:
        import sqlite3
        db_path = os.path.join(xbmcvfs.translatePath("special://userdata/Database"), "Textures13.db")
        used_files = set()
        if os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT cachedurl FROM texture")
            for row in cursor.fetchall():
                if row and row[0]:
                    used_files.add(os.path.basename(row[0]))
            conn.close()

        for folder in os.listdir(THUMBS):
            folder_path = os.path.join(THUMBS, folder)
            if folder.lower() in "abcdefghijklmnopqrstuvwxyz0123456789" and os.path.isdir(folder_path):
                for dirpath, _, filenames in os.walk(folder_path):
                    for filename in filenames:
                        if filename not in used_files:
                            try:
                                os.remove(os.path.join(dirpath, filename))
                            except:
                                pass
    except:
        pass


def get_installed_addons():
    return set([f for f in os.listdir(ADDONS) if os.path.isdir(os.path.join(ADDONS, f))])

def summarize_sizes_with_counts():
    sizes = {}
    if addon.getSettingBool("clean_cache"):
        sizes["Cache"] = (get_size(CACHE), count_files(CACHE))
    if addon.getSettingBool("clean_packages"):
        sizes["Packages"] = (get_size(PACKAGES), count_files(PACKAGES))
    if addon.getSettingBool("clean_thumbs"):
        sizes["Thumbnails"] = (get_size(THUMBS), count_files(THUMBS))
    if addon.getSettingBool("clean_addon_data") or addon.getSettingBool("clean_orphaned_addon_data"):
        total_size, total_files = 0, 0
        installed = get_installed_addons()
        for d in os.listdir(ADDON_DATA):
            if d != "plugin.program.ascleaner":
                full_path = os.path.join(ADDON_DATA, d)
                if addon.getSettingBool("clean_addon_data") and d in installed:
                    total_size += get_size(full_path)
                    total_files += count_files(full_path)
                elif addon.getSettingBool("clean_orphaned_addon_data") and d not in installed:
                    total_size += get_size(full_path)
                    total_files += count_files(full_path)
        sizes["Addon Data"] = (round(total_size, 2), total_files)
    return sizes

    sizes = {}
    if addon.getSettingBool("clean_cache"):
        sizes["Cache"] = get_size(CACHE)
    if addon.getSettingBool("clean_packages"):
        sizes["Packages"] = get_size(PACKAGES)
    if addon.getSettingBool("clean_thumbs"):
        sizes["Thumbnails"] = get_size(THUMBS)
    if addon.getSettingBool("clean_addon_data") or addon.getSettingBool("clean_orphaned_addon_data"):
        total = 0
        installed = get_installed_addons()
        for d in os.listdir(ADDON_DATA):
            if d != "plugin.program.ascleaner":
                full_path = os.path.join(ADDON_DATA, d)
                if addon.getSettingBool("clean_addon_data") and d in installed:
                    total += get_size(full_path)
                elif addon.getSettingBool("clean_orphaned_addon_data") and d not in installed:
                    total += get_size(full_path)
        sizes["Addon Data"] = round(total, 2)
    return sizes

def clean_selected():
    installed = get_installed_addons()
    if addon.getSettingBool("clean_cache"):
        delete_folder_contents(CACHE)
    if addon.getSettingBool("clean_packages"):
        delete_folder_contents(PACKAGES)
    if addon.getSettingBool("clean_thumbs"):
        clean_thumbnails_safely()
    if addon.getSettingBool("clean_addon_data") or addon.getSettingBool("clean_orphaned_addon_data"):
        for addon_id in os.listdir(ADDON_DATA):
            if addon_id == "plugin.program.ascleaner":
                continue
            full_path = os.path.join(ADDON_DATA, addon_id)
            if addon.getSettingBool("clean_addon_data") and addon_id in installed:
                delete_folder_contents(full_path)
            elif addon.getSettingBool("clean_orphaned_addon_data") and addon_id not in installed:
                delete_folder_contents(full_path)

def show_summary(before, after):
    lines = []
    for key in before:
        lines.append(f"{key}: {before[key][0]:.2f} MB ({before[key][1]} files) → {after.get(key, (0.0, 0))[0]:.2f} MB ({after.get(key, (0.0, 0))[1]} files)")
    xbmcgui.Dialog().ok("AS Cleaner - Results", "\n".join(lines))

def run():
    sizes_before = summarize_sizes_with_counts()
    if not sizes_before:
        xbmcgui.Dialog().ok("AS Cleaner", "No cleaning options enabled.")
        return

    summary_lines = [f"{k}: {v[0]:.2f} MB ({v[1]} files)" for k, v in sizes_before.items()]
    choice = xbmcgui.Dialog().yesno("AS Cleaner - Preview", "\n".join(summary_lines), nolabel="Exit", yeslabel="Clear All")
    if choice:
        clean_selected()
        sizes_after = summarize_sizes_with_counts()
        show_summary(sizes_before, sizes_after)

run()
