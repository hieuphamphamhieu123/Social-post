"""
Test script để verify market range updates liên tục
"""
import requests
import time
from datetime import datetime
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

API_URL = "http://127.0.0.1:8000"

def test_continuous_updates():
    """Test xem market range có update liên tục không"""
    print("=" * 80)
    print("Testing Market Range Continuous Updates")
    print("=" * 80)

    # Check health first
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("[OK] API is healthy")
            print(f"   Response: {response.json()}")
        else:
            print(f"[ERROR] API health check failed: {response.status_code}")
            return
    except Exception as e:
        print(f"[ERROR] Cannot connect to API: {e}")
        print(f"   Make sure Python API is running at {API_URL}")
        return

    print("\n" + "=" * 80)
    print("Monitoring Market Range Updates (10 iterations, 1 second interval)")
    print("=" * 80)

    previous_range = None
    changes_detected = 0
    total_iterations = 10

    for i in range(total_iterations):
        try:
            response = requests.get(f"{API_URL}/market-range/simple")

            if response.status_code == 200:
                data = response.json()
                current_range = data['market_range']
                timestamp = data['timestamp']

                # Check if value changed
                change_indicator = ""
                if previous_range is not None:
                    diff = current_range - previous_range
                    diff_pct = (diff / previous_range) * 100 if previous_range != 0 else 0

                    if abs(diff) > 0.01:  # Changed
                        changes_detected += 1
                        change_indicator = f"[CHANGED] {diff:+.0f} ({diff_pct:+.2f}%)"
                    else:
                        change_indicator = "[STATIC] No change"

                print(f"[{i+1}/{total_iterations}] {datetime.now().strftime('%H:%M:%S')} | "
                      f"Range: {current_range:.0f} | {change_indicator}")

                previous_range = current_range
            else:
                print(f"[ERROR] [{i+1}/{total_iterations}] API error: {response.status_code}")

        except Exception as e:
            print(f"[ERROR] [{i+1}/{total_iterations}] Request failed: {e}")

        if i < total_iterations - 1:
            time.sleep(1)

    print("\n" + "=" * 80)
    print("Test Results")
    print("=" * 80)
    print(f"Total iterations: {total_iterations}")
    print(f"Changes detected: {changes_detected}/{total_iterations - 1}")

    if changes_detected >= (total_iterations - 1) * 0.8:  # At least 80% changed
        print("[SUCCESS] Market range is updating continuously!")
    elif changes_detected > 0:
        print(f"[WARNING] Only {changes_detected} changes detected out of {total_iterations - 1} intervals")
        print("   Market range is updating but not every second")
    else:
        print("[FAILED] Market range is STATIC - not updating!")
        print("\nTroubleshooting steps:")
        print("   1. Check Python console logs for prediction_loop activity")
        print("   2. Verify SimpleCollector is fetching data from Binance")
        print("   3. Check if formula has enough variance components")

    # Get detailed metrics
    print("\n" + "=" * 80)
    print("Current Order Flow Metrics")
    print("=" * 80)
    try:
        response = requests.get(f"{API_URL}/orderflow/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print(f"Buy Volume:           {metrics['buy_volume']:.4f}")
            print(f"Sell Volume:          {metrics['sell_volume']:.4f}")
            print(f"Volume Imbalance:     {metrics['volume_imbalance']:.4f}")
            print(f"Large Trades Ratio:   {metrics['large_trades_ratio']:.4f}")
            print(f"Bid-Ask Spread:       {metrics['bid_ask_spread']:.6f}")
            print(f"Order Book Imbalance: {metrics['order_book_imbalance']:.4f}")
            print(f"Trade Intensity:      {metrics['trade_intensity']:.2f}")
    except Exception as e:
        print(f"Could not fetch metrics: {e}")

if __name__ == "__main__":
    test_continuous_updates()
