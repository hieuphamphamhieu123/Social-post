"""
Quick 5-second test to verify market range updates
"""
import requests
import time

API_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("Quick Market Range Test (5 samples)")
print("=" * 60)

try:
    # Health check
    r = requests.get(f"{API_URL}/health", timeout=2)
    if r.status_code != 200:
        print("[ERROR] API not healthy!")
        exit(1)
    print("[OK] API is running\n")
except:
    print("[ERROR] Cannot connect to API!")
    print("Please start API: cd ai_market_analyzer && python main.py")
    exit(1)

# Get 5 samples
prev = None
changes = 0

for i in range(5):
    try:
        r = requests.get(f"{API_URL}/market-range/simple", timeout=2)
        if r.status_code == 200:
            val = r.json()['market_range']

            if prev is not None:
                diff = val - prev
                if abs(diff) > 1:
                    changes += 1
                    print(f"  {i+1}. {val:.0f}  [{diff:+.0f}] CHANGED")
                else:
                    print(f"  {i+1}. {val:.0f}  [STATIC]")
            else:
                print(f"  {i+1}. {val:.0f}")

            prev = val
        else:
            print(f"  {i+1}. ERROR")
    except Exception as e:
        print(f"  {i+1}. ERROR: {e}")

    if i < 4:
        time.sleep(1)

print()
print("=" * 60)
if changes >= 3:
    print(f"SUCCESS! Detected {changes}/4 changes")
    print("Market range is updating correctly!")
else:
    print(f"FAILED! Only {changes}/4 changes")
    print("Please restart API and try again")
print("=" * 60)
