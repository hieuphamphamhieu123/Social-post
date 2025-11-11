"""
Test backtest với config đảm bảo có trades
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.test_config import TEST_CONFIG, VOLATILE_CONFIG
from backtest.backtest_engine import BacktestEngine

print("="*60)
print("BACKTEST TEST - With trades guaranteed config")
print("="*60)

# Sử dụng TEST_CONFIG
config = TEST_CONFIG

# Initialize engine
engine = BacktestEngine(config)
print(f"\nEngine initialized OK")
print(f"   Period 1 entry distance: {config.period1_first_entry_distance} points")
print(f"   Period 2 entry distance: {config.period2_first_entry_distance} points")
print(f"   Period 1 TP: {config.period1_tp} points")

# Load synthetic data with HIGHER volatility
print(f"\nLoading synthetic data...")
engine.load_data(
    data_source="synthetic",
    base_price=2000.0,
    volatility=0.005  # ⭐ Tăng từ 0.002 → 0.005 để có price movement lớn hơn
)

print(f"   Data loaded: {len(engine.market_data)} bars")
print(f"   Price range: {engine.market_data['low'].min():.2f} - {engine.market_data['high'].max():.2f}")
print(f"   Price movement: {engine.market_data['high'].max() - engine.market_data['low'].min():.2f} points")

# Run backtest
print(f"\nRunning backtest...")
results = engine.run(verbose=False, progress_bar=True)

# Get stats
stats = results['ea_statistics']
metrics = results['performance_metrics']

print("\n" + "="*60)
print("RESULTS")
print("="*60)
print(f"Total Trades:     {stats['total_trades']}")
print(f"Winning Trades:   {stats['winning_trades']}")
print(f"Losing Trades:    {stats['losing_trades']}")
print(f"Win Rate:         {stats['win_rate']:.2f}%")
print(f"Final Balance:    ${stats['final_balance']:,.2f}")
print(f"Return:           {stats['return_pct']:.2f}%")
print(f"Max Drawdown:     {metrics['max_drawdown_pct']:.2f}%")
print(f"Profit Factor:    {stats['profit_factor']:.2f}")
print(f"Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
print("="*60)

if stats['total_trades'] > 0:
    print("\nSUCCESS! Backtest executed with trades!")

    # Show first few trades
    trades_log = results['trades_log']
    if len(trades_log) > 0:
        print(f"\nFirst 5 trades:")
        print(trades_log.head().to_string())

    # Export results
    print(f"\nExporting results...")
    engine.export_results("backtest_results/test_with_trades")
    print(f"   Results saved to: backtest_results/test_with_trades/")

else:
    print("\nWARNING: Still no trades!")
    print("\nTroubleshooting:")
    print("1. Check if price movement is sufficient")
    print("2. Try increasing volatility further (0.01)")
    print("3. Decrease entry distances more")
    print("4. Check anchor price logic")

print("\nTest completed!")
