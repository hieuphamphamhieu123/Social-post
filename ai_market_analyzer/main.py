"""
Main entry point for AI Market Range Analyzer
"""
import argparse
import sys
from loguru import logger
import uvicorn

from config.config import API_HOST, API_PORT, LOG_FILE, LOG_LEVEL


def setup_logging():
    """Setup logging configuration"""
    logger.remove()  # Remove default handler

    # Console logging
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=LOG_LEVEL
    )

    # File logging
    logger.add(
        LOG_FILE,
        rotation="100 MB",
        retention="10 days",
        compression="zip",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=LOG_LEVEL
    )

    logger.info("Logging configured")


def run_api():
    """Run FastAPI server"""
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")

    uvicorn.run(
        "api.market_api:app",
        host=API_HOST,
        port=API_PORT,
        reload=False,
        log_level="info"
    )


def run_collector_only():
    """Run data collector only (for testing)"""
    from data.binance_collector import BinanceOrderFlowCollector
    import time

    logger.info("Starting data collector in standalone mode...")

    collector = BinanceOrderFlowCollector()
    collector.start()

    try:
        while True:
            time.sleep(10)
            metrics = collector.get_current_metrics()
            logger.info(f"Current metrics: {metrics}")

    except KeyboardInterrupt:
        logger.info("Stopping collector...")
        collector.stop()


def run_training():
    """Run model training"""
    from models.market_range_predictor import MarketRangePredictor
    from data.binance_collector import BinanceOrderFlowCollector
    import pandas as pd
    import numpy as np
    import time

    logger.info("Starting model training...")

    # Start collector
    collector = BinanceOrderFlowCollector()
    collector.start()

    # Wait for data collection
    logger.info("Collecting data for training... (waiting 5 minutes)")
    time.sleep(300)  # 5 minutes

    # Get historical data
    df = collector.get_historical_data(lookback_minutes=60)

    if df.empty or len(df) < 100:
        logger.error("Not enough data for training")
        return

    logger.info(f"Collected {len(df)} samples")

    # Prepare data (simplified)
    # You would need to calculate actual market ranges here
    # For now, we'll create dummy data

    # Stop collector
    collector.stop()

    logger.info("Training completed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Market Range Analyzer")

    parser.add_argument(
        "mode",
        choices=["api", "collect", "train"],
        help="Running mode: api (run API server), collect (data collection only), train (train model)"
    )

    parser.add_argument(
        "--host",
        default=API_HOST,
        help=f"API host (default: {API_HOST})"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=API_PORT,
        help=f"API port (default: {API_PORT})"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()

    logger.info(f"Starting AI Market Range Analyzer in {args.mode} mode")

    # Run based on mode
    if args.mode == "api":
        run_api()
    elif args.mode == "collect":
        run_collector_only()
    elif args.mode == "train":
        run_training()


if __name__ == "__main__":
    main()
