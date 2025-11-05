"""
Simple REST API-based collector (fallback for WebSocket issues)
Thu thập data từ Binance REST API thay vì WebSocket
"""
from binance.client import Client
from datetime import datetime
import time
from collections import deque
from loguru import logger


class SimpleCollector:
    """Simple collector using REST API polling instead of WebSocket"""

    def __init__(self):
        self.client = Client()  # No auth needed for public data
        self.symbol = 'PAXGUSDT'
        self.trades_buffer = deque(maxlen=1000)
        self.seen_trade_ids = set()  # Track để tránh duplicate
        self.is_running = False

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

            logger.info(f"Data updated: {len(self.trades_buffer)} total trades in buffer | {new_trades_count} new trades added")

        except Exception as e:
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
        import numpy as np
        price_volatility = np.std(prices) if len(prices) > 1 else 0

        # Calculate buy/sell volume
        buy_volume = sum(t['quantity'] for t in recent_trades if not t['is_buyer_maker'])
        sell_volume = sum(t['quantity'] for t in recent_trades if t['is_buyer_maker'])
        total_volume = buy_volume + sell_volume

        logger.debug(f"Price Range: {price_range:.2f} ({price_range_pct:.4f}%) | Volatility: {price_volatility:.2f}")
        logger.debug(f"Buy: {buy_volume}, Sell: {sell_volume}, Total: {total_volume}")

        # Volume imbalance
        volume_imbalance = (buy_volume - sell_volume) / total_volume if total_volume > 0 else 0

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
        # Update data before returning
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
