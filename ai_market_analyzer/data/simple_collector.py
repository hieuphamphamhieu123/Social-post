"""
Simple REST API-based collector (fallback for WebSocket issues)
Thu thập data từ Binance REST API thay vì WebSocket
"""
from binance.client import Client
from datetime import datetime
import time
from collections import deque
from loguru import logger
import numpy as np


class SimpleCollector:
    """Simple collector using REST API polling instead of WebSocket"""

    def __init__(self, update_interval=15):
        self.client = Client()  # No auth needed for public data
        self.symbol = 'PAXGUSDT'
        self.trades_buffer = deque(maxlen=1000)
        self.seen_trade_ids = set()  # Track để tránh duplicate
        self.is_running = False

        # Rate limiting - Mặc định 15 giây để tránh rate limit
        # 3 API calls x 4 requests/min = 12 requests/min (an toàn)
        self.update_interval = update_interval  # Minimum seconds between API calls
        self.last_update_time = 0  # Timestamp of last update
        self.update_cooldown = 0  # Cooldown counter for rate limit errors
        self.consecutive_rate_limits = 0  # Đếm số lần liên tiếp bị rate limit

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
            'price_range': 0.0,  # Actual price movement (high - low)
            'price_range_pct': 0.0,  # Price range as percentage
            'price_volatility': 0.0  # Standard deviation of prices
        }

    def start(self):
        """Start collecting data"""
        self.is_running = True
        logger.info("SimpleCollector started")

        # Initial data fetch
        self._update_data()

    def _update_data(self):
        """Update data from Binance REST API"""
        current_time = time.time()

        # Check cooldown period (if we hit rate limit previously)
        if self.update_cooldown > 0:
            if current_time < self.update_cooldown:
                logger.debug(f"In cooldown period, skipping update. Cooldown ends in {self.update_cooldown - current_time:.1f}s")
                return
            else:
                # Cooldown expired
                self.update_cooldown = 0
                logger.info("Cooldown period expired, resuming API calls")

        # Check rate limit
        time_since_last_update = current_time - self.last_update_time
        if time_since_last_update < self.update_interval:
            logger.debug(f"Rate limit: Skipping update (last update {time_since_last_update:.1f}s ago, interval={self.update_interval}s)")
            return

        try:
            # Get recent trades
            trades = self.client.get_recent_trades(symbol=self.symbol, limit=100)
            logger.debug(f"Fetched {len(trades)} trades from Binance")

            # Add to buffer (skip duplicates)
            new_trades_count = 0
            for trade in trades:
                trade_id = trade['id']
                if trade_id not in self.seen_trade_ids:
                    self.trades_buffer.append({
                        'timestamp': trade['time'],
                        'price': float(trade['price']),
                        'quantity': float(trade['qty']),
                        'is_buyer_maker': trade['isBuyerMaker'],
                        'trade_id': trade_id
                    })
                    self.seen_trade_ids.add(trade_id)
                    new_trades_count += 1

                    # Giới hạn seen_trade_ids để không tốn memory
                    if len(self.seen_trade_ids) > 2000:
                        # Xóa 500 IDs cũ nhất (giữ 1500 gần nhất)
                        oldest_ids = list(self.seen_trade_ids)[:500]
                        for old_id in oldest_ids:
                            self.seen_trade_ids.discard(old_id)

            logger.debug(f"Added {new_trades_count} new trades (skipped {len(trades) - new_trades_count} duplicates)")

            # Get ticker
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            current_price = float(ticker['price'])
            logger.debug(f"Current price: {current_price}")

            # Get order book
            depth = self.client.get_order_book(symbol=self.symbol, limit=20)
            logger.debug(f"Order book: {len(depth['bids'])} bids, {len(depth['asks'])} asks")

            # Calculate metrics
            logger.debug("Calling _calculate_metrics...")
            self._calculate_metrics(depth, current_price)

            # Update last update time on success
            self.last_update_time = current_time

            # Reset consecutive rate limits on success
            if self.consecutive_rate_limits > 0:
                logger.info(f"✅ API calls successful, resetting rate limit counter")
                self.consecutive_rate_limits = 0

            logger.info(f"Data updated: {len(self.trades_buffer)} total trades in buffer | {new_trades_count} new trades added")

        except Exception as e:
            # Check if it's a rate limit error
            if 'APIError(code=-1003)' in str(e) or 'Too much request weight' in str(e):
                self.consecutive_rate_limits += 1

                # Tự động tăng update_interval sau mỗi lần bị rate limit
                if self.consecutive_rate_limits > 1:
                    self.update_interval = min(self.update_interval * 1.5, 60)  # Max 60s
                    logger.warning(f"⚠️ Multiple rate limits detected! Increasing update_interval to {self.update_interval:.1f}s")

                # Set cooldown - tăng theo số lần liên tiếp bị rate limit
                cooldown_time = 60 * self.consecutive_rate_limits  # 60s, 120s, 180s...
                cooldown_time = min(cooldown_time, 300)  # Max 5 minutes
                self.update_cooldown = time.time() + cooldown_time

                logger.error(f"🚫 RATE LIMIT HIT (#{self.consecutive_rate_limits})! Cooldown for {cooldown_time}s")
                logger.error(f"Current update_interval: {self.update_interval}s")
                logger.error("SOLUTION: Use WebSocketCollector instead - set USE_WEBSOCKET=true")
            else:
                logger.error(f"Error updating data: {e}")
                import traceback
                logger.error(traceback.format_exc())

    def _calculate_metrics(self, depth, current_price):
        """Calculate metrics from collected data"""
        if len(self.trades_buffer) < 10:
            logger.warning(f"Not enough trades: {len(self.trades_buffer)}")
            return

        # Use all trades in buffer (they are recent from API)
        # Don't filter by timestamp as API trades might have older timestamps
        recent_trades = list(self.trades_buffer)

        if not recent_trades:
            logger.warning("No recent trades found")
            return

        logger.debug(f"Calculating metrics from {len(recent_trades)} trades")

        # CALCULATE ACTUAL PRICE VOLATILITY (This is KEY for market range!)
        prices = [t['price'] for t in recent_trades]
        price_high = max(prices)
        price_low = min(prices)
        price_range = price_high - price_low
        price_range_pct = (price_range / price_low) * 100 if price_low > 0 else 0

        # Calculate price volatility (standard deviation)
        price_volatility = np.std(prices) if len(prices) > 1 else 0

        # Calculate buy/sell volume
        buy_volume = sum(t['quantity'] for t in recent_trades if not t['is_buyer_maker'])
        sell_volume = sum(t['quantity'] for t in recent_trades if t['is_buyer_maker'])
        total_volume = buy_volume + sell_volume

        logger.debug(f"Price Range: {price_range:.2f} ({price_range_pct:.4f}%) | Volatility: {price_volatility:.2f}")
        logger.debug(f"Buy: {buy_volume}, Sell: {sell_volume}, Total: {total_volume}")

        # ===== IMPROVED VOLUME IMBALANCE CALCULATION =====
        # REST API không có timestamp chính xác, dùng position-based weighting
        if total_volume > 0:
            weighted_buy = 0
            weighted_sell = 0
            total_weight = 0

            total_trades = len(recent_trades)
            for idx, t in enumerate(recent_trades):
                # Position-based weight: trades mới hơn (idx cao hơn) có weight cao hơn
                # Weight tăng exponentially: early trades = 0.1x, latest trades = 1.0x
                position_factor = (idx + 1) / total_trades  # 0 to 1
                weight = np.exp(position_factor * 2) / np.exp(2)  # normalize to 0.13 to 1.0

                # Size-weighted: large trades có impact lớn hơn
                volume_weight = weight * (t['quantity'] ** 1.1)
                total_weight += volume_weight

                if not t['is_buyer_maker']:  # Market buy (aggressive)
                    weighted_buy += volume_weight
                else:  # Market sell (aggressive)
                    weighted_sell += volume_weight

            # Volume imbalance từ trades (-1 to +1)
            trade_imbalance = (weighted_buy - weighted_sell) / total_weight if total_weight > 0 else 0

            # Order book imbalance để confirm direction
            bid_volume_ob = sum(float(bid[1]) for bid in depth['bids'][:20])
            ask_volume_ob = sum(float(ask[1]) for ask in depth['asks'][:20])
            ob_imbalance_temp = (bid_volume_ob - ask_volume_ob) / (bid_volume_ob + ask_volume_ob) if (bid_volume_ob + ask_volume_ob) > 0 else 0

            # Combined imbalance: 70% trades + 30% order book
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
        best_bid = float(depth['bids'][0][0]) if depth['bids'] else 0
        best_ask = float(depth['asks'][0][0]) if depth['asks'] else 0
        bid_ask_spread = (best_ask - best_bid) / best_bid if best_bid > 0 else 0

        bid_volume = sum(float(bid[1]) for bid in depth['bids'][:20])
        ask_volume = sum(float(ask[1]) for ask in depth['asks'][:20])
        ob_imbalance = (bid_volume - ask_volume) / (bid_volume + ask_volume) if (bid_volume + ask_volume) > 0 else 0

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

        logger.info(f"✅ Metrics | PriceRange: {price_range:.2f} ({price_range_pct:.4f}%) | Vol: {price_volatility:.2f} | Trades: {len(recent_trades)}")

    def get_current_metrics(self):
        """Get current metrics"""
        # Update data before returning (với rate limiting tự động)
        # Nếu gọi quá nhanh, _update_data() sẽ tự động skip để tránh rate limit
        if self.is_running:
            self._update_data()

        return self.current_metrics.copy()

    def get_feature_vector(self):
        """Get feature vector for AI model"""
        import numpy as np

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
        logger.info("SimpleCollector stopped")


if __name__ == "__main__":
    # Test
    collector = SimpleCollector()
    collector.start()

    time.sleep(2)

    metrics = collector.get_current_metrics()
    print("\nMetrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    collector.stop()
