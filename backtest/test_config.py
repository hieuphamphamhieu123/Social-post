"""
Test-friendly configurations cho backtest
Dùng khi muốn test nhanh và đảm bảo có trades
"""
from config import BacktestConfig

# Config cho testing - đảm bảo có trades
TEST_CONFIG = BacktestConfig(
    # Backtest period
    start_date="2024-01-01",
    end_date="2024-01-07",  # 1 tuần để test nhanh
    initial_balance=10000,

    # EA Settings - GIẢM entry distance để dễ trigger
    default_lot_size=0.01,
    max_orders=15,
    max_simultaneous_cycles=5,

    # ⭐ QUAN TRỌNG: Giảm first entry distance
    # Với XAUUSD base price ~2000, volatility thấp
    # Cần distance nhỏ để price có thể reach được
    period1_first_entry_distance=50,    # Giảm từ 3000 → 50
    period2_first_entry_distance=100,   # Giảm từ 9000 → 100
    period3_first_entry_distance=75,    # Giảm từ 6000 → 75
    outside_hours_first_entry_distance=30,  # Giảm từ 900 → 30

    # Extra distances
    period1_extra_distance=10,
    period2_extra_distance=20,
    period3_extra_distance=15,
    outside_hours_extra_distance=5,

    # Take profits - nhỏ hơn để dễ hit
    period1_tp=100,
    period2_tp=80,
    period3_tp=120,
    first_order_tp=150,
    second_order_tp=150,

    # Order limits
    period1_max_orders=10,
    period2_max_orders=8,
    period3_max_orders=10,
    outside_hours_max_orders=5,

    # Profit target
    daily_profit_target=500,  # Giảm để dễ test
    enable_daily_profit_limit=False,  # Tắt để test đầy đủ

    # AI
    use_ai_prediction=True,

    # Timeframe
    timeframe="M5"
)


# Config cho XAUUSD với volatility cao
VOLATILE_CONFIG = BacktestConfig(
    start_date="2024-01-01",
    end_date="2024-03-31",
    initial_balance=10000,

    # Distances phù hợp với high volatility
    period1_first_entry_distance=200,
    period2_first_entry_distance=400,
    period3_first_entry_distance=300,

    period1_tp=300,
    period2_tp=250,
    period3_tp=350,

    daily_profit_target=1500,
    use_ai_prediction=True
)


# Config cho scalping (high frequency)
SCALPING_TEST_CONFIG = BacktestConfig(
    start_date="2024-01-01",
    end_date="2024-01-03",  # 3 ngày
    initial_balance=10000,
    timeframe="M1",  # 1 minute

    # Very small distances
    period1_first_entry_distance=20,
    period2_first_entry_distance=30,
    period3_first_entry_distance=25,

    # Small TPs
    period1_tp=40,
    period2_tp=30,
    period3_tp=50,
    first_order_tp=60,

    # More orders
    max_orders=20,
    period1_max_orders=20,

    daily_profit_target=300,
    enable_daily_profit_limit=False
)


if __name__ == "__main__":
    """Test các configs"""
    print("TEST_CONFIG settings:")
    print(f"  Period 1 entry distance: {TEST_CONFIG.period1_first_entry_distance}")
    print(f"  Period 2 entry distance: {TEST_CONFIG.period2_first_entry_distance}")
    print(f"  Period 1 TP: {TEST_CONFIG.period1_tp}")
    print(f"  Daily target: ${TEST_CONFIG.daily_profit_target}")
