"""
AI Model để dự đoán Market Range từ Order Flow
Sử dụng LSTM và Neural Networks để phân tích và dự đoán
"""
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Optional
import joblib
import os
from datetime import datetime

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.models import Sequential, Model, load_model
from tensorflow.keras.layers import (
    LSTM, Dense, Dropout, BatchNormalization,
    Input, Concatenate, Attention
)
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import train_test_split

from loguru import logger
from config.config import (
    LSTM_UNITS, DENSE_UNITS, DROPOUT_RATE,
    LEARNING_RATE, BATCH_SIZE, EPOCHS,
    FEATURE_WINDOW, MODEL_SAVE_PATH, SCALER_PATH,
    MARKET_RANGE_THRESHOLD
)


class MarketRangePredictor:
    """AI Model để dự đoán Market Range"""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.scaler = RobustScaler()  # Robust to outliers
        self.feature_scaler = StandardScaler()
        self.is_trained = False
        self.feature_window = FEATURE_WINDOW
        self.model_path = model_path or MODEL_SAVE_PATH

        # Training history
        self.training_history = []

        # Feature importance
        self.feature_importance = {}

        logger.info("Initialized MarketRangePredictor")

        # Load model if exists
        if os.path.exists(f"{self.model_path}/market_range_model.h5"):
            self.load_model()

    def build_model(self, input_shape: Tuple[int, int]) -> Model:
        """
        Xây dựng LSTM model với attention mechanism
        """
        # Input layer
        inputs = Input(shape=input_shape, name='orderflow_input')

        # LSTM layers với attention
        x = LSTM(LSTM_UNITS[0], return_sequences=True, name='lstm_1')(inputs)
        x = BatchNormalization()(x)
        x = Dropout(DROPOUT_RATE)(x)

        x = LSTM(LSTM_UNITS[1], return_sequences=True, name='lstm_2')(x)
        x = BatchNormalization()(x)
        x = Dropout(DROPOUT_RATE)(x)

        x = LSTM(LSTM_UNITS[2], return_sequences=False, name='lstm_3')(x)
        x = BatchNormalization()(x)
        x = Dropout(DROPOUT_RATE)(x)

        # Dense layers
        x = Dense(DENSE_UNITS[0], activation='relu', name='dense_1')(x)
        x = BatchNormalization()(x)
        x = Dropout(DROPOUT_RATE)(x)

        x = Dense(DENSE_UNITS[1], activation='relu', name='dense_2')(x)
        x = Dropout(DROPOUT_RATE / 2)(x)

        # Output layers - Multiple outputs
        # 1. Market Range (main output)
        market_range_output = Dense(1, activation='linear', name='market_range')(x)

        # 2. Volatility classification (low, medium, high)
        volatility_output = Dense(3, activation='softmax', name='volatility_class')(x)

        # 3. Trend strength
        trend_output = Dense(1, activation='tanh', name='trend_strength')(x)

        # Create model
        model = Model(
            inputs=inputs,
            outputs=[market_range_output, volatility_output, trend_output],
            name='MarketRangePredictor'
        )

        # Compile model
        optimizer = keras.optimizers.Adam(learning_rate=LEARNING_RATE)

        model.compile(
            optimizer=optimizer,
            loss={
                'market_range': 'mse',
                'volatility_class': 'categorical_crossentropy',
                'trend_strength': 'mse'
            },
            loss_weights={
                'market_range': 1.0,
                'volatility_class': 0.3,
                'trend_strength': 0.2
            },
            metrics={
                'market_range': ['mae', 'mape'],
                'volatility_class': ['accuracy'],
                'trend_strength': ['mae']
            }
        )

        logger.info(f"Model built with input shape: {input_shape}")
        return model

    def prepare_training_data(
        self,
        orderflow_data: pd.DataFrame,
        market_ranges: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Chuẩn bị dữ liệu training từ order flow
        """
        # Tạo sequences từ orderflow data
        X_sequences = []
        y_market_range = []
        y_volatility_class = []
        y_trend_strength = []

        for i in range(self.feature_window, len(orderflow_data)):
            # Lấy window features
            window = orderflow_data.iloc[i - self.feature_window:i]
            X_sequences.append(window.values)

            # Target: market range
            target_range = market_ranges[i]
            y_market_range.append(target_range)

            # Volatility classification
            if target_range < MARKET_RANGE_THRESHOLD * 0.7:
                vol_class = [1, 0, 0]  # Low
            elif target_range < MARKET_RANGE_THRESHOLD * 1.3:
                vol_class = [0, 1, 0]  # Medium
            else:
                vol_class = [0, 0, 1]  # High
            y_volatility_class.append(vol_class)

            # Trend strength từ volume imbalance
            if i < len(orderflow_data):
                trend = orderflow_data.iloc[i]['volume_imbalance']
                y_trend_strength.append(trend)
            else:
                y_trend_strength.append(0)

        X = np.array(X_sequences, dtype=np.float32)
        y = {
            'market_range': np.array(y_market_range, dtype=np.float32),
            'volatility_class': np.array(y_volatility_class, dtype=np.float32),
            'trend_strength': np.array(y_trend_strength, dtype=np.float32)
        }

        # Normalize X
        n_samples, n_timesteps, n_features = X.shape
        X_reshaped = X.reshape(-1, n_features)
        X_scaled = self.feature_scaler.fit_transform(X_reshaped)
        X = X_scaled.reshape(n_samples, n_timesteps, n_features)

        # Normalize y['market_range']
        y['market_range'] = self.scaler.fit_transform(
            y['market_range'].reshape(-1, 1)
        ).flatten()

        logger.info(f"Prepared training data: X shape={X.shape}, y shapes={[v.shape for v in y.values()]}")

        return X, y

    def train(
        self,
        orderflow_data: pd.DataFrame,
        market_ranges: np.ndarray,
        validation_split: float = 0.2
    ):
        """
        Train model với order flow data
        """
        logger.info("Starting model training...")

        # Prepare data
        X, y = self.prepare_training_data(orderflow_data, market_ranges)

        # Split train/validation
        indices = np.arange(len(X))
        train_idx, val_idx = train_test_split(
            indices,
            test_size=validation_split,
            shuffle=False  # Time series - không shuffle
        )

        X_train, X_val = X[train_idx], X[val_idx]
        y_train = {k: v[train_idx] for k, v in y.items()}
        y_val = {k: v[val_idx] for k, v in y.items()}

        # Build model if not exists
        if self.model is None:
            input_shape = (X.shape[1], X.shape[2])
            self.model = self.build_model(input_shape)

        # Callbacks
        callbacks = [
            EarlyStopping(
                monitor='val_market_range_loss',
                patience=10,
                restore_best_weights=True,
                verbose=1
            ),
            ModelCheckpoint(
                filepath=f"{self.model_path}/market_range_model_best.h5",
                monitor='val_market_range_loss',
                save_best_only=True,
                verbose=1
            ),
            ReduceLROnPlateau(
                monitor='val_market_range_loss',
                factor=0.5,
                patience=5,
                min_lr=1e-7,
                verbose=1
            )
        ]

        # Train
        history = self.model.fit(
            X_train,
            y_train,
            validation_data=(X_val, y_val),
            epochs=EPOCHS,
            batch_size=BATCH_SIZE,
            callbacks=callbacks,
            verbose=1
        )

        self.training_history.append(history.history)
        self.is_trained = True

        # Save model
        self.save_model()

        logger.info("Model training completed")

        return history

    def predict(self, orderflow_sequence: np.ndarray) -> Dict[str, float]:
        """
        Dự đoán market range từ orderflow sequence
        """
        if not self.is_trained and self.model is None:
            logger.error("Model not trained or loaded")
            return {
                'market_range': MARKET_RANGE_THRESHOLD,
                'volatility_class': 'medium',
                'trend_strength': 0.0,
                'confidence': 0.0
            }

        # Ensure correct shape
        if len(orderflow_sequence.shape) == 2:
            orderflow_sequence = np.expand_dims(orderflow_sequence, axis=0)

        # Scale features
        n_samples, n_timesteps, n_features = orderflow_sequence.shape
        X_reshaped = orderflow_sequence.reshape(-1, n_features)
        X_scaled = self.feature_scaler.transform(X_reshaped)
        X = X_scaled.reshape(n_samples, n_timesteps, n_features)

        # Predict
        predictions = self.model.predict(X, verbose=0)

        market_range_scaled, volatility_probs, trend_strength = predictions

        # Inverse transform market range
        market_range = self.scaler.inverse_transform(
            market_range_scaled.reshape(-1, 1)
        )[0][0]

        # Get volatility class
        vol_class_idx = np.argmax(volatility_probs[0])
        vol_classes = ['low', 'medium', 'high']
        volatility_class = vol_classes[vol_class_idx]
        confidence = volatility_probs[0][vol_class_idx]

        result = {
            'market_range': float(market_range),
            'volatility_class': volatility_class,
            'trend_strength': float(trend_strength[0][0]),
            'confidence': float(confidence),
            'timestamp': datetime.now().isoformat()
        }

        return result

    def predict_from_features(self, features: np.ndarray) -> Dict[str, float]:
        """
        Dự đoán từ feature vector đơn giản
        Cần có ít nhất FEATURE_WINDOW data points
        """
        if len(features) < self.feature_window:
            logger.warning(f"Not enough features for prediction: {len(features)} < {self.feature_window}")
            return {
                'market_range': MARKET_RANGE_THRESHOLD,
                'volatility_class': 'medium',
                'trend_strength': 0.0,
                'confidence': 0.0
            }

        # Get last window
        sequence = features[-self.feature_window:]
        return self.predict(sequence)

    def save_model(self):
        """Lưu model và scalers"""
        os.makedirs(self.model_path, exist_ok=True)
        os.makedirs(SCALER_PATH, exist_ok=True)

        # Save Keras model
        self.model.save(f"{self.model_path}/market_range_model.h5")

        # Save scalers
        joblib.dump(self.scaler, f"{SCALER_PATH}/market_range_scaler.pkl")
        joblib.dump(self.feature_scaler, f"{SCALER_PATH}/feature_scaler.pkl")

        logger.info(f"Model and scalers saved to {self.model_path}")

    def load_model(self):
        """Load model và scalers"""
        try:
            # Load Keras model
            self.model = load_model(f"{self.model_path}/market_range_model.h5")

            # Load scalers
            self.scaler = joblib.load(f"{SCALER_PATH}/market_range_scaler.pkl")
            self.feature_scaler = joblib.load(f"{SCALER_PATH}/feature_scaler.pkl")

            self.is_trained = True
            logger.info(f"Model and scalers loaded from {self.model_path}")

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.is_trained = False

    def evaluate(self, X_test: np.ndarray, y_test: Dict[str, np.ndarray]) -> Dict:
        """Đánh giá model"""
        if not self.is_trained:
            logger.error("Model not trained")
            return {}

        results = self.model.evaluate(X_test, y_test, verbose=0)

        metrics = {
            'loss': results[0],
            'market_range_loss': results[1],
            'market_range_mae': results[4],
            'market_range_mape': results[5],
            'volatility_accuracy': results[7],
            'trend_strength_mae': results[9]
        }

        logger.info(f"Model evaluation: {metrics}")
        return metrics


if __name__ == "__main__":
    # Test predictor
    predictor = MarketRangePredictor()

    # Generate dummy data for testing
    n_samples = 1000
    n_features = 10

    # Create dummy orderflow data
    orderflow_data = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )

    # Create dummy market ranges
    market_ranges = np.random.uniform(10000, 20000, n_samples)

    # Train
    history = predictor.train(orderflow_data, market_ranges)

    # Test prediction
    test_sequence = orderflow_data.iloc[-FEATURE_WINDOW:].values
    prediction = predictor.predict(test_sequence)

    print("\nPrediction Results:")
    for key, value in prediction.items():
        print(f"{key}: {value}")
