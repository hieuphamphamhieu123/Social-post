# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         BINANCE EXCHANGE                         │
│                    (Order Flow, Orderbook, Trades)               │
└───────────────┬─────────────────────────────────────────────────┘
                │ WebSocket Streams
                │
                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PYTHON AI SYSTEM                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │           Data Collection Layer                           │  │
│  │  - BinanceOrderFlowCollector                             │  │
│  │  - Trade Stream, Depth Stream, Klines                    │  │
│  │  - Real-time metrics calculation                         │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         │                                        │
│                         ▼                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Feature Engineering                          │  │
│  │  - Volume analysis                                        │  │
│  │  - Order book imbalance                                   │  │
│  │  - Trade intensity                                        │  │
│  │  - Large trades detection                                 │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         │                                        │
│                         ▼                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              AI Model (LSTM)                              │  │
│  │  - Input: 10 orderflow features                          │  │
│  │  - LSTM layers: [128, 64, 32]                            │  │
│  │  - Outputs:                                               │  │
│  │    * Market Range (main)                                 │  │
│  │    * Volatility Classification                           │  │
│  │    * Trend Strength                                      │  │
│  └──────────────────────┬────────────────────────────────────┘  │
│                         │                                        │
│                         ▼                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              REST API (FastAPI)                           │  │
│  │  Endpoints:                                               │  │
│  │  - GET /market-range                                      │  │
│  │  - GET /market-range/simple                               │  │
│  │  - GET /orderflow/metrics                                 │  │
│  │  - GET /health                                            │  │
│  │  - POST /model/train                                      │  │
│  └──────────────────────┬────────────────────────────────────┘  │
└────────────────────────┼────────────────────────────────────────┘
                         │ HTTP/REST
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    METATRADER 5 (MT5)                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              Box-EA (Expert Advisor)                      │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │      AI_MarketRange.mqh (Integration Layer)        │  │  │
│  │  │  - WebRequest to Python API                        │  │  │
│  │  │  - GetAIMarketRange()                              │  │  │
│  │  │  - Fallback to traditional calculation            │  │  │
│  │  └───────────────────┬────────────────────────────────┘  │  │
│  │                      │                                    │  │
│  │                      ▼                                    │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │      CalculateMarketRange()                        │  │  │
│  │  │  - Uses AI prediction if available                │  │  │
│  │  │  - Falls back to traditional if API offline       │  │  │
│  │  └───────────────────┬────────────────────────────────┘  │  │
│  │                      │                                    │  │
│  │                      ▼                                    │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │      Trading Logic                                 │  │  │
│  │  │  - Entry distance calculation                      │  │  │
│  │  │  - Position sizing                                 │  │  │
│  │  │  - Risk management                                 │  │  │
│  │  │  - Order execution                                 │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│                         ▼                                        │
│                  BROKER → MARKET                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Collection Layer

**File**: `ai_market_analyzer/data/binance_collector.py`

**Responsibilities**:
- Connect to Binance WebSocket streams
- Collect real-time trades, orderbook depth, klines
- Calculate order flow metrics
- Maintain data buffers

**Key Features**:
- Real-time streaming (sub-second latency)
- Automatic reconnection on disconnect
- Efficient buffering with deque
- Metrics calculation every second

### 2. Feature Engineering

**Implemented in**: `BinanceOrderFlowCollector._calculate_current_metrics()`

**Features Calculated**:
1. **Volume Metrics**:
   - Buy volume
   - Sell volume
   - Volume imbalance ratio

2. **Trade Analysis**:
   - Large trades detection
   - Trade intensity (trades/second)
   - Volume weighted price

3. **Order Book Metrics**:
   - Bid-ask spread
   - Order book imbalance
   - Depth analysis

4. **Momentum Indicators**:
   - Aggressive buy/sell ratios
   - Directional pressure

### 3. AI Model Layer

**File**: `ai_market_analyzer/models/market_range_predictor.py`

**Architecture**:
```
Input (100, 10)  # 100 timesteps, 10 features
    ↓
LSTM(128) → BatchNorm → Dropout(0.2)
    ↓
LSTM(64) → BatchNorm → Dropout(0.2)
    ↓
LSTM(32) → BatchNorm → Dropout(0.2)
    ↓
Dense(16) → BatchNorm → Dropout(0.2)
    ↓
Dense(8) → Dropout(0.1)
    ↓
┌──────────┬──────────────────┬─────────────────┐
▼          ▼                  ▼
Market     Volatility         Trend
Range      Classification     Strength
(Linear)   (Softmax)         (Tanh)
```

**Training Process**:
1. Collect historical order flow data
2. Create sequences (sliding window)
3. Normalize features
4. Train with multiple outputs
5. Validate and save model

### 4. REST API Layer

**File**: `ai_market_analyzer/api/market_api.py`

**Key Endpoints**:

```python
GET /health
# Returns API status and readiness

GET /market-range
# Full prediction with all details

GET /market-range/simple
# Simplified response for EA
# Returns: {"market_range": 15234.5, "timestamp": "..."}

GET /orderflow/metrics
# Current order flow metrics

POST /model/train
# Trigger model training
```

