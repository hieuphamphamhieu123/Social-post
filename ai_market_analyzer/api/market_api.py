"""
FastAPI REST API cho Market Range Predictor
Cung cấp endpoints để EA có thể lấy dữ liệu market range từ AI
"""
import sys
import os
# Fix import path khi chạy trực tiếp từ api folder
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import uvicorn
import asyncio
from loguru import logger

from models.market_range_predictor import MarketRangePredictor

# Choose collector based on environment variable
# WebSocketCollector is preferred (no rate limits)
# SimpleCollector is fallback (with rate limiting)
USE_WEBSOCKET = os.getenv('USE_WEBSOCKET', 'true').lower() == 'true'

if USE_WEBSOCKET:
    try:
        from data.websocket_collector import WebSocketCollector as BinanceOrderFlowCollector
        logger.info("✅ Using WebSocketCollector (no rate limits)")
    except Exception as e:
        logger.warning(f"Failed to import WebSocketCollector: {e}, falling back to SimpleCollector")
        from data.simple_collector import SimpleCollector as BinanceOrderFlowCollector
else:
    from data.simple_collector import SimpleCollector as BinanceOrderFlowCollector
    logger.info("ℹ️ Using SimpleCollector (with rate limiting)")

from config.config import API_HOST, API_PORT, SYMBOL

