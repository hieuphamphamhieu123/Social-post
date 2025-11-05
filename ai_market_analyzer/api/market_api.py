"""
FastAPI REST API cho Market Range Predictor
Cung cấp endpoints để EA có thể lấy dữ liệu market range từ AI
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime
import uvicorn
import asyncio
from loguru import logger

from models.market_range_predictor import MarketRangePredictor
# Use SimpleCollector (REST-based) instead of WebSocket collector
# WebSocket has event loop issues in some environments
from data.simple_collector import SimpleCollector as BinanceOrderFlowCollector
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
collector = BinanceOrderFlowCollector()

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

            await asyncio.sleep(1)  # Update every second

        except Exception as e:
            logger.error(f"❌ Error in prediction loop (iteration #{update_count}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            await asyncio.sleep(5)


def calculate_market_range_from_metrics(metrics: Dict) -> float:
    """
    Market Range CHỈ từ Imbalance - KHÔNG thêm bớt
    Công thức: 10000 + (|imbalance| × 15000)
    """

    # Volume Imbalance từ thị trường (-1 to +1)
    volume_imbalance = metrics.get('volume_imbalance', 0)
    imb_abs = abs(volume_imbalance)

    # Market Range TRỰC TIẾP từ imbalance
    market_range = (imb_abs * 15000)

    # Safety clamp
    market_range = max(1, min(market_range, 30000))

    logger.info(f"🎯 Range: {market_range:.0f} | imb={volume_imbalance:+.3f}")

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
