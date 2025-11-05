"""
Quick script to restart API and verify it's working
"""
import subprocess
import time
import requests
import sys
import os

API_URL = "http://127.0.0.1:8000"

def main():
    print("=" * 80)
    print("API Restart and Verification Script")
    print("=" * 80)

    # Kill existing Python processes running uvicorn
    print("\n[1/4] Stopping existing API processes...")
    try:
        if sys.platform == 'win32':
            # Windows
            subprocess.run(['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq AI Market API*'],
                         stderr=subprocess.DEVNULL)
        else:
            # Linux/Mac
            subprocess.run(['pkill', '-f', 'uvicorn.*market_api'],
                         stderr=subprocess.DEVNULL)
        print("   Processes stopped (if any were running)")
    except Exception as e:
        print(f"   Warning: {e}")

    time.sleep(2)

    # Start new API process
    print("\n[2/4] Starting API server...")
    api_dir = os.path.join(os.path.dirname(__file__), 'ai_market_analyzer')

    if sys.platform == 'win32':
        # Windows - start in new window
        subprocess.Popen(
            ['cmd', '/c', 'start', 'AI Market API', 'cmd', '/k', 'python', 'main.py'],
            cwd=api_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
    else:
        # Linux/Mac - background process
        subprocess.Popen(
            ['python', 'main.py'],
            cwd=api_dir,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    print("   API starting... waiting 10 seconds for initialization")

    # Wait for API to start
    for i in range(10, 0, -1):
        print(f"   {i}...", end='\r')
        time.sleep(1)
    print("   Ready!   ")

    # Verify API is running
    print("\n[3/4] Verifying API health...")
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   [OK] API is healthy!")
            data = response.json()
            print(f"   Status: {data['status']}")
            print(f"   Collecting: {data['is_collecting']}")
        else:
            print(f"   [ERROR] Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   [ERROR] Cannot connect to API: {e}")
        print("   Please start API manually: cd ai_market_analyzer && python main.py")
        return False

    # Test market range
    print("\n[4/4] Testing market range updates...")
    print("   Fetching 3 samples, 2 seconds apart...\n")

    prev_range = None
    changes = 0

    for i in range(3):
        try:
            response = requests.get(f"{API_URL}/market-range/simple", timeout=5)
            if response.status_code == 200:
                data = response.json()
                current_range = data['market_range']

                change_info = ""
                if prev_range is not None:
                    diff = current_range - prev_range
                    if abs(diff) > 0.01:
                        changes += 1
                        change_info = f" [CHANGE: {diff:+.0f}]"
                    else:
                        change_info = " [STATIC]"

                print(f"   Sample {i+1}/3: Range = {current_range:.0f}{change_info}")
                prev_range = current_range
            else:
                print(f"   Sample {i+1}/3: ERROR {response.status_code}")
        except Exception as e:
            print(f"   Sample {i+1}/3: ERROR - {e}")

        if i < 2:
            time.sleep(2)

    # Results
    print("\n" + "=" * 80)
    if changes > 0:
        print(f"[SUCCESS] Market range is updating! ({changes}/2 changes detected)")
        print("\nYou can now use the AI Market Range in MT5!")
    else:
        print("[WARNING] Market range not changing")
        print("Check Python console for prediction_loop logs")
    print("=" * 80)

    return changes > 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
