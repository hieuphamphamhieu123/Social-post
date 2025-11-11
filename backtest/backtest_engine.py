"""
Backtest Engine
Engine chính để chạy backtest hoàn chỉnh
"""
import pandas as pd
from typing import Dict, Optional
from datetime import datetime
from loguru import logger
from tqdm import tqdm

from .config import BacktestConfig
from .data_loader import DataLoader
from .ea_simulator import BoxEASimulator
from .ai_predictor import AIPredictor
from .performance_analyzer import PerformanceAnalyzer


class BacktestEngine:
    """
    Main backtest engine
    Orchestrate toàn bộ quá trình backtest
    """

    def __init__(self, config: Optional[BacktestConfig] = None):
        """
        Initialize backtest engine

        Args:
            config: BacktestConfig object (optional)
        """
        self.config = config or BacktestConfig()

        # Initialize components
        self.data_loader = DataLoader(symbol=self.config.symbol)
        self.ea_simulator = BoxEASimulator(config=self.config)
        self.ai_predictor = AIPredictor(mode="rule_based")
        self.performance_analyzer = PerformanceAnalyzer(
            initial_balance=self.config.initial_balance,
            risk_free_rate=self.config.risk_free_rate
        )

        # Data
        self.market_data = None
        self.results = None

        logger.info(f"Backtest Engine initialized for {self.config.symbol}")

    def load_data(
        self,
        data_source: str = "synthetic",
        **kwargs
    ) -> pd.DataFrame:
        """
        Load market data

        Args:
            data_source: "csv", "mt5", "yahoo", "synthetic"
            **kwargs: Additional arguments for data loader

        Returns:
            DataFrame with OHLCV data
        """
        logger.info(f"Loading data from {data_source}...")

        if data_source == "csv":
            filepath = kwargs.get("filepath")
            if not filepath:
                raise ValueError("filepath required for CSV data source")
            self.market_data = self.data_loader.load_from_csv(filepath)

        elif data_source == "mt5":
            filepath = kwargs.get("filepath")
            if not filepath:
                raise ValueError("filepath required for MT5 CSV data source")
            self.market_data = self.data_loader.load_from_mt5_csv(filepath)

        elif data_source == "yahoo":
            ticker = kwargs.get("ticker", "GC=F")
            self.market_data = self.data_loader.load_from_yahoo(
                ticker=ticker,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                interval="5m"
            )

        elif data_source == "synthetic":
            self.market_data = self.data_loader.generate_synthetic_data(
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                timeframe=self.config.timeframe,
                base_price=kwargs.get("base_price", 2000.0),
                volatility=kwargs.get("volatility", 0.002)
            )

        else:
            raise ValueError(f"Unknown data source: {data_source}")

        # Add indicators
        self.data_loader.add_indicators()
        self.market_data = self.data_loader.get_data()

        # Validate data
        valid, message = self.data_loader.validate_data()
        if not valid:
            raise ValueError(f"Data validation failed: {message}")

        logger.info(f"Data loaded: {len(self.market_data)} bars")
        logger.info(f"Date range: {self.market_data.index[0]} to {self.market_data.index[-1]}")

        return self.market_data

    def run(
        self,
        verbose: bool = True,
        progress_bar: bool = True
    ) -> Dict:
        """
        Run backtest

        Args:
            verbose: Print detailed logs
            progress_bar: Show progress bar

        Returns:
            Dictionary với backtest results
        """
        if self.market_data is None:
            raise ValueError("No data loaded. Call load_data() first.")

        logger.info("=" * 60)
        logger.info("STARTING BACKTEST")
        logger.info("=" * 60)
        logger.info(f"Symbol: {self.config.symbol}")
        logger.info(f"Period: {self.config.start_date} to {self.config.end_date}")
        logger.info(f"Initial Balance: ${self.config.initial_balance:,.2f}")
        logger.info(f"Timeframe: {self.config.timeframe}")
        logger.info(f"Total Bars: {len(self.market_data)}")
        logger.info("=" * 60)

        # Reset simulator
        self.ea_simulator.reset()

        # Main backtest loop
        iterator = enumerate(self.market_data.iterrows())
        if progress_bar:
            iterator = tqdm(
                iterator,
                total=len(self.market_data),
                desc="Backtesting",
                unit="bar"
            )

        for i, (timestamp, bar) in iterator:
            # Get AI predictions
            historical_data = self.market_data.iloc[:i+1]

            if len(historical_data) < 20:
                # Not enough data for predictions
                continue

            # Predict market range
            ai_market_range = self.ai_predictor.predict_market_range(
                current_bar=bar,
                historical_data=historical_data
            )

            # Get imbalance
            ai_imbalance = self.ai_predictor.get_imbalance(
                current_bar=bar,
                historical_data=historical_data
            )

            # Process tick in EA
            self.ea_simulator.on_tick(
                current_bar=bar,
                ai_market_range=ai_market_range,
                ai_imbalance=ai_imbalance
            )

            # Update progress bar with stats
            if progress_bar and i % 100 == 0:
                stats = self.ea_simulator.get_statistics()
                iterator.set_postfix({
                    'Balance': f"${stats['final_balance']:.0f}",
                    'Trades': stats['total_trades'],
                    'Return': f"{stats['return_pct']:.1f}%"
                })

        logger.info("=" * 60)
        logger.info("BACKTEST COMPLETED")
        logger.info("=" * 60)

        # Get results
        self.results = self._compile_results()

        return self.results

    def _compile_results(self) -> Dict:
        """Compile backtest results"""
        # Get data from EA simulator
        equity_curve = self.ea_simulator.get_equity_curve()
        trades_log = self.ea_simulator.get_trades_log()
        ea_stats = self.ea_simulator.get_statistics()

        # Calculate performance metrics
        performance_metrics = self.performance_analyzer.calculate_metrics(
            equity_curve=equity_curve,
            trades_log=trades_log
        )

        # Get AI prediction history
        ai_predictions = self.ai_predictor.get_prediction_history()

        # Compile everything
        results = {
            'config': self.config.to_dict(),
            'ea_statistics': ea_stats,
            'performance_metrics': performance_metrics,
            'equity_curve': equity_curve,
            'trades_log': trades_log,
            'ai_predictions': ai_predictions,
            'market_data': self.market_data
        }

        return results

    def print_report(self):
        """Print detailed backtest report"""
        if self.results is None:
            logger.error("No results available. Run backtest first.")
            return

        # Print EA statistics
        logger.info("\n" + "=" * 60)
        logger.info("EA STATISTICS")
        logger.info("=" * 60)
        stats = self.results['ea_statistics']
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key:.<40} {value:>15,.2f}")
            else:
                print(f"{key:.<40} {value:>15}")

        # Print performance metrics
        self.performance_analyzer.print_report(self.results['performance_metrics'])

    def plot_results(self, save_path: Optional[str] = None):
        """Plot backtest results"""
        if self.results is None:
            logger.error("No results available. Run backtest first.")
            return

        self.performance_analyzer.plot_results(
            equity_curve=self.results['equity_curve'],
            trades_log=self.results['trades_log'],
            save_path=save_path
        )

    def export_results(self, output_dir: str = "backtest_results"):
        """Export results to files"""
        if self.results is None:
            logger.error("No results available. Run backtest first.")
            return

        import os
        from pathlib import Path

        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save equity curve
        equity_file = output_path / "equity_curve.csv"
        self.results['equity_curve'].to_csv(equity_file)
        logger.info(f"Equity curve saved to {equity_file}")

        # Save trades log
        trades_file = output_path / "trades_log.csv"
        self.results['trades_log'].to_csv(trades_file, index=False)
        logger.info(f"Trades log saved to {trades_file}")

        # Save AI predictions
        if not self.results['ai_predictions'].empty:
            predictions_file = output_path / "ai_predictions.csv"
            self.results['ai_predictions'].to_csv(predictions_file)
            logger.info(f"AI predictions saved to {predictions_file}")

        # Save metrics as JSON
        import json
        metrics_file = output_path / "metrics.json"
        with open(metrics_file, 'w') as f:
            # Combine all metrics
            all_metrics = {
                **self.results['ea_statistics'],
                **self.results['performance_metrics']
            }
            json.dump(all_metrics, f, indent=2, default=str)
        logger.info(f"Metrics saved to {metrics_file}")

        # Save plot
        plot_file = output_path / "results_plot.png"
        self.plot_results(save_path=str(plot_file))

        logger.info(f"All results exported to {output_path}")

    def optimize(
        self,
        param_grid: Dict,
        metric: str = "total_return_pct"
    ):
        """
        Optimize parameters (simplified grid search)

        Args:
            param_grid: Dictionary of parameters to optimize
            metric: Metric to optimize (e.g., "total_return_pct", "sharpe_ratio")
        """
        from itertools import product

        logger.info("Starting parameter optimization...")

        # Generate all combinations
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(product(*values))

        logger.info(f"Testing {len(combinations)} parameter combinations...")

        best_result = None
        best_metric_value = float('-inf')
        best_params = None

        for combo in tqdm(combinations, desc="Optimizing"):
            # Create config with current parameters
            test_config = BacktestConfig()
            for key, value in zip(keys, combo):
                setattr(test_config, key, value)

            # Run backtest
            test_engine = BacktestEngine(config=test_config)
            test_engine.market_data = self.market_data  # Use same data
            test_engine.run(verbose=False, progress_bar=False)

            # Get metric value
            metric_value = test_engine.results['performance_metrics'].get(metric, float('-inf'))

            # Check if better
            if metric_value > best_metric_value:
                best_metric_value = metric_value
                best_result = test_engine.results
                best_params = dict(zip(keys, combo))

        logger.info("=" * 60)
        logger.info("OPTIMIZATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Best {metric}: {best_metric_value:.2f}")
        logger.info(f"Best parameters: {best_params}")

        return best_params, best_result


if __name__ == "__main__":
    # Quick test
    from config import BacktestConfig

    config = BacktestConfig(
        start_date="2024-01-01",
        end_date="2024-03-31",
        initial_balance=10000,
        timeframe="M5"
    )

    engine = BacktestEngine(config)

    # Load synthetic data
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
    engine.export_results("test_backtest_results")
