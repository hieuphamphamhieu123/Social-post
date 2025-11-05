"""
Final restart script with updated formula
"""
import subprocess
import time
import requests
import sys
import os

def kill_python():
    """Kill all python processes"""
    print("[1/4] Stopping all Python processes...")
    try:
        if sys.platform == 'win32':
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe'],
                         stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        else:
            subprocess.run(['pkill', '-f', 'python'],
                         stderr=subprocess.DEVNULL)
        print("   All Python processes stopped")
    except:
        print("   No processes to stop")
    time.sleep(3)

def start_api():
    """Start API server"""
    print("\n[2/4] Starting API with new formula...")
    api_dir = os.path.join(os.path.dirname(__file__), 'ai_market_analyzer')

    if sys.platform == 'win32':
        subprocess.Popen(
            ['cmd', '/c', 'start', 'AI Market API - FINAL', 'cmd', '/k', 'python', 'main.py'],
            cwd=api_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        subprocess.Popen(['python', 'main.py'], cwd=api_dir)

    print("   API starting in new window...")
    print("\n[3/4] Waiting 10 seconds for initialization...")
    for i in range(10, 0, -1):
        print(f"   {i}...", end='\r')
        time.sleep(1)
    print("   Ready!   ")

def test_updates():
    """Test if updates are working"""
    print("\n[4/4] Testing market range updates...")
    print("   Fetching 5 samples, 1 second apart:\n")

    API_URL = "http://127.0.0.1:8000"
    prev_range = None
    changes = 0

    for i in range(5):
        try:
            response = requests.get(f"{API_URL}/market-range/simple", timeout=5)
            if response.status_code == 200:
                data = response.json()
                current_range = data['market_range']

                change_info = ""
                if prev_range is not None:
                    diff = current_range - prev_range
                    if abs(diff) > 1:
                        changes += 1
                        change_info = f" [CHANGE: {diff:+.0f}]"
                    else:
                        change_info = " [STATIC]"

                print(f"   Sample {i+1}/5: {current_range:.0f}{change_info}")
                prev_range = current_range
            else:
                print(f"   Sample {i+1}/5: ERROR {response.status_code}")
        except Exception as e:
            print(f"   Sample {i+1}/5: ERROR - {e}")

        if i < 4:
            time.sleep(1)

    return changes

def main():
    print("=" * 80)
    print("FINAL RESTART - Updated Formula with Variance")
    print("=" * 80)
    print()

    kill_python()
    start_api()
    changes = test_updates()

    print("\n" + "=" * 80)
    if changes >= 3:
        print(f"SUCCESS! Market range is updating! ({changes}/4 changes detected)")
        print("\nThe system is working correctly!")
        print("You can now use it in MT5.")
    else:
        print(f"WARNING: Only {changes}/4 changes detected")
        print("Check the Python console for errors")
    print("=" * 80)

if __name__ == "__main__":
    main()
