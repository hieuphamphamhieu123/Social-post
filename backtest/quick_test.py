"""Quick test to verify backtest system works"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.config import BacktestConfig
from backtest.backtest_engine import BacktestEngine

print("="*60)
print("QUICK BACKTEST TEST")
print("="*60)

# Create minimal config
config = BacktestConfig(
    start_date="2024-01-01",
    end_date="2024-01-07",  # Just 1 week for quick test
    initial_balance=10000,
    timeframe="M5"
)

# Initialize engine
engine = BacktestEngine(config)
print("Engine initialized OK")

# Load synthetic data
engine.load_data(
    data_source="synthetic",
    base_price=2000.0,
    volatility=0.002
)
print(f"Data loaded: {len(engine.market_data)} bars")

# Run backtest
print("\nRunning backtest...")
results = engine.run(verbose=False, progress_bar=False)

# Get stats
stats = results['ea_statistics']
metrics = results['performance_metrics']

print("\n" + "="*60)
print("RESULTS")
print("="*60)
print(f"Total Trades:     {stats['total_trades']}")
print(f"Final Balance:    ${stats['final_balance']:,.2f}")
print(f"Return:           {stats['return_pct']:.2f}%")
print(f"Win Rate:         {stats['win_rate']:.2f}%")
print(f"Max Drawdown:     {metrics['max_drawdown_pct']:.2f}%")
print("="*60)

if stats['total_trades'] > 0:
    print("\nSUCCESS: Backtest system working!")
else:
    print("\nWARNING: No trades executed. Check EA logic.")

print("\nTest completed!")
