# AI Market Range Analyzer for Box-EA

Project AI Python sử dụng dữ liệu order flow từ Binance PAXGUSDT để phân tích và dự đoán market range theo thời gian thực, tích hợp với Expert Advisor (EA) trên MT5.

## 🎯 Tính năng chính

- **Thu thập Order Flow Real-time**: Kết nối với Binance WebSocket để thu thập trades, orderbook depth, và klines data
- **AI Model dự đoán Market Range**: Sử dụng LSTM Neural Networks để phân tích và dự đoán market range
- **REST API**: Cung cấp endpoints để EA có thể lấy dữ liệu theo thời gian thực
- **Tích hợp MQL5**: Code sẵn để tích hợp với Box-EA

## 📁 Cấu trúc Project

```
Lab-9/
├── ai_market_analyzer/           # Python AI Project
│   ├── api/                      # REST API
│   │   ├── market_api.py        # FastAPI endpoints
│   │   └── __init__.py
│   ├── config/                   # Configuration
│   │   ├── config.py            # Settings
│   │   └── __init__.py
│   ├── data/                     # Data Collection
│   │   ├── binance_collector.py # Binance order flow collector
│   │   └── __init__.py
│   ├── models/                   # AI Models
│   │   ├── market_range_predictor.py  # LSTM model
│   │   ├── saved_models/        # Saved trained models
│   │   ├── scalers/             # Data scalers
│   │   └── __init__.py
│   ├── utils/                    # Utilities
│   ├── logs/                     # Log files
│   ├── main.py                   # Entry point
│   └── requirements.txt          # Dependencies
├── Box-ea                        # Original EA file
├── MQL5_Integration.mq5          # Standalone MQL5 integration
├── AI_MarketRange.mqh            # Include file for Box-EA
└── README.md                     # This file
```

## 🚀 Cài đặt

### 1. Cài đặt Python Environment

```bash
# Clone repository
cd Lab-9

# Tạo virtual environment (khuyến nghị)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt dependencies
cd ai_market_analyzer
pip install -r requirements.txt
```

### 2. Cấu hình Binance API

Tạo file `.env` trong thư mục `ai_market_analyzer/`:

```env
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

**Lưu ý**: Bạn cần tạo API key từ Binance (https://www.binance.com/en/my/settings/api-management)

### 3. Chạy API Server

```bash
# Chạy API server
python main.py api

# Hoặc với custom host/port
python main.py api --host 0.0.0.0 --port 8000
```

API sẽ chạy tại: `http://localhost:8000`

### 4. Kiểm tra API

Mở trình duyệt và truy cập:
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- Market range: http://localhost:8000/market-range

## 📊 API Endpoints

### Endpoints chính

#### 1. GET `/market-range`
Lấy market range prediction đầy đủ

**Response:**
```json
{
  "market_range": 15234.5,
  "volatility_class": "medium",
  "trend_strength": 0.15,
  "confidence": 0.85,
  "timestamp": "2025-11-05T10:30:00",
  "current_metrics": {
    "buy_volume": 1234.5,
    "sell_volume": 1156.2,
    ...
  }
}
```

#### 2. GET `/market-range/simple`
Lấy market range đơn giản (dùng cho EA)

**Response:**
```json
{
  "market_range": 15234.5,
  "timestamp": "2025-11-05T10:30:00"
}
```

#### 3. GET `/orderflow/metrics`
Lấy order flow metrics hiện tại

#### 4. GET `/health`
Kiểm tra trạng thái API

## 🔧 Tích hợp với Box-EA

### Phương án 1: Sử dụng Include File (Khuyến nghị)

1. Copy file `AI_MarketRange.mqh` vào thư mục `MQL5/Include/`

2. Mở file `Box-ea` và thêm vào đầu file:
```mql5
#include <AI_MarketRange.mqh>
```

3. Trong hàm `OnInit()`, thêm:
```mql5
InitAIIntegration();
```

4. Tìm hàm `CalculateMarketRange()` (dòng 2206) và đổi tên thành:
```mql5
double CalculateTraditionalMarketRange() {
    // Code gốc giữ nguyên
    ...
}
```

5. Thêm hàm wrapper mới:
```mql5
double CalculateMarketRange() {
    return CalculateMarketRangeWithAI();
}
```

### Phương án 2: Sử dụng file riêng

1. Compile file `MQL5_Integration.mq5`
2. Chạy EA này song song với Box-EA
3. Hoặc copy code từ file này vào Box-EA

### Cài đặt WebRequest trong MT5

**QUAN TRỌNG**: Phải enable WebRequest trong MT5

