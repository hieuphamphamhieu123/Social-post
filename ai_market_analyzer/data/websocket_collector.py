"""
WebSocket-based collector cho Binance data
Giải pháp tốt nhất để tránh rate limits
"""
import json
import time
import threading
from datetime import datetime
from collections import deque
from typing import Dict
import numpy as np
import websocket
from loguru import logger


class WebSocketCollector:
    """
    WebSocket collector - Real-time data mà không có rate limits
    Tương thích với SimpleCollector interface
    """

    def __init__(self):
        self.symbol = 'PAXGUSDT'
        self.trades_buffer = deque(maxlen=1000)
        self.seen_trade_ids = set()
        self.is_running = False

        # WebSocket connections
        self.ws_trades = None
        self.ws_ticker = None
        self.ws_depth = None

        # Threads
        self.trade_thread = None
        self.ticker_thread = None
        self.depth_thread = None

        # Current data
        self.current_price = 0
        self.current_depth = {'bids': [], 'asks': []}

        self.current_metrics = {
            'timestamp': None,
            'buy_volume': 0.0,
            'sell_volume': 0.0,
            'volume_imbalance': 0.0,
            'large_trades_ratio': 0.0,
            'aggressive_buy_ratio': 0.0,
            'aggressive_sell_ratio': 0.0,
            'bid_ask_spread': 0.0,
            'order_book_imbalance': 0.0,
            'volume_weighted_price': 0.0,
            'trade_intensity': 0.0,
            'price_range': 0.0,
            'price_range_pct': 0.0,
            'price_volatility': 0.0
        }

        logger.info("WebSocketCollector initialized")

    def start(self):
        """Start WebSocket connections"""
        self.is_running = True
        logger.info("Starting WebSocket connections...")

        # Start trade stream
        self._start_trade_stream()

        # Start ticker stream (for current price)
        self._start_ticker_stream()

        # Start depth stream (for order book)
        self._start_depth_stream()

        # Start metrics calculation thread
        self.metrics_thread = threading.Thread(target=self._metrics_loop, daemon=True)
        self.metrics_thread.start()

        logger.info("✅ WebSocket collector started")

    def _start_trade_stream(self):
        """Start trade WebSocket stream"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if 'e' in data and data['e'] == 'trade':
                    trade_id = data['t']
                    if trade_id not in self.seen_trade_ids:
                        self.trades_buffer.append({
                            'timestamp': data['T'],
                            'price': float(data['p']),
                            'quantity': float(data['q']),
                            'is_buyer_maker': data['m'],
                            'trade_id': trade_id
                        })
                        self.seen_trade_ids.add(trade_id)

                        # Limit seen_trade_ids memory
                        if len(self.seen_trade_ids) > 2000:
                            oldest_ids = list(self.seen_trade_ids)[:500]
                            for old_id in oldest_ids:
                                self.seen_trade_ids.discard(old_id)
            except Exception as e:
                logger.error(f"Error processing trade: {e}")

        def on_error(ws, error):
            logger.error(f"Trade stream error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.warning("Trade stream closed")
            if self.is_running:
                logger.info("Reconnecting trade stream...")
                time.sleep(5)
                self._start_trade_stream()

        def on_open(ws):
            logger.info("✅ Trade stream connected")

        stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@trade"
        self.ws_trades = websocket.WebSocketApp(
            stream_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        self.trade_thread = threading.Thread(
            target=self.ws_trades.run_forever,
            daemon=True
        )
        self.trade_thread.start()

    def _start_ticker_stream(self):
        """Start ticker WebSocket stream for current price"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if 'c' in data:  # 'c' is current price
                    self.current_price = float(data['c'])
            except Exception as e:
                logger.error(f"Error processing ticker: {e}")

        def on_error(ws, error):
            logger.error(f"Ticker stream error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.warning("Ticker stream closed")
            if self.is_running:
                logger.info("Reconnecting ticker stream...")
                time.sleep(5)
                self._start_ticker_stream()

        def on_open(ws):
            logger.info("✅ Ticker stream connected")

        stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@ticker"
        self.ws_ticker = websocket.WebSocketApp(
            stream_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        self.ticker_thread = threading.Thread(
            target=self.ws_ticker.run_forever,
            daemon=True
        )
        self.ticker_thread.start()

    def _start_depth_stream(self):
        """Start depth WebSocket stream for order book"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if 'bids' in data and 'asks' in data:
                    self.current_depth = {
                        'bids': [[float(b[0]), float(b[1])] for b in data['bids'][:20]],
                        'asks': [[float(a[0]), float(a[1])] for a in data['asks'][:20]]
                    }
            except Exception as e:
                logger.error(f"Error processing depth: {e}")

        def on_error(ws, error):
            logger.error(f"Depth stream error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.warning("Depth stream closed")
            if self.is_running:
                logger.info("Reconnecting depth stream...")
                time.sleep(5)
                self._start_depth_stream()

        def on_open(ws):
            logger.info("✅ Depth stream connected")

        stream_url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@depth20@100ms"
        self.ws_depth = websocket.WebSocketApp(
            stream_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        self.depth_thread = threading.Thread(
            target=self.ws_depth.run_forever,
            daemon=True
        )
        self.depth_thread.start()

    def _metrics_loop(self):
        """Calculate metrics periodically"""
        while self.is_running:
            try:
                self._calculate_metrics()
                time.sleep(1)  # Update metrics every second
            except Exception as e:
                logger.error(f"Error in metrics loop: {e}")
                time.sleep(5)

    def _calculate_metrics(self):
        """Calculate metrics from collected data"""
        if len(self.trades_buffer) < 10:
            return

        # Filter trades from last 60 seconds
        current_time = int(time.time() * 1000)
        one_minute_ago = current_time - 60000
        recent_trades = [t for t in self.trades_buffer if t['timestamp'] > one_minute_ago]

        if not recent_trades:
            return

        # Calculate price volatility
        prices = [t['price'] for t in recent_trades]
        price_high = max(prices)
        price_low = min(prices)
        price_range = price_high - price_low
        price_range_pct = (price_range / price_low) * 100 if price_low > 0 else 0
        price_volatility = np.std(prices) if len(prices) > 1 else 0

        # Calculate buy/sell volume
        buy_volume = sum(t['quantity'] for t in recent_trades if not t['is_buyer_maker'])
        sell_volume = sum(t['quantity'] for t in recent_trades if t['is_buyer_maker'])
        total_volume = buy_volume + sell_volume

        # ===== IMPROVED VOLUME IMBALANCE CALCULATION =====
        # 1. Time-weighted volume imbalance (trades gần đây quan trọng hơn)
        if total_volume > 0:
            # Exponential decay: weight giảm theo thời gian
            decay_factor = 30000  # 30 seconds half-life
            weighted_buy = 0
            weighted_sell = 0
            total_weight = 0

            for t in recent_trades:
                age = current_time - t['timestamp']  # milliseconds
                weight = np.exp(-age / decay_factor)  # exponential decay

                # Size-weighted: large trades có impact lớn hơn
                volume_weight = weight * (t['quantity'] ** 1.1)
                total_weight += volume_weight

                if not t['is_buyer_maker']:  # Market buy (aggressive)
                    weighted_buy += volume_weight
                else:  # Market sell (aggressive)
                    weighted_sell += volume_weight

            # Volume imbalance từ trades (-1 to +1)
            trade_imbalance = (weighted_buy - weighted_sell) / total_weight if total_weight > 0 else 0

            # 2. Order book imbalance để confirm direction
            depth = self.current_depth
            if depth['bids'] and depth['asks']:
                bid_volume_ob = sum(bid[1] for bid in depth['bids'][:20])
                ask_volume_ob = sum(ask[1] for ask in depth['asks'][:20])
                ob_imbalance_temp = (bid_volume_ob - ask_volume_ob) / (bid_volume_ob + ask_volume_ob) if (bid_volume_ob + ask_volume_ob) > 0 else 0
            else:
                ob_imbalance_temp = 0

            # 3. Combined imbalance: 70% trades + 30% order book
            volume_imbalance = 0.70 * trade_imbalance + 0.30 * ob_imbalance_temp

            # Clamp to [-1, 1]
            volume_imbalance = max(-1.0, min(1.0, volume_imbalance))
        else:
            volume_imbalance = 0.0

        # Large trades
        avg_trade_size = total_volume / len(recent_trades) if recent_trades else 0
        large_trades = [t for t in recent_trades if t['quantity'] > avg_trade_size * 3]
        large_trades_ratio = len(large_trades) / len(recent_trades) if recent_trades else 0

        # Aggressive ratios
        aggressive_buy_ratio = buy_volume / total_volume if total_volume > 0 else 0
        aggressive_sell_ratio = sell_volume / total_volume if total_volume > 0 else 0

        # Volume weighted price
        vwp = sum(t['price'] * t['quantity'] for t in recent_trades) / total_volume if total_volume > 0 else 0

        # Trade intensity
        trade_intensity = len(recent_trades) / 60.0

        # Order book metrics
        depth = self.current_depth
        if depth['bids'] and depth['asks']:
            best_bid = depth['bids'][0][0]
            best_ask = depth['asks'][0][0]
            bid_ask_spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0

            bid_volume = sum(bid[1] for bid in depth['bids'])
            ask_volume = sum(ask[1] for ask in depth['asks'])
            ob_imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0
        else:
            bid_ask_spread = 0
            ob_imbalance = 0

        # Update metrics
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
            'trade_intensity': trade_intensity,
            'price_range': price_range,
            'price_range_pct': price_range_pct,
            'price_volatility': price_volatility
        })

        logger.debug(f"Metrics updated | Trades: {len(recent_trades)} | Range: {price_range:.2f} | Vol Imb: {volume_imbalance:+.3f}")

    def get_current_metrics(self):
        """Get current metrics (compatible with SimpleCollector)"""
        return self.current_metrics.copy()

    def get_feature_vector(self):
        """Get feature vector for AI model (compatible with SimpleCollector)"""
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

    def get_historical_data(self, lookback_minutes=60):
        """Get historical data (placeholder for compatibility)"""
        import pandas as pd
        return pd.DataFrame()

    def stop(self):
        """Stop collector"""
        self.is_running = False

        # Close WebSocket connections
        if self.ws_trades:
            self.ws_trades.close()
        if self.ws_ticker:
            self.ws_ticker.close()
        if self.ws_depth:
            self.ws_depth.close()

        logger.info("WebSocketCollector stopped")


if __name__ == "__main__":
    # Test
    collector = WebSocketCollector()
    collector.start()

    # Wait for data
    time.sleep(10)

    metrics = collector.get_current_metrics()
    print("\n=== Current Metrics ===")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    collector.stop()
