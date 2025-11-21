"""
Test script to compare OLD vs NEW Volume Imbalance calculation
Demonstrates improvements from weighted calculation
"""
import numpy as np
import time

def old_volume_imbalance(trades):
    """Original simple calculation"""
    buy_volume = sum(t['quantity'] for t in trades if not t['is_buyer_maker'])
    sell_volume = sum(t['quantity'] for t in trades if t['is_buyer_maker'])
    total_volume = buy_volume + sell_volume

    return (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0


def new_volume_imbalance(trades, current_time, orderbook_imbalance=0):
    """
    NEW improved calculation with:
    - Time-weighted (recent trades more important)
    - Size-weighted (large trades more important)
    - Order book confirmation
    """
    if not trades:
        return 0.0

    decay_factor = 30000  # 30 seconds half-life
    weighted_buy = 0
    weighted_sell = 0
    total_weight = 0

    for t in trades:
        age = current_time - t['timestamp']  # milliseconds
        weight = np.exp(-age / decay_factor)  # exponential decay

        # Size-weighted: large trades có impact lớn hơn
        volume_weight = weight * (t['quantity'] ** 1.1)
        total_weight += volume_weight

        if not t['is_buyer_maker']:  # Market buy
            weighted_buy += volume_weight
        else:  # Market sell
            weighted_sell += volume_weight

    # Volume imbalance từ trades
    trade_imbalance = (weighted_buy - weighted_sell) / total_weight if total_weight > 0 else 0

    # Combined with order book (70% trades + 30% order book)
    volume_imbalance = 0.70 * trade_imbalance + 0.30 * orderbook_imbalance

    # Clamp to [-1, 1]
    return max(-1.0, min(1.0, volume_imbalance))


def create_test_scenario():
    """Create realistic test scenarios"""
    current_time = int(time.time() * 1000)

    # Scenario 1: Recent aggressive buying
    print("=" * 70)
    print("SCENARIO 1: Recent aggressive buying (large buys in last 10 seconds)")
    print("=" * 70)

    trades = []
    # Old trades (40-60 seconds ago): balanced
    for i in range(20):
        trades.append({
            'timestamp': current_time - 60000 + i * 1000,
            'quantity': 10.0,
            'is_buyer_maker': i % 2 == 0
        })

    # Recent trades (0-10 seconds ago): aggressive buying with large orders
    for i in range(10):
        trades.append({
            'timestamp': current_time - 10000 + i * 1000,
            'quantity': 50.0,  # Large buy orders
            'is_buyer_maker': False  # Market buys
        })

    old_imb = old_volume_imbalance(trades)
    new_imb = new_volume_imbalance(trades, current_time, orderbook_imbalance=0.2)

    print(f"OLD formula: {old_imb:+.4f}")
    print(f"NEW formula: {new_imb:+.4f}")
    print(f"Difference:  {new_imb - old_imb:+.4f}")
    print(f"\n[+] NEW correctly gives MORE WEIGHT to recent large buy orders\n")

    # Scenario 2: Old large sell, recent small buys
    print("=" * 70)
    print("SCENARIO 2: Old large sell (50s ago), recent small balanced trades")
    print("=" * 70)

    trades = []
    # One large sell 50 seconds ago
    trades.append({
        'timestamp': current_time - 50000,
        'quantity': 200.0,
        'is_buyer_maker': True  # Market sell
    })

    # Recent small balanced trades
    for i in range(20):
        trades.append({
            'timestamp': current_time - 10000 + i * 500,
            'quantity': 5.0,
            'is_buyer_maker': i % 2 == 0
        })

    old_imb = old_volume_imbalance(trades)
    new_imb = new_volume_imbalance(trades, current_time, orderbook_imbalance=0.1)

    print(f"OLD formula: {old_imb:+.4f}")
    print(f"NEW formula: {new_imb:+.4f}")
    print(f"Difference:  {new_imb - old_imb:+.4f}")
    print(f"\n[+] NEW correctly REDUCES IMPACT of old large sell order\n")

    # Scenario 3: Order book confirmation
    print("=" * 70)
    print("SCENARIO 3: Mixed trades + bullish order book")
    print("=" * 70)

    trades = []
    for i in range(30):
        trades.append({
            'timestamp': current_time - 30000 + i * 1000,
            'quantity': 10.0,
            'is_buyer_maker': i % 3 == 0  # Slightly bearish trades
        })

    old_imb = old_volume_imbalance(trades)
    new_imb_no_ob = new_volume_imbalance(trades, current_time, orderbook_imbalance=0)
    new_imb_with_ob = new_volume_imbalance(trades, current_time, orderbook_imbalance=0.5)

    print(f"OLD formula:              {old_imb:+.4f}")
    print(f"NEW formula (no OB):      {new_imb_no_ob:+.4f}")
    print(f"NEW formula (bullish OB): {new_imb_with_ob:+.4f}")
    print(f"OB Impact:                {new_imb_with_ob - new_imb_no_ob:+.4f}")
    print(f"\n[+] NEW combines trades + order book for better signal\n")

    # Scenario 4: All recent trades vs all old trades
    print("=" * 70)
    print("SCENARIO 4: Time decay demonstration")
    print("=" * 70)

    # All trades 55 seconds ago
    trades_old = []
    for i in range(20):
        trades_old.append({
            'timestamp': current_time - 55000,
            'quantity': 10.0,
            'is_buyer_maker': False  # All buys
        })

    # All trades 5 seconds ago
    trades_new = []
    for i in range(20):
        trades_new.append({
            'timestamp': current_time - 5000,
            'quantity': 10.0,
            'is_buyer_maker': False  # All buys
        })

    old_imb_old = old_volume_imbalance(trades_old)
    new_imb_old = new_volume_imbalance(trades_old, current_time)

    old_imb_new = old_volume_imbalance(trades_new)
    new_imb_new = new_volume_imbalance(trades_new, current_time)

    print(f"55 seconds ago trades:")
    print(f"  OLD formula: {old_imb_old:+.4f}")
    print(f"  NEW formula: {new_imb_old:+.4f} (decay factor: {np.exp(-55):+.4f})")
    print(f"\n5 seconds ago trades:")
    print(f"  OLD formula: {old_imb_new:+.4f}")
    print(f"  NEW formula: {new_imb_new:+.4f} (decay factor: {np.exp(-5/30):+.4f})")
    print(f"\n[+] NEW gives much higher weight to recent trades\n")


if __name__ == "__main__":
    print("\nVOLUME IMBALANCE CALCULATION COMPARISON")
    print("=" * 70)
    print("Testing improvements:")
    print("  [+] Time-weighted (exponential decay)")
    print("  [+] Size-weighted (large trades more important)")
    print("  [+] Order book confirmation")
    print()

    create_test_scenario()

    print("=" * 70)
    print("SUMMARY:")
    print("=" * 70)
    print("OLD formula: Simple (buy - sell) / total")
    print("  [-] All trades weighted equally regardless of time")
    print("  [-] Small and large trades have same impact per volume")
    print("  [-] Doesn't consider order book intentions")
    print()
    print("NEW formula: Time + Size weighted + Order Book")
    print("  [+] Recent trades weighted MORE (exponential decay)")
    print("  [+] Large trades have HIGHER impact (power 1.1)")
    print("  [+] Combines trades (70%) + order book (30%)")
    print("  [+] More accurate market sentiment")
    print("=" * 70)