**Background Tasks**:
- Continuous prediction loop (1Hz)
- Market range calculation from metrics
- Fallback when model not trained

### 5. MQL5 Integration Layer

**File**: `AI_MarketRange.mqh`

**Integration Flow**:

```mql5
OnTick()
    ↓
CalculateMarketRange()  // Called by EA
    ↓
CalculateMarketRangeWithAI()
    ↓
    ├─→ GetAIMarketRange()  // Primary
    │       ↓
    │   WebRequest(API_URL/market-range/simple)
    │       ↓
    │   Parse JSON → return market_range
    │
    └─→ CalculateTraditionalMarketRange()  // Fallback
            ↓
        Traditional calculation (H1, H4, D1 ranges)
```

**Features**:
- Automatic failover to traditional calculation
- Caching (5-second intervals)
- Error handling and logging
- Minimal latency impact

## Data Flow

### Real-time Prediction Flow

```
1. Binance sends tick data
   ↓ (WebSocket)
2. BinanceOrderFlowCollector receives and buffers
   ↓ (In-memory)
3. Calculate metrics every 1 second
   ↓
4. Feature vector created
   ↓
5. AI Model predicts market range
   ↓
6. Result stored in app.state.last_prediction
   ↓
7. EA calls API endpoint
   ↓ (HTTP GET)
8. API returns cached prediction
   ↓ (JSON)
9. EA parses and uses market range
   ↓
10. Trading decisions made
```

### Training Data Flow

```
1. Collector runs for N hours
   ↓
2. Historical data accumulated
   ↓
3. User triggers training
   ↓
4. Data preprocessed:
   - Create sequences
   - Normalize features
   - Calculate targets
   ↓
5. Model trained with validation
   ↓
6. Best model saved
   ↓
7. Scalers saved
   ↓
8. Model ready for predictions
```

## Scalability Considerations

### Current Implementation

- **Data Collection**: Single-threaded, ~1ms latency
- **Prediction**: ~10ms per prediction
- **API**: Can handle ~1000 req/sec
- **EA calls**: Typically 0.2 req/sec

### Scaling Options

If needed in future:

1. **Horizontal Scaling**:
   - Multiple API instances behind load balancer
   - Shared Redis cache for predictions

2. **Data Layer**:
   - Add MongoDB for persistent storage
   - Batch insert for efficiency

3. **Model Serving**:
   - Separate model server (TensorFlow Serving)
   - GPU acceleration for larger models

4. **Caching**:
   - Redis for distributed cache
   - Edge caching for multiple EAs

## Performance Metrics

### Expected Performance

- **API Response Time**: < 10ms (local)
- **Prediction Latency**: < 50ms end-to-end
- **Data Collection Rate**: 100+ trades/sec
- **Memory Usage**: ~500MB (Python)
- **CPU Usage**: ~5-10% (idle), ~30% (active trading)

### Monitoring Points

1. **Data Collection**:
   - WebSocket connection status
   - Buffer sizes
   - Metrics calculation time

2. **Model**:
   - Prediction accuracy
   - Confidence scores
   - Inference time

3. **API**:
   - Request rate
   - Response time
   - Error rate

4. **Integration**:
   - WebRequest success rate
   - Fallback frequency
   - Market range quality

## Security Considerations

### API Security

- Currently: Local-only (localhost)
- For remote access: Add authentication
- HTTPS recommended for production

### API Keys

- Stored in `.env` (not committed)
- Read-only permissions sufficient
- Regular rotation recommended

### EA Security

- WebRequest URL whitelist required
- No sensitive data in logs
- Error messages sanitized

## Deployment Options

### Development (Current)

```
Python API (localhost:8000)
    ↓
MT5 EA (same machine)
```

### Production Option 1 (VPS)

```
Python API (VPS:8000)
    ↑ HTTPS
MT5 (VPS or local)
```

### Production Option 2 (Cloud)

```
Python API (AWS/GCP)
    ↑ HTTPS + Auth
MT5 (Local/VPS)
```

## Technology Stack

### Python Components

- **Framework**: FastAPI (async)
- **ML**: TensorFlow/Keras
- **Data**: NumPy, Pandas
- **API Client**: python-binance
- **Logging**: Loguru

### MQL5 Components

- **HTTP Client**: Native WebRequest
- **JSON Parsing**: Custom (simple parser)
- **Integration**: Include file pattern

## Future Enhancements

### Short-term

1. ✓ Basic LSTM model
2. ☐ Train with real data
3. ☐ Model evaluation metrics
4. ☐ Auto-retraining schedule

### Medium-term

1. ☐ Additional features (RSI, MACD, etc.)
2. ☐ Ensemble models
3. ☐ Multi-symbol support
4. ☐ Performance dashboard

### Long-term

1. ☐ Reinforcement learning integration
2. ☐ Automated parameter optimization
3. ☐ Advanced risk management
4. ☐ Multi-broker support

---

**Last Updated**: 2025-11-05
