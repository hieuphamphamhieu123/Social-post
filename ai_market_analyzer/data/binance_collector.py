"""
Binance Order Flow Data Collector
Thu thập dữ liệu order flow từ Binance cho PAXGUSDT
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from binance.client import Client
from binance.websockets import BinanceSocketManager
import websocket
from loguru import logger

from config.config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, SYMBOL,
    ORDERBOOK_DEPTH, TRADE_STREAM_BUFFER, KLINE_INTERVALS
)


class BinanceOrderFlowCollector:
    """Thu thập và xử lý order flow data từ Binance"""

    def __init__(self):
        self.client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)
        self.symbol = SYMBOL

        # Data buffers
        self.trades_buffer = deque(maxlen=TRADE_STREAM_BUFFER)
        self.orderbook_snapshots = deque(maxlen=100)
        self.klines_data = {interval: deque(maxlen=500) for interval in KLINE_INTERVALS}

        # Order flow metrics
        self.current_metrics = {
            'timestamp': None,
            'buy_volume': 0.0,
            'sell_volume': 0.0,
            'volume_imbalance': 0.0,
            'large_trades_count': 0,
            'aggressive_buy_ratio': 0.0,
            'aggressive_sell_ratio': 0.0,
            'bid_ask_spread': 0.0,
            'order_book_imbalance': 0.0,
            'volume_weighted_price': 0.0,
            'trade_intensity': 0.0,
            'market_range_prediction': 0.0
        }

        # WebSocket connections
        self.ws_trades = None
        self.ws_depth = None
        self.ws_klines = {}

        logger.info(f"Initialized BinanceOrderFlowCollector for {self.symbol}")

    def start(self):
        """Bắt đầu thu thập dữ liệu"""
        logger.info("Starting data collection...")

        # Khởi tạo các WebSocket streams
        self._start_trade_stream()
        self._start_depth_stream()
        self._start_kline_streams()

        # Bắt đầu tính toán metrics
        asyncio.create_task(self._calculate_metrics_loop())

        logger.info("Data collection started successfully")

    def _start_trade_stream(self):
        """Bắt đầu stream trades"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if 'e' in data and data['e'] == 'trade':
                    self._process_trade(data)
            except Exception as e:
                logger.error(f"Error processing trade message: {e}")

        def on_error(ws, error):
            logger.error(f"Trade stream error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.warning("Trade stream closed, reconnecting...")
            time.sleep(5)
            self._start_trade_stream()

        stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@trade"
        self.ws_trades = websocket.WebSocketApp(
            stream_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        # Chạy trong thread riêng
        import threading
        thread = threading.Thread(target=self.ws_trades.run_forever)
        thread.daemon = True
        thread.start()

        logger.info("Trade stream started")

    def _start_depth_stream(self):
        """Bắt đầu stream order book depth"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if 'e' in data and data['e'] == 'depthUpdate':
                    self._process_depth(data)
            except Exception as e:
                logger.error(f"Error processing depth message: {e}")

        def on_error(ws, error):
            logger.error(f"Depth stream error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.warning("Depth stream closed, reconnecting...")
            time.sleep(5)
            self._start_depth_stream()

        stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@depth@100ms"
        self.ws_depth = websocket.WebSocketApp(
            stream_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        # Chạy trong thread riêng
        import threading
        thread = threading.Thread(target=self.ws_depth.run_forever)
        thread.daemon = True
        thread.start()

        logger.info("Depth stream started")

    def _start_kline_streams(self):
        """Bắt đầu stream klines cho các timeframes"""
        for interval in KLINE_INTERVALS:
            def on_message(ws, message, interval=interval):
                try:
                    data = json.loads(message)
                    if 'e' in data and data['e'] == 'kline':
                        self._process_kline(data, interval)
                except Exception as e:
                    logger.error(f"Error processing kline message: {e}")

            stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@kline_{interval}"
            ws = websocket.WebSocketApp(
                stream_url,
                on_message=on_message
            )

            self.ws_klines[interval] = ws

            # Chạy trong thread riêng
            import threading
            thread = threading.Thread(target=ws.run_forever)
            thread.daemon = True
            thread.start()

        logger.info(f"Kline streams started for {len(KLINE_INTERVALS)} intervals")

    def _process_trade(self, data: Dict):
        """Xử lý trade data"""
        trade = {
            'timestamp': data['T'],
            'price': float(data['p']),
            'quantity': float(data['q']),
            'is_buyer_maker': data['m'],  # True = sell, False = buy
            'trade_id': data['t']
        }

        self.trades_buffer.append(trade)

    def _process_depth(self, data: Dict):
        """Xử lý order book depth data"""
        snapshot = {
            'timestamp': data['E'],
            'bids': [[float(bid[0]), float(bid[1])] for bid in data['b'][:ORDERBOOK_DEPTH]],
            'asks': [[float(ask[0]), float(ask[1])] for ask in data['a'][:ORDERBOOK_DEPTH]]
        }

        self.orderbook_snapshots.append(snapshot)

    def _process_kline(self, data: Dict, interval: str):
        """Xử lý kline/candlestick data"""
        kline = data['k']
        candle = {
            'timestamp': kline['t'],
            'open': float(kline['o']),
            'high': float(kline['h']),
            'low': float(kline['l']),
            'close': float(kline['c']),
            'volume': float(kline['v']),
            'is_closed': kline['x']
        }

        if candle['is_closed']:
            self.klines_data[interval].append(candle)

    async def _calculate_metrics_loop(self):
        """Tính toán metrics liên tục"""
        while True:
            try:
                self._calculate_current_metrics()
                await asyncio.sleep(1)  # Cập nhật mỗi giây
            except Exception as e:
                logger.error(f"Error calculating metrics: {e}")
                await asyncio.sleep(5)

    def _calculate_current_metrics(self):
        """Tính toán các metrics từ order flow"""
        if len(self.trades_buffer) < 10:
            return

        # Lấy trades trong 1 phút gần nhất
        current_time = int(time.time() * 1000)
        one_minute_ago = current_time - 60000

        recent_trades = [t for t in self.trades_buffer if t['timestamp'] > one_minute_ago]

        if not recent_trades:
            return

        # Tính buy/sell volume
        buy_volume = sum(t['quantity'] for t in recent_trades if not t['is_buyer_maker'])
        sell_volume = sum(t['quantity'] for t in recent_trades if t['is_buyer_maker'])
        total_volume = buy_volume + sell_volume

        # ===== IMPROVED VOLUME IMBALANCE CALCULATION =====
        # 1. Time-weighted volume imbalance (trades gần đây quan trọng hơn)
        if total_volume > 0:
            # Exponential decay: weight giảm theo thời gian (trades cũ hơn có weight thấp hơn)
            decay_factor = 30000  # 30 seconds half-life
            weighted_buy = 0
            weighted_sell = 0
            total_weight = 0

            for t in recent_trades:
                age = current_time - t['timestamp']  # milliseconds
                weight = np.exp(-age / decay_factor)  # exponential decay

                # Size-weighted: large trades có impact lớn hơn (power 1.1 để tăng nhẹ impact)
                volume_weight = weight * (t['quantity'] ** 1.1)
                total_weight += volume_weight

                if not t['is_buyer_maker']:  # Market buy (aggressive)
                    weighted_buy += volume_weight
                else:  # Market sell (aggressive)
                    weighted_sell += volume_weight

            # Volume imbalance từ trades (-1 to +1)
            trade_imbalance = (weighted_buy - weighted_sell) / total_weight if total_weight > 0 else 0

            # 2. Order book imbalance để confirm direction
            if len(self.orderbook_snapshots) > 0:
                latest_ob = self.orderbook_snapshots[-1]
                bid_volume = sum(bid[1] for bid in latest_ob['bids'][:20])
                ask_volume = sum(ask[1] for ask in latest_ob['asks'][:20])
                ob_imbalance_temp = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
            else:
                ob_imbalance_temp = 0

            # 3. Combined imbalance: 70% trades + 30% order book
            # Trades phản ánh hành động thực tế, order book phản ánh ý định
            volume_imbalance = 0.70 * trade_imbalance + 0.30 * ob_imbalance_temp

            # Clamp to [-1, 1] để đảm bảo
            volume_imbalance = max(-1.0, min(1.0, volume_imbalance))
        else:
            volume_imbalance = 0.0

        # Large trades (trades > average * 3)
        avg_trade_size = total_volume / len(recent_trades) if recent_trades else 0
        large_trades = [t for t in recent_trades if t['quantity'] > avg_trade_size * 3]
        large_trades_ratio = len(large_trades) / len(recent_trades) if recent_trades else 0

        # Aggressive buy/sell ratio
        aggressive_buy_ratio = buy_volume / total_volume if total_volume > 0 else 0
        aggressive_sell_ratio = sell_volume / total_volume if total_volume > 0 else 0

        # Volume weighted price
        vwp = sum(t['price'] * t['quantity'] for t in recent_trades) / total_volume if total_volume > 0 else 0

        # Trade intensity (trades per second)
        trade_intensity = len(recent_trades) / 60.0

        # Order book metrics
        if len(self.orderbook_snapshots) > 0:
            latest_ob = self.orderbook_snapshots[-1]

            # Bid-ask spread
            best_bid = latest_ob['bids'][0][0] if latest_ob['bids'] else 0
            best_ask = latest_ob['asks'][0][0] if latest_ob['asks'] else 0
            bid_ask_spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0

            # Order book imbalance
            bid_volume = sum(bid[1] for bid in latest_ob['bids'][:20])
            ask_volume = sum(ask[1] for ask in latest_ob['asks'][:20])
            ob_imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
        else:
            bid_ask_spread = 0
            ob_imbalance = 0

        # Cập nhật metrics
        self.current_metrics.update({
            'timestamp': datetime.now().isoformat(),
            'buy_volume': buy_volume,
            'sell_volume': sell_volume,
            'volume_imbalance': volume_imbalance,
            'large_trades_ratio': large_trades_ratio,
            'aggressive_buy_ratio': aggressive_buy_ratio,
            'aggressive_sell_ratio': aggressive_sell_ratio,
            'bid_ask_spread': bid_ask_spread,
            'order_book_imbalance': ob_imbalance,
            'volume_weighted_price': vwp,
            'trade_intensity': trade_intensity
        })

    def get_current_metrics(self) -> Dict:
        """Lấy metrics hiện tại"""
        return self.current_metrics.copy()

    def get_feature_vector(self) -> np.ndarray:
        """Tạo feature vector cho AI model"""
        metrics = self.current_metrics

        features = [
            metrics['buy_volume'],
            metrics['sell_volume'],
            metrics['volume_imbalance'],
            metrics['large_trades_ratio'],
            metrics['aggressive_buy_ratio'],
            metrics['aggressive_sell_ratio'],
            metrics['bid_ask_spread'],
            metrics['order_book_imbalance'],
            metrics['volume_weighted_price'],
            metrics['trade_intensity']
        ]

        return np.array(features, dtype=np.float32)

    def get_historical_data(self, lookback_minutes: int = 60) -> pd.DataFrame:
        """Lấy dữ liệu lịch sử"""
        # Lấy trades trong lookback period
        current_time = int(time.time() * 1000)
        lookback_ms = lookback_minutes * 60 * 1000
        start_time = current_time - lookback_ms

        historical_trades = [t for t in self.trades_buffer if t['timestamp'] > start_time]

        if not historical_trades:
            return pd.DataFrame()

        df = pd.DataFrame(historical_trades)
        return df

    def stop(self):
        """Dừng thu thập dữ liệu"""
        logger.info("Stopping data collection...")

        if self.ws_trades:
            self.ws_trades.close()
        if self.ws_depth:
            self.ws_depth.close()
        for ws in self.ws_klines.values():
            ws.close()

        logger.info("Data collection stopped")


if __name__ == "__main__":
    # Test collector
    collector = BinanceOrderFlowCollector()
    collector.start()

    # Run for 60 seconds
    time.sleep(60)

    # Print metrics
    metrics = collector.get_current_metrics()
    print("\nCurrent Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    collector.stop()
