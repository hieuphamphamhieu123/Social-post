"""
Example Backtest Script
Demo cách sử dụng backtest framework
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backtest.config import BacktestConfig
from backtest.backtest_engine import BacktestEngine
from loguru import logger


def example_1_simple_backtest():
    """
    Example 1: Simple backtest với default settings
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Simple Backtest")
    print("="*60)

    # Create config
    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-03-31",
        initial_balance=10000,
        timeframe="M5"
    )

    # Initialize engine
    engine = BacktestEngine(config)

    # Load synthetic data
    engine.load_data(
        data_source="synthetic",
        base_price=2000.0,
        volatility=0.002
    )

    # Run backtest
    results = engine.run(verbose=False, progress_bar=True)

    # Print report
    engine.print_report()

    print("\n✅ Example 1 completed!")


def example_2_aggressive_strategy():
    """
    Example 2: Backtest với aggressive strategy
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Aggressive Strategy")
    print("="*60)

    # Create aggressive config
    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-03-31",
        initial_balance=10000,
        max_orders=20,
        daily_profit_target=3000,
        period1_max_orders=20,
        period2_max_orders=15,
        period3_max_orders=20
    )

    engine = BacktestEngine(config)

    engine.load_data(
        data_source="synthetic",
        base_price=2000.0,
        volatility=0.003  # Higher volatility
    )

    results = engine.run(verbose=False, progress_bar=True)
    engine.print_report()

    # Export results
    engine.export_results("example_results/aggressive")

    print("\n✅ Example 2 completed!")


def example_3_custom_parameters():
    """
    Example 3: Backtest với custom parameters
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Custom Parameters")
    print("="*60)

    # Highly customized config
    config = BacktestConfig(
        # General
        symbol="XAUUSD",
        start_date="2024-01-01",
        end_date="2024-06-30",
        initial_balance=20000,
        leverage=10000,

        # EA Settings
        default_lot_size=0.01,
        max_orders=33,
        max_simultaneous_cycles=3333,

        # Period 1 (Asian session)
        period1_start_hour=0,
        period1_end_hour=8,
        period1_first_entry_distance=2,
        period1_extra_distance=2,
        period1_tp=900,
        period1_max_orders=33,

        # Period 2 (London session)
        period2_start_hour=8,
        period2_end_hour=16,
        period2_first_entry_distance=8,
        period2_extra_distance=8,
        period2_tp=999,
        period2_max_orders=99,

        # Period 3 (NY session)
        period3_start_hour=16,
        period3_end_hour=22,
        period3_first_entry_distance=50,
        period3_extra_distance=50,
        period3_tp=990,
        period3_max_orders=99,

        # Profit targets
        daily_profit_target=2500,
        enable_daily_profit_limit=False,

        # AI
        use_ai_prediction=True
    )

    engine = BacktestEngine(config)

    engine.load_data(
        data_source="synthetic",
        base_price=2050.0,
        volatility=0.0025
    )

    results = engine.run(verbose=False, progress_bar=True)
    engine.print_report()

    # Plot results
    engine.plot_results(save_path="example_results/custom_plot.png")

    print("\n✅ Example 3 completed!")


