"""
Clear Python cache and restart API server
"""
import os
import shutil
import subprocess
import time
import sys

def clear_pycache(directory):
    """Recursively clear __pycache__ directories"""
    count = 0
    for root, dirs, files in os.walk(directory):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                count += 1
                print(f"   Removed: {cache_dir}")
            except Exception as e:
                print(f"   Error removing {cache_dir}: {e}")

        for file in files:
            if file.endswith('.pyc'):
                file_path = os.path.join(root, file)
                try:
                    os.remove(file_path)
                    count += 1
                    print(f"   Removed: {file_path}")
                except Exception as e:
                    print(f"   Error removing {file_path}: {e}")

    return count

def main():
    print("=" * 80)
    print("Clear Cache and Restart API")
    print("=" * 80)

    # Clear cache
    print("\n[1/3] Clearing Python bytecode cache...")
    api_dir = os.path.join(os.path.dirname(__file__), 'ai_market_analyzer')
    count = clear_pycache(api_dir)
    print(f"   Removed {count} cache files/directories")

    # Kill processes
    print("\n[2/3] Stopping existing API processes...")
    try:
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'],
                         stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        else:
            subprocess.run(['pkill', '-f', 'python.*main.py'],
                         stderr=subprocess.DEVNULL)
        print("   Processes stopped")
    except:
        print("   No processes to stop")

    time.sleep(2)

    # Start API
    print("\n[3/3] Starting fresh API server...")
    if sys.platform == 'win32':
        subprocess.Popen(
            ['cmd', '/c', 'start', 'AI Market API - FRESH', 'cmd', '/k', 'python', 'main.py'],
            cwd=api_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        subprocess.Popen(['python', 'main.py'], cwd=api_dir)

    print("   API starting in new window...")
    print("\n" + "=" * 80)
    print("DONE! API is starting with fresh code (no cache)")
    print("Wait 10 seconds, then run: python test_market_range_updates.py")
    print("=" * 80)

if __name__ == "__main__":
    main()