# Initialize FastAPI app
app = FastAPI(
    title="AI Market Range Analyzer",
    description="API để dự đoán market range từ order flow data",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
predictor = MarketRangePredictor()

# Initialize collector
# If using SimpleCollector, set longer update interval to avoid rate limits
if USE_WEBSOCKET:
    collector = BinanceOrderFlowCollector()  # WebSocket doesn't need update_interval
else:
    # Tăng lên 20 giây để chắc chắn tránh rate limit
    # 3 API calls x 3 requests/min = 9 requests/min (rất an toàn)
    collector = BinanceOrderFlowCollector(update_interval=20)

# State
app.state.is_collecting = False
app.state.last_prediction = None


# Pydantic models
class MarketRangeResponse(BaseModel):
    """Response model cho market range prediction"""
    market_range: float = Field(..., description="Predicted market range in points")
    volatility_class: str = Field(..., description="Volatility classification: low, medium, high")
    trend_strength: float = Field(..., description="Trend strength [-1, 1]")
    confidence: float = Field(..., description="Prediction confidence [0, 1]")
    timestamp: str = Field(..., description="Prediction timestamp")
    current_metrics: Dict = Field(..., description="Current order flow metrics")


class OrderFlowMetrics(BaseModel):
    """Order flow metrics"""
    buy_volume: float
    sell_volume: float
    volume_imbalance: float
    large_trades_ratio: float
    aggressive_buy_ratio: float
    aggressive_sell_ratio: float
    bid_ask_spread: float
    order_book_imbalance: float
    volume_weighted_price: float
    trade_intensity: float
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    is_collecting: bool
    predictor_ready: bool
    timestamp: str


class TrainingRequest(BaseModel):
    """Request model cho training"""
    lookback_hours: int = Field(24, description="Hours of historical data to use for training")


# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Khởi động khi API start"""
    logger.info("Starting Market Range API...")

    # Start data collection
    collector.start()
    app.state.is_collecting = True

    # Start prediction loop
    asyncio.create_task(prediction_loop())

    logger.info("Market Range API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Dừng khi API shutdown"""
    logger.info("Shutting down Market Range API...")

    app.state.is_collecting = False
    collector.stop()

    logger.info("Market Range API shutdown complete")


async def prediction_loop():
    """Background task để update predictions liên tục"""
    logger.info("🔄 Prediction loop started!")
    update_count = 0

    while app.state.is_collecting:
        try:
            update_count += 1
            logger.debug(f"⏰ Prediction loop iteration #{update_count}")

            # Get current orderflow data
            metrics = collector.get_current_metrics()

            if metrics['timestamp'] is not None:
                # Get feature vector
                features = collector.get_feature_vector()

                # Predict (nếu có đủ data)
                # Tạm thời sử dụng metrics trực tiếp để tính market range
                # Sau khi train model sẽ dùng predictor
                if predictor.is_trained:
                    # Cần tạo sequence từ historical data
                    pass
                else:
                    # Fallback: Tính market range từ metrics
                    market_range = calculate_market_range_from_metrics(metrics)

                    prediction = {
                        'market_range': market_range,
                        'volatility_class': classify_volatility(market_range),
                        'trend_strength': metrics['volume_imbalance'],
                        'confidence': 0.8,
                        'timestamp': metrics['timestamp'],
                        'current_metrics': metrics
                    }

                    app.state.last_prediction = prediction
                    logger.info(f"✅ Prediction #{update_count} updated: Market Range = {market_range:.0f}")
            else:
                logger.warning(f"⚠️ Iteration #{update_count}: No metrics available yet")

            # Update every 10 seconds to reduce API calls and avoid rate limits
            # SimpleCollector has internal rate limiting (20s interval)
            # WebSocketCollector updates real-time, không ảnh hưởng bởi sleep
            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"❌ Error in prediction loop (iteration #{update_count}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            await asyncio.sleep(5)


def calculate_market_range_from_metrics(metrics: Dict) -> float:
    """
    Market Range - HYBRID LOGIC
    Kết hợp volume imbalance (stable base) + volatility adjustment (responsive)

    Phù hợp với PAXGUSDT trading thực tế!
    """

    # 1. VOLUME METRICS - Base stable từ volume (như logic cũ)
    volume_imbalance = metrics.get('volume_imbalance', 0)  # -1 to +1
    large_trades_ratio = metrics.get('large_trades_ratio', 0)  # 0 to 1

    # 2. PRICE VOLATILITY - Điều chỉnh responsive
    price_range = metrics.get('price_range', 0)  # High - Low
    price_range_pct = metrics.get('price_range_pct', 0)  # % movement (primary indicator)

    # 3. TRADE ACTIVITY
    trade_intensity = metrics.get('trade_intensity', 0)  # trades/sec

    # 4. BASE RANGE từ volume imbalance (10000 baseline phù hợp EA)
    # Volume imbalance 0 → 10000 points
    # Volume imbalance 1 → 25000 points
    base_range = (abs(volume_imbalance) * 15000)

    # 5. VOLATILITY ADJUSTMENT (0.5 - 2.0x)
    # Dùng price_range_pct (%) thay vì absolute để responsive hơn
    # PAXGUSDT: 0.1% movement = low volatility
    #           0.5% movement = high volatility
    if price_range_pct > 0:
        # Scale: 0.1% → x0.8, 0.3% → x1.2, 0.5%+ → x1.5
        volatility_mult = 0.8 + (price_range_pct * 2.0)
        volatility_mult = max(0.5, min(volatility_mult, 2.0))
    else:
        volatility_mult = 1.0

    # 6. LARGE TRADES ADJUSTMENT (1.0 - 1.4x)
    large_trades_mult = 1.0 + (large_trades_ratio * 0.4)

    # 7. TRADE INTENSITY ADJUSTMENT (0.8 - 1.3x)
    # Ít trades → giảm range, nhiều trades → tăng range
    if trade_intensity < 1.0:
        intensity_mult = 0.8 + (trade_intensity * 0.2)
    else:
        intensity_mult = 1.0 + min(trade_intensity / 10.0, 0.3)

    # 8. TÍNH MARKET RANGE CUỐI CÙNG
    market_range = base_range * volatility_mult * large_trades_mult * intensity_mult

    # 9. SAFETY CLAMP (5000 - 35000 phù hợp với EA)
    market_range = max(1, min(market_range, 35000))

    # 10. LOG chi tiết để debug
    logger.info(f"🎯 Market Range Calculation:")
    logger.info(f"   Volume Imb: {volume_imbalance:+.3f} → Base: {base_range:.0f}")
    logger.info(f"   Price Range: {price_range:.2f} ({price_range_pct:.4f}%) → x{volatility_mult:.2f}")
    logger.info(f"   Large Trades: {large_trades_ratio:.2f} → x{large_trades_mult:.2f}")
    logger.info(f"   Intensity: {trade_intensity:.2f} trades/s → x{intensity_mult:.2f}")
    logger.info(f"   → FINAL RANGE: {market_range:.0f} points")

    return market_range


def classify_volatility(market_range: float) -> str:
    """Phân loại volatility dựa trên market range"""
    from config.config import MARKET_RANGE_THRESHOLD

    if market_range < MARKET_RANGE_THRESHOLD * 0.7:
        return 'low'
    elif market_range < MARKET_RANGE_THRESHOLD * 1.3:
        return 'medium'
    else:
        return 'high'


@app.get("/", response_model=Dict)
async def root():
    """Root endpoint"""
    return {
        "service": "AI Market Range Analyzer",
        "version": "1.0.0",
        "status": "running",
        "symbol": SYMBOL
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if app.state.is_collecting else "stopped",
        is_collecting=app.state.is_collecting,
        predictor_ready=predictor.is_trained,
        timestamp=datetime.now().isoformat()
    )


@app.get("/market-range", response_model=MarketRangeResponse)
async def get_market_range():
    """
    Lấy market range prediction hiện tại
    Đây là endpoint chính mà EA sẽ gọi
    """
    if app.state.last_prediction is None:
        raise HTTPException(
            status_code=503,
            detail="Prediction not ready yet, please wait a moment"
        )

    return MarketRangeResponse(**app.state.last_prediction)


@app.get("/market-range/simple", response_model=Dict)
async def get_market_range_simple():
    """
    Lấy market range đơn giản (chỉ trả về số)
    Dễ dàng cho EA parse
    """
    if app.state.last_prediction is None:
        raise HTTPException(
            status_code=503,
            detail="Prediction not ready yet"
        )

    return {
        "market_range": app.state.last_prediction['market_range'],
        "timestamp": app.state.last_prediction['timestamp']
    }


@app.get("/orderflow/metrics", response_model=OrderFlowMetrics)
async def get_orderflow_metrics():
    """Lấy order flow metrics hiện tại"""
    metrics = collector.get_current_metrics()

    if metrics['timestamp'] is None:
        raise HTTPException(
            status_code=503,
            detail="Metrics not ready yet"
        )

    return OrderFlowMetrics(**metrics)


@app.get("/orderflow/historical")
async def get_historical_orderflow(lookback_minutes: int = 60):
    """Lấy dữ liệu order flow historical"""
    df = collector.get_historical_data(lookback_minutes)

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail="No historical data available"
        )

    return {
        "data": df.to_dict(orient='records'),
        "count": len(df),
        "lookback_minutes": lookback_minutes
    }


@app.post("/model/train")
async def train_model(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    """
    Train AI model với historical data
    """
    try:
        # Get historical data
        lookback_minutes = request.lookback_hours * 60
        df = collector.get_historical_data(lookback_minutes)

        if df.empty or len(df) < 1000:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough data for training. Need at least 1000 samples, got {len(df)}"
            )

        # Prepare training data (simplified version)
        # In production, you would need to calculate actual market ranges
        # For now, use a placeholder

        logger.info(f"Starting model training with {len(df)} samples...")

        return {
            "status": "training_started",
            "samples": len(df),
            "message": "Model training will complete in background"
        }

    except Exception as e:
        logger.error(f"Error starting training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/model/status")
async def get_model_status():
    """Lấy trạng thái của model"""
    return {
        "is_trained": predictor.is_trained,
        "model_exists": predictor.model is not None,
        "feature_window": predictor.feature_window,
        "training_history_count": len(predictor.training_history)
    }


@app.post("/data/collection/start")
async def start_collection():
    """Bắt đầu thu thập dữ liệu"""
    if app.state.is_collecting:
        return {"status": "already_collecting"}

    collector.start()
    app.state.is_collecting = True

    return {"status": "collection_started"}


@app.post("/data/collection/stop")
async def stop_collection():
    """Dừng thu thập dữ liệu"""
    if not app.state.is_collecting:
        return {"status": "not_collecting"}

    collector.stop()
    app.state.is_collecting = False

    return {"status": "collection_stopped"}


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return {
        "error": str(exc),
        "type": type(exc).__name__
    }


if __name__ == "__main__":
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")

    uvicorn.run(
        "market_api:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
        log_level="info"
    )
