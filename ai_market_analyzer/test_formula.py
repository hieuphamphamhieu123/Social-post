"""
Test formula calculation directly
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api.market_api import calculate_market_range_from_metrics

# Test with current metrics
metrics = {
    'buy_volume': 19.69,
    'sell_volume': 23.78,
    'volume_imbalance': -0.09,
    'large_trades_ratio': 0.13,
    'bid_ask_spread': 0.000003,
    'order_book_imbalance': 0.15,
    'trade_intensity': 8.85
}

print("Testing market range calculation:")
print(f"Input metrics: {metrics}")
print()

result = calculate_market_range_from_metrics(metrics)

print()
print(f"Result: {result:.0f}")
print()

if result > 5000:
    print("[OK] Formula is working correctly!")
else:
    print("[ERROR] Formula returning value below minimum!")
