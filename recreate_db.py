# recreate_db.py
import os
import shutil
import time
from datetime import datetime
from app import app   # ensure this import doesn't auto-start the server (your app should only create the app object)
from models import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data.sqlite")

def try_copy_with_retries(src, dst, retries=5, wait=1.0):
    for attempt in range(1, retries + 1):
        try:
            shutil.copy2(src, dst)
            return True
        except PermissionError:
            print(f"[{attempt}/{retries}] PermissionError while copying {src} -> {dst}. File may be locked. Retrying in {wait}s...")
            time.sleep(wait)
    return False

def try_remove_with_retries(path, retries=5, wait=1.0):
    for attempt in range(1, retries + 1):
        try:
            os.remove(path)
            return True
        except PermissionError:
            print(f"[{attempt}/{retries}] PermissionError while removing {path}. Retrying in {wait}s...")
            time.sleep(wait)
        except FileNotFoundError:
            return True
    return False

def backup_db(path):
    if not os.path.exists(path):
        print("No existing DB to back up.")
        return None

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = path + f".bak.{ts}"
    print(f"Attempting to copy {path} -> {bak} (safe copy)...")
    ok = try_copy_with_retries(path, bak, retries=6, wait=1.0)
    if not ok:
        print("Could not copy the DB file (likely locked).")
        print("Please: stop the Flask server, close DB tools, restart Spyder kernel, then re-run this script.")
        raise SystemExit(1)
    # try to remove original (optional)
    removed = try_remove_with_retries(path, retries=6, wait=1.0)
    if removed:
        print("Original DB removed after backup.")
    else:
        print("Original DB could not be removed after backup (left in place).")
    return bak

def recreate():
    with app.app_context():
        try:
            print("Dropping all tables (if any)...")
            db.drop_all()
        except Exception as e:
            print("drop_all() error (can be ignored if starting fresh):", e)
        print("Creating all tables from models...")
        db.create_all()
        print("Done. New DB created at:", DB_PATH)

if __name__ == "__main__":
    # Attempt backup first (copy). If file locked, script stops and tells you what to do.
    if os.path.exists(DB_PATH):
        backup_db(DB_PATH)
    recreate()
