"""
Quick test for data collector
"""
from data.simple_collector import SimpleCollector
import time

print("Testing Simple Collector (REST API)...")

collector = SimpleCollector()
print("Collector initialized")

collector.start()
print("Collector started, waiting for data...")

# Wait and check metrics every 5 seconds
for i in range(12):  # 1 minute total
    time.sleep(5)
    metrics = collector.get_current_metrics()

    print(f"\n=== Check {i+1}/12 (after {(i+1)*5} seconds) ===")
    print(f"Timestamp: {metrics.get('timestamp')}")
    print(f"Buy Volume: {metrics.get('buy_volume')}")
    print(f"Sell Volume: {metrics.get('sell_volume')}")
    print(f"Trade Intensity: {metrics.get('trade_intensity')}")

    if metrics['timestamp'] is not None:
        print("✅ METRICS READY!")
        print(f"Full metrics: {metrics}")
        break
    else:
        print("⏳ Still waiting for data...")

collector.stop()
print("\nTest complete!")
