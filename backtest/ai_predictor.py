"""
AI Predictor Simulator
Mô phỏng AI market range predictions cho backtest
Có thể dùng trained model thực hoặc rule-based simulation
"""
import numpy as np
import pandas as pd
from typing import Dict, Optional
from datetime import datetime
from loguru import logger


class AIPredictor:
    """
    Simulate AI predictions trong backtest
    Có thể dùng:
    1. Rule-based (ATR, volatility)
    2. Real AI model
    3. Replay historical predictions
    """

    def __init__(
        self,
        mode: str = "rule_based",  # "rule_based", "ai_model", "replay"
        model_path: Optional[str] = None
    ):
        self.mode = mode
        self.model = None
        self.prediction_history = []

        if mode == "ai_model" and model_path:
            self.load_model(model_path)

        logger.info(f"AI Predictor initialized in {mode} mode")

    def load_model(self, model_path: str):
        """Load trained AI model"""
        try:
            # Import AI model từ project
            import sys
            from pathlib import Path

            # Add project root to path
            project_root = Path(__file__).parent.parent
            sys.path.insert(0, str(project_root))

            from ai_market_analyzer.models.market_range_predictor import MarketRangePredictor

            self.model = MarketRangePredictor(model_path=model_path)
            logger.info(f"AI model loaded from {model_path}")

        except Exception as e:
            logger.error(f"Failed to load AI model: {e}")
            logger.warning("Falling back to rule-based mode")
            self.mode = "rule_based"

    def predict_market_range(
        self,
        current_bar: pd.Series,
        historical_data: pd.DataFrame,
        orderflow_metrics: Optional[Dict] = None
    ) -> float:
        """
        Predict market range

        Args:
            current_bar: Current OHLC bar
            historical_data: Historical data for context
            orderflow_metrics: Optional orderflow metrics

        Returns:
            Predicted market range in points
        """
        if self.mode == "rule_based":
            return self._rule_based_prediction(current_bar, historical_data)

        elif self.mode == "ai_model" and self.model:
            return self._ai_model_prediction(current_bar, historical_data, orderflow_metrics)

        elif self.mode == "replay":
            return self._replay_prediction(current_bar)

        else:
            # Fallback
            return 15000.0

    def _rule_based_prediction(
        self,
        current_bar: pd.Series,
        historical_data: pd.DataFrame
    ) -> float:
        """
        Rule-based market range prediction
        Dựa trên ATR, volatility, time of day
        """
        # Calculate ATR if available
        if 'atr' in historical_data.columns:
            atr = historical_data['atr'].iloc[-1]
            if pd.notna(atr):
                # Market range ~ 10x ATR
                market_range = atr * 10
            else:
                market_range = 15000.0
        else:
            # Fallback: use recent range
            recent_high = historical_data['high'].tail(20).max()
            recent_low = historical_data['low'].tail(20).min()
            market_range = (recent_high - recent_low) * 0.5

        # Time-based adjustment
        hour = current_bar.name.hour if hasattr(current_bar.name, 'hour') else 12

        # Asian session (quieter)
        if 0 <= hour < 8:
            market_range *= 0.7

        # London open (volatile)
        elif 8 <= hour < 12:
            market_range *= 1.3

        # NY session (most volatile)
        elif 13 <= hour < 17:
            market_range *= 1.5

        # Overlap period (very volatile)
        elif 8 <= hour < 11:
            market_range *= 1.6

        # After hours
        else:
            market_range *= 0.8

        # Clamp to reasonable range
        market_range = max(5000, min(market_range, 30000))

        # Add to history
        self.prediction_history.append({
            'datetime': current_bar.name,
            'market_range': market_range,
            'method': 'rule_based'
        })

        return market_range

    def _ai_model_prediction(
        self,
        current_bar: pd.Series,
        historical_data: pd.DataFrame,
        orderflow_metrics: Optional[Dict] = None
    ) -> float:
        """
        Use real AI model for prediction
        """
        try:
            # Create feature vector từ historical data
            features = self._create_feature_vector(historical_data, orderflow_metrics)

            # Predict
            prediction = self.model.predict_from_features(features)
            market_range = prediction['market_range']

            # Add to history
            self.prediction_history.append({
                'datetime': current_bar.name,
                'market_range': market_range,
                'volatility_class': prediction.get('volatility_class', 'unknown'),
                'trend_strength': prediction.get('trend_strength', 0.0),
                'confidence': prediction.get('confidence', 0.0),
                'method': 'ai_model'
            })

            return market_range

        except Exception as e:
            logger.error(f"AI model prediction failed: {e}")
            # Fallback to rule-based
            return self._rule_based_prediction(current_bar, historical_data)

    def _replay_prediction(self, current_bar: pd.Series) -> float:
        """
        Replay historical predictions
        (Cần có file predictions trước)
        """
        # TODO: Implement replay from saved predictions
        return 15000.0

    def _create_feature_vector(
        self,
        historical_data: pd.DataFrame,
        orderflow_metrics: Optional[Dict] = None
    ) -> np.ndarray:
        """
        Create feature vector cho AI model từ historical data
        """
        features = []

        # Nếu có orderflow metrics (simulated hoặc real)
        if orderflow_metrics:
            features.extend([
                orderflow_metrics.get('buy_volume', 0),
                orderflow_metrics.get('sell_volume', 0),
                orderflow_metrics.get('volume_imbalance', 0),
                orderflow_metrics.get('large_trades_ratio', 0),
                orderflow_metrics.get('aggressive_buy_ratio', 0),
                orderflow_metrics.get('aggressive_sell_ratio', 0),
                orderflow_metrics.get('bid_ask_spread', 0),
                orderflow_metrics.get('order_book_imbalance', 0),
                orderflow_metrics.get('volume_weighted_price', 0),
                orderflow_metrics.get('trade_intensity', 0)
            ])
        else:
            # Generate simulated orderflow metrics từ OHLCV
            features.extend(self._simulate_orderflow_features(historical_data))

        return np.array(features, dtype=np.float32)

    def _simulate_orderflow_features(self, historical_data: pd.DataFrame) -> list:
        """
        Simulate orderflow features từ OHLCV data
        Dùng khi không có real orderflow data
        """
        recent_data = historical_data.tail(20)

        # Simulate buy/sell volume from price movement
        price_change = recent_data['close'].diff()
        buy_volume = recent_data.loc[price_change > 0, 'volume'].sum()
        sell_volume = recent_data.loc[price_change < 0, 'volume'].sum()
        total_volume = recent_data['volume'].sum()

        volume_imbalance = (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0

        # Simulate other features
        features = [
            float(buy_volume),
            float(sell_volume),
            float(volume_imbalance),
            np.random.uniform(0.1, 0.3),  # large_trades_ratio
            buy_volume / total_volume if total_volume > 0 else 0.5,  # aggressive_buy_ratio
            sell_volume / total_volume if total_volume > 0 else 0.5,  # aggressive_sell_ratio
            0.0001,  # bid_ask_spread
            float(volume_imbalance * 0.8),  # order_book_imbalance
            float(recent_data['close'].iloc[-1]),  # volume_weighted_price
            len(recent_data) / 60.0  # trade_intensity (trades per minute)
        ]

        return features

    def get_imbalance(
        self,
        current_bar: pd.Series,
        historical_data: pd.DataFrame
    ) -> float:
        """
        Get current market imbalance
        Range: -1 (strong sell) to +1 (strong buy)
        """
        # Simple imbalance từ price movement
        recent_data = historical_data.tail(20)
        price_change = recent_data['close'].diff()

        buy_bars = (price_change > 0).sum()
        sell_bars = (price_change < 0).sum()
        total_bars = len(price_change) - 1  # -1 vì diff tạo 1 NaN

        if total_bars == 0:
            return 0.0

        imbalance = (buy_bars - sell_bars) / total_bars

        return imbalance

    def get_prediction_history(self) -> pd.DataFrame:
        """Get history of predictions"""
        if not self.prediction_history:
            return pd.DataFrame()

        df = pd.DataFrame(self.prediction_history)
        if 'datetime' in df.columns:
            df = df.set_index('datetime')

        return df

    def calculate_market_range_from_imbalance(self, imbalance: float) -> float:
        """
        Calculate market range từ imbalance (mirror logic từ Python API)
        Formula: (|imbalance| × 15000)
        """
        imb_abs = abs(imbalance)
        market_range = imb_abs * 15000

        # Safety clamp
        market_range = max(1, min(market_range, 30000))

        return market_range


if __name__ == "__main__":
    # Test predictor
    predictor = AIPredictor(mode="rule_based")

    # Generate test data
    dates = pd.date_range(start='2024-01-01', end='2024-01-02', freq='5min')
    test_data = pd.DataFrame({
        'open': np.random.uniform(2000, 2010, len(dates)),
        'high': np.random.uniform(2010, 2020, len(dates)),
        'low': np.random.uniform(1990, 2000, len(dates)),
        'close': np.random.uniform(2000, 2010, len(dates)),
        'volume': np.random.randint(100, 1000, len(dates))
    }, index=dates)

    # Calculate ATR
    test_data['tr'] = test_data['high'] - test_data['low']
    test_data['atr'] = test_data['tr'].rolling(window=14).mean()

    # Test prediction
    for i in range(50, len(test_data)):
        current_bar = test_data.iloc[i]
        historical = test_data.iloc[:i]

        market_range = predictor.predict_market_range(current_bar, historical)
        imbalance = predictor.get_imbalance(current_bar, historical)

        print(f"{current_bar.name}: Market Range = {market_range:.0f}, Imbalance = {imbalance:+.3f}")

    # Get history
    history = predictor.get_prediction_history()
    print(f"\n{len(history)} predictions recorded")
    print(history.head())
