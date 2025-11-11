"""
Backtest Configuration
Cấu hình cho backtest engine - mirror từ Box-EA settings
"""
from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class BacktestConfig:
    """Configuration for backtest"""

    # ===== BACKTEST SETTINGS =====
    symbol: str = "XAUUSD"
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"
    initial_balance: float = 10000.0
    leverage: int = 1000

    # ===== EA SETTINGS (từ Box-EA) =====
    default_lot_size: float = 0.01
    max_orders: int = 33
    max_spread: float = 999
    max_simultaneous_cycles: int = 9

    # ===== PROFIT TARGETS =====
    daily_profit_target: float = 1800.0
    enable_daily_profit_limit: bool = False

    # ===== ANCHOR PRICE DISTANCES =====
    period1_first_entry_distance: int = 3
    period2_first_entry_distance: int = 9
    period3_first_entry_distance: int = 9
    outside_hours_first_entry_distance: int = 9
    hedging_threshold: float = 3

    # ===== TIME PERIODS =====
    period1_start_hour: int = 0
    period1_end_hour: int = 3
    period1_extra_distance: float = 9

    period2_start_hour: int = 11
    period2_end_hour: int = 17
    period2_extra_distance: float = 9

    period3_start_hour: int = 17
    period3_end_hour: int = 21
    period3_extra_distance: float = 6

    outside_hours_extra_distance: float = 1

    # ===== ORDER LIMITS =====
    period1_max_orders: int = 99
    period2_max_orders: int = 99
    period3_max_orders: int = 99
    outside_hours_max_orders: int = 99

    # ===== TIME-BASED CLOSING =====
    enable_time_based_closing: bool = False
    period1_order_lifetime: int = 3880
    period2_order_lifetime: int = 4880
    period3_order_lifetime: int = 5880
    outside_hours_lifetime: int = 2880

    # ===== TAKE PROFIT SETTINGS =====
    combined_tp_level: int = 1
    period1_tp: int = 999
    period2_tp: int = 999
    period3_tp: int = 999
    trend_tp: float = 999

    # Individual order TPs
    first_order_tp: int = 2000
    second_order_tp: int = 2000
    third_order_tp: int = 2000
    fourth_order_tp: int = 2000
    fifth_order_tp: int = 2000
    sixth_order_tp: int = 2000
    seventh_order_tp: int = 2000
    eighth_order_tp: int = 2000
    ninth_order_tp: int = 2000
    tenth_order_tp: int = 2000

    stop_loss: int = 36999

    # ===== AI SETTINGS =====
    use_ai_prediction: bool = True
    ai_update_interval: int = 1  # seconds
    default_market_range: float = 15000

    # ===== BACKTEST ENGINE SETTINGS =====
    timeframe: str = "M5"  # M1, M5, M15, H1, H4, D1
    commission_per_lot: float = 7.0  # USD per lot
    slippage_points: int = 5

    # ===== PERFORMANCE SETTINGS =====
    calculate_sharpe_ratio: bool = True
    risk_free_rate: float = 0.04  # 4% annual

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return self.__dict__

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BacktestConfig':
        """Create config from dictionary"""
        return cls(**config_dict)


# Default configuration
DEFAULT_CONFIG = BacktestConfig()


# Quick config presets
AGGRESSIVE_CONFIG = BacktestConfig(
    max_orders=20,
    daily_profit_target=3000,
    period1_max_orders=20,
    period2_max_orders=15,
    period3_max_orders=20,
)

CONSERVATIVE_CONFIG = BacktestConfig(
    max_orders=10,
    daily_profit_target=1000,
    period1_max_orders=10,
    period2_max_orders=6,
    period3_max_orders=10,
    stop_loss=20000,
)

SCALPING_CONFIG = BacktestConfig(
    timeframe="M1",
    first_order_tp=500,
    second_order_tp=500,
    third_order_tp=500,
    period1_tp=200,
    period2_tp=150,
    period3_tp=300,
)