1. Mở MT5
2. Tools → Options → Expert Advisors
3. Check "Allow WebRequest for listed URL"
4. Thêm URL: `http://localhost:8000`
5. Click OK

## 📈 Cách hoạt động

### 1. Data Collection Flow

```
Binance WebSocket → Order Flow Collector → Feature Extraction → Buffer
                                                                    ↓
                                                            Real-time Metrics
```

### 2. AI Prediction Flow

```
Historical Features → LSTM Model → Market Range Prediction
                                           ↓
                                    REST API → EA (MT5)
```

### 3. Integration Flow

```
EA (MT5) → HTTP GET Request → Python API → AI Model → Response
              ↓
    Update CalculateMarketRange()
              ↓
    EA sử dụng market range mới
```

## 🧠 AI Model

Model sử dụng LSTM (Long Short-Term Memory) Neural Network với:

- **Input Features** (10 features):
  - Buy volume
  - Sell volume
  - Volume imbalance
  - Large trades ratio
  - Aggressive buy/sell ratios
  - Bid-ask spread
  - Order book imbalance
  - Volume weighted price
  - Trade intensity

- **Architecture**:
  - LSTM layers: [128, 64, 32]
  - Dense layers: [16, 8]
  - Dropout: 0.2
  - Multiple outputs:
    - Market range (main)
    - Volatility classification
    - Trend strength

- **Training**:
  - Loss: MSE for regression, Categorical crossentropy for classification
  - Optimizer: Adam
  - Early stopping với patience=10

## 🎓 Training Model

### Thu thập dữ liệu training

```bash
# Chạy data collector trong 24h để thu thập training data
python main.py collect
```

### Train model

```bash
# Train với historical data
python main.py train
```

Hoặc sử dụng API endpoint:
```bash
curl -X POST "http://localhost:8000/model/train" \
     -H "Content-Type: application/json" \
     -d '{"lookback_hours": 24}'
```

## ⚙️ Configuration

Chỉnh sửa file `ai_market_analyzer/config/config.py`:

```python
# Trading pair
SYMBOL = 'PAXGUSDT'

# Data collection
ORDERBOOK_DEPTH = 100
TRADE_STREAM_BUFFER = 1000
UPDATE_INTERVAL = 1

# AI Model
FEATURE_WINDOW = 100
PREDICTION_HORIZON = 60

# Market Range Thresholds (từ EA)
MARKET_RANGE_THRESHOLD = 15000

# API
API_HOST = '0.0.0.0'
API_PORT = 8000
```

## 📊 Monitoring

### Xem logs

```bash
tail -f ai_market_analyzer/logs/market_analyzer.log
```

### Check API status

```bash
curl http://localhost:8000/health
```

### Monitor predictions

```bash
# Xem prediction real-time
watch -n 1 'curl -s http://localhost:8000/market-range/simple'
```

## 🔍 Troubleshooting

### API không kết nối được

1. Kiểm tra API có chạy không: `curl http://localhost:8000/health`
2. Kiểm tra firewall
3. Kiểm tra WebRequest đã enable trong MT5 chưa

### EA không nhận được dữ liệu

1. Check log EA trong MT5
2. Verify URL trong allowed list: Tools → Options → Expert Advisors
3. Test API trực tiếp trong browser

### Model không accurate

1. Thu thập thêm training data (ít nhất 24h)
2. Retrain model với data mới
3. Điều chỉnh hyperparameters trong config

### Binance API errors

1. Kiểm tra API key và secret
2. Verify API permissions (cần có quyền đọc market data)
3. Kiểm tra network connection

## 📝 Development

### Thêm features mới

1. Thêm feature vào `ORDERFLOW_FEATURES` trong config
2. Update `_calculate_current_metrics()` trong binance_collector.py
3. Retrain model

### Tùy chỉnh model architecture

Chỉnh sửa `build_model()` trong `market_range_predictor.py`

### Thêm API endpoints

Thêm routes vào `api/market_api.py`

## 📚 References

- [Binance API Documentation](https://binance-docs.github.io/apidocs/spot/en/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [TensorFlow/Keras Documentation](https://www.tensorflow.org/api_docs)
- [MQL5 Documentation](https://www.mql5.com/en/docs)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## ⚠️ Disclaimer

This software is for educational purposes only. Use at your own risk. Trading involves risk and may not be suitable for all investors.

## 🆘 Support

Nếu gặp vấn đề, vui lòng:
1. Kiểm tra logs: `ai_market_analyzer/logs/`
2. Xem API docs: http://localhost:8000/docs
3. Check troubleshooting section ở trên

---

**Created with ❤️ for algorithmic trading**