def example_4_optimization():
    """
    Example 4: Parameter optimization
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: Parameter Optimization")
    print("="*60)

    # Base config
    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-02-29",  # Shorter period for faster optimization
        initial_balance=10000
    )

    engine = BacktestEngine(config)

    # Load data
    engine.load_data(
        data_source="synthetic",
        base_price=2000.0,
        volatility=0.002
    )

    # Define parameter grid (small grid for demo)
    param_grid = {
        'period1_first_entry_distance': [20, 30],
        'period2_first_entry_distance': [70, 90],
        'period1_tp': [500, 700],
        'max_orders': [12, 15]
    }

    print("\n🔍 Running optimization...")
    print(f"Testing {2*2*2*2} = 16 combinations")

    # Run optimization
    best_params, best_result = engine.optimize(
        param_grid=param_grid,
        metric="total_return_pct"
    )

    print("\n📊 Optimization Results:")
    print(f"Best Return: {best_result['performance_metrics']['total_return_pct']:.2f}%")
    print(f"Best Parameters: {best_params}")

    print("\n✅ Example 4 completed!")


def example_5_compare_strategies():
    """
    Example 5: Compare multiple strategies
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Strategy Comparison")
    print("="*60)

    from backtest.config import AGGRESSIVE_CONFIG, CONSERVATIVE_CONFIG

    strategies = {
        'Default': BacktestConfig(),
        'Aggressive': AGGRESSIVE_CONFIG,
        'Conservative': CONSERVATIVE_CONFIG
    }

    results_summary = {}

    for name, config in strategies.items():
        print(f"\n📈 Testing {name} strategy...")

        config.start_date = "2024-01-01"
        config.end_date = "2024-03-31"

        engine = BacktestEngine(config)
        engine.load_data(
            data_source="synthetic",
            base_price=2000.0,
            volatility=0.002
        )

        results = engine.run(verbose=False, progress_bar=False)

        # Store summary
        metrics = results['performance_metrics']
        results_summary[name] = {
            'Return %': metrics['total_return_pct'],
            'Max DD %': metrics['max_drawdown_pct'],
            'Sharpe': metrics['sharpe_ratio'],
            'Win Rate %': metrics['win_rate'],
            'Trades': metrics['total_trades']
        }

    # Print comparison table
    print("\n" + "="*60)
    print("COMPARISON RESULTS")
    print("="*60)

    import pandas as pd
    df = pd.DataFrame(results_summary).T
    print(df.to_string())

    print("\n✅ Example 5 completed!")


def example_6_with_ai_predictions():
    """
    Example 6: Backtest với AI predictions
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: AI-Enhanced Backtest")
    print("="*60)

    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-03-31",
        initial_balance=10000,
        use_ai_prediction=True,  # Enable AI
        ai_update_interval=1
    )

    engine = BacktestEngine(config)

    # Load data
    engine.load_data(
        data_source="synthetic",
        base_price=2000.0,
        volatility=0.002
    )

    # Run backtest
    results = engine.run(verbose=False, progress_bar=True)
    engine.print_report()

    # Check AI predictions
    ai_predictions = results['ai_predictions']
    if not ai_predictions.empty:
        print(f"\n🤖 AI Predictions generated: {len(ai_predictions)}")
        print(f"Average Market Range: {ai_predictions['market_range'].mean():.0f}")
        print(f"Market Range Std Dev: {ai_predictions['market_range'].std():.0f}")

    # Export results with AI data
    engine.export_results("example_results/ai_enhanced")

    print("\n✅ Example 6 completed!")


def run_all_examples():
    """Run all examples"""
    print("\n" + "="*80)
    print(" "*20 + "BACKTEST FRAMEWORK - EXAMPLES")
    print("="*80)

    examples = [
        ("Simple Backtest", example_1_simple_backtest),
        ("Aggressive Strategy", example_2_aggressive_strategy),
        ("Custom Parameters", example_3_custom_parameters),
        ("Parameter Optimization", example_4_optimization),
        ("Strategy Comparison", example_5_compare_strategies),
        ("AI-Enhanced Backtest", example_6_with_ai_predictions)
    ]

    for i, (name, func) in enumerate(examples, 1):
        try:
            print(f"\n{'='*80}")
            print(f"Running Example {i}/{len(examples)}: {name}")
            print(f"{'='*80}")
            func()
        except Exception as e:
            logger.error(f"Example {i} failed: {e}")
            import traceback
            traceback.print_exc()
            continue

    print("\n" + "="*80)
    print("ALL EXAMPLES COMPLETED! ✅")
    print("="*80)


if __name__ == "__main__":
    # Setup logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )

    # Chọn example để chạy
    print("\nChọn example để chạy:")
    print("1. Simple Backtest")
    print("2. Aggressive Strategy")
    print("3. Custom Parameters")
    print("4. Parameter Optimization")
    print("5. Strategy Comparison")
    print("6. AI-Enhanced Backtest")
    print("7. Run ALL examples")
    print("0. Exit")

    try:
        choice = input("\nNhập số (0-7): ").strip()

        if choice == "1":
            example_1_simple_backtest()
        elif choice == "2":
            example_2_aggressive_strategy()
        elif choice == "3":
            example_3_custom_parameters()
        elif choice == "4":
            example_4_optimization()
        elif choice == "5":
            example_5_compare_strategies()
        elif choice == "6":
            example_6_with_ai_predictions()
        elif choice == "7":
            run_all_examples()
        elif choice == "0":
            print("Bye!")
        else:
            print("Invalid choice. Running example 1 by default...")
            example_1_simple_backtest()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Bye!")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
