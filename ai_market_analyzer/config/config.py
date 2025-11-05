"""
Configuration file for AI Market Analyzer
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Binance API Configuration
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', '')

# Trading Pair
SYMBOL = 'PAXGUSDT'
BASE_CURRENCY = 'PAXG'
QUOTE_CURRENCY = 'USDT'

# Data Collection Settings
ORDERBOOK_DEPTH = 100  # Depth của order book
TRADE_STREAM_BUFFER = 1000  # Số lượng trades lưu trong buffer
UPDATE_INTERVAL = 1  # Cập nhật mỗi 1 giây
KLINE_INTERVALS = ['1m', '5m', '15m', '1h', '4h', '1d']

# AI Model Settings
MODEL_UPDATE_INTERVAL = 300  # Cập nhật model mỗi 5 phút
FEATURE_WINDOW = 100  # Số data points để tính features
PREDICTION_HORIZON = 60  # Dự đoán 60 phút tiếp theo

# Market Range Thresholds (từ EA)
MARKET_RANGE_THRESHOLD = 15000  # Từ EA config
MOMENTUM_THRESHOLD = 0.0020

# Feature Engineering
ORDERFLOW_FEATURES = [
    'buy_volume',
    'sell_volume',
    'volume_imbalance',
    'large_trades_ratio',
    'bid_ask_spread',
    'order_book_imbalance',
    'aggressive_buy_ratio',
    'aggressive_sell_ratio',
    'volume_weighted_price',
    'trade_intensity'
]

# Neural Network Architecture
LSTM_UNITS = [128, 64, 32]
DENSE_UNITS = [16, 8]
DROPOUT_RATE = 0.2
LEARNING_RATE = 0.001
BATCH_SIZE = 32
EPOCHS = 50

# API Settings
API_HOST = '0.0.0.0'
API_PORT = 8000
API_WORKERS = 4

# Cache Settings
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
CACHE_TTL = 300  # 5 minutes

# Logging
LOG_LEVEL = 'INFO'
LOG_FILE = 'logs/market_analyzer.log'

# Database
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
MONGODB_DB = 'market_data'

# Model Paths
MODEL_SAVE_PATH = 'models/saved_models'
SCALER_PATH = 'models/scalers'
FEATURE_IMPORTANCE_PATH = 'models/feature_importance'
