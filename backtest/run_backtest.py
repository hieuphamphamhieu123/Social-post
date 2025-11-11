"""
Run Backtest
Entry point để chạy backtest với các preset configurations
"""
import argparse
import sys
from pathlib import Path
from loguru import logger

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.config import BacktestConfig, AGGRESSIVE_CONFIG, CONSERVATIVE_CONFIG, SCALPING_CONFIG
from backtest.backtest_engine import BacktestEngine


def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=level
    )


def run_default_backtest():
    """Run backtest với default config"""
    logger.info("Running backtest with DEFAULT configuration...")

    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-12-31",
        initial_balance=10000,
        timeframe="M5",
        use_ai_prediction=True
    )

    engine = BacktestEngine(config)

    # Load synthetic data (hoặc thay bằng real data)
    engine.load_data(
        data_source="synthetic",
        base_price=2000.0,
        volatility=0.002
    )

    # Run backtest
    results = engine.run(verbose=True, progress_bar=True)

    # Print report
    engine.print_report()

    # Export results
    engine.export_results("backtest_results/default")

    return results


def run_aggressive_backtest():
    """Run backtest với aggressive config"""
    logger.info("Running backtest with AGGRESSIVE configuration...")

    config = AGGRESSIVE_CONFIG
    config.start_date = "2024-01-01"
    config.end_date = "2024-12-31"

    engine = BacktestEngine(config)

    engine.load_data(
        data_source="synthetic",
        base_price=2000.0,
        volatility=0.002
    )

    results = engine.run(verbose=True, progress_bar=True)
    engine.print_report()
    engine.export_results("backtest_results/aggressive")

    return results


def run_conservative_backtest():
    """Run backtest với conservative config"""
    logger.info("Running backtest with CONSERVATIVE configuration...")

    config = CONSERVATIVE_CONFIG
    config.start_date = "2024-01-01"
    config.end_date = "2024-12-31"

    engine = BacktestEngine(config)

    engine.load_data(
        data_source="synthetic",
        base_price=2000.0,
        volatility=0.002
    )

    results = engine.run(verbose=True, progress_bar=True)
    engine.print_report()
    engine.export_results("backtest_results/conservative")

    return results


def run_custom_backtest(
    csv_file: str = None,
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31",
    initial_balance: float = 10000,
    output_dir: str = "backtest_results/custom"
):
    """
    Run backtest với custom parameters

    Args:
        csv_file: Path to CSV file with historical data
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        initial_balance: Initial balance
        output_dir: Output directory for results
    """
    logger.info("Running CUSTOM backtest...")

    config = BacktestConfig(
        start_date=start_date,
        end_date=end_date,
        initial_balance=initial_balance,
        timeframe="M5"
    )

    engine = BacktestEngine(config)

    # Load data
    if csv_file:
        logger.info(f"Loading data from CSV: {csv_file}")
        engine.load_data(data_source="csv", filepath=csv_file)
    else:
        logger.info("Loading synthetic data...")
        engine.load_data(
            data_source="synthetic",
            base_price=2000.0,
            volatility=0.002
        )

    # Run backtest
    results = engine.run(verbose=True, progress_bar=True)
    engine.print_report()
    engine.export_results(output_dir)

    return results


def run_optimization():
    """Run parameter optimization"""
    logger.info("Running parameter OPTIMIZATION...")

    # Base config
    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-03-31",  # Shorter period for optimization
        initial_balance=10000
    )

    engine = BacktestEngine(config)

    # Load data
    engine.load_data(
        data_source="synthetic",
        base_price=2000.0,
        volatility=0.002
    )

    # Define parameter grid
    param_grid = {
        'period1_first_entry_distance': [2000, 3000, 4000],
        'period2_first_entry_distance': [7000, 9000, 11000],
        'period1_tp': [400, 600, 800],
        'period2_tp': [200, 300, 400],
        'max_orders': [10, 15, 20]
    }

    # Run optimization
    best_params, best_result = engine.optimize(
        param_grid=param_grid,
        metric="total_return_pct"
    )

    logger.info(f"Best parameters found: {best_params}")

    return best_params, best_result


def compare_strategies():
    """Compare different strategy configurations"""
    logger.info("Comparing different strategies...")

    strategies = {
        'Default': BacktestConfig(),
        'Aggressive': AGGRESSIVE_CONFIG,
        'Conservative': CONSERVATIVE_CONFIG,
        'Scalping': SCALPING_CONFIG
    }

    results_comparison = {}

    for name, config in strategies.items():
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing {name} strategy...")
        logger.info(f"{'='*60}")

        config.start_date = "2024-01-01"
        config.end_date = "2024-12-31"

        engine = BacktestEngine(config)
        engine.load_data(
            data_source="synthetic",
            base_price=2000.0,
            volatility=0.002
        )

        results = engine.run(verbose=False, progress_bar=True)

        # Store key metrics
        metrics = results['performance_metrics']
        results_comparison[name] = {
            'total_return_pct': metrics.get('total_return_pct', 0),
            'max_drawdown_pct': metrics.get('max_drawdown_pct', 0),
            'sharpe_ratio': metrics.get('sharpe_ratio', 0),
            'win_rate': metrics.get('win_rate', 0),
            'profit_factor': metrics.get('profit_factor', 0)
        }

    # Print comparison
    logger.info("\n" + "="*80)
    logger.info("STRATEGY COMPARISON")
    logger.info("="*80)

    import pandas as pd
    df = pd.DataFrame(results_comparison).T
    print(df.to_string())

    # Export comparison
    df.to_csv("backtest_results/strategy_comparison.csv")
    logger.info("\nComparison saved to backtest_results/strategy_comparison.csv")

    return results_comparison


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Backtest Box-EA + AI Market Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run default backtest
  python run_backtest.py

  # Run aggressive strategy
  python run_backtest.py --mode aggressive

  # Run with custom CSV data
  python run_backtest.py --mode custom --csv data.csv

  # Run optimization
  python run_backtest.py --mode optimize

  # Compare all strategies
  python run_backtest.py --mode compare

  # Run with custom parameters
  python run_backtest.py --mode custom --start 2024-01-01 --end 2024-12-31 --balance 20000
        """
    )

    parser.add_argument(
        '--mode',
        choices=['default', 'aggressive', 'conservative', 'custom', 'optimize', 'compare'],
        default='default',
        help='Backtest mode'
    )

    parser.add_argument(
        '--csv',
        type=str,
        help='Path to CSV file with historical data'
    )

    parser.add_argument(
        '--start',
        type=str,
        default='2024-01-01',
        help='Start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--end',
        type=str,
        default='2024-12-31',
        help='End date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--balance',
        type=float,
        default=10000,
        help='Initial balance'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='backtest_results',
        help='Output directory for results'
    )

    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Run backtest based on mode
    try:
        if args.mode == 'default':
            run_default_backtest()

        elif args.mode == 'aggressive':
            run_aggressive_backtest()

        elif args.mode == 'conservative':
            run_conservative_backtest()

        elif args.mode == 'custom':
            run_custom_backtest(
                csv_file=args.csv,
                start_date=args.start,
                end_date=args.end,
                initial_balance=args.balance,
                output_dir=args.output
            )

        elif args.mode == 'optimize':
            run_optimization()

        elif args.mode == 'compare':
            compare_strategies()

        logger.info("\n✅ Backtest completed successfully!")

    except Exception as e:
        logger.error(f"\n❌ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
