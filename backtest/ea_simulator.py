"""
EA Simulator
Mô phỏng Box-EA trading logic cho backtest
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger

from .config import BacktestConfig


class OrderType(Enum):
    """Order types"""
    BUY = 1
    SELL = 2


class OrderStatus(Enum):
    """Order status"""
    OPEN = 1
    CLOSED = 2
    CANCELLED = 3


@dataclass
class Order:
    """Order object"""
    ticket: int
    order_type: OrderType
    open_price: float
    lot_size: float
    open_time: datetime
    take_profit: float = 0.0
    stop_loss: float = 0.0
    close_price: Optional[float] = None
    close_time: Optional[datetime] = None
    status: OrderStatus = OrderStatus.OPEN
    profit: float = 0.0
    commission: float = 0.0
    swap: float = 0.0
    comment: str = ""
    cycle_id: int = 0

    def calculate_profit(self, current_price: float, point_value: float = 1.0) -> float:
        """Calculate current profit"""
        if self.order_type == OrderType.BUY:
            profit_points = current_price - self.open_price
        else:
            profit_points = self.open_price - current_price

        profit_usd = profit_points * self.lot_size * point_value
        return profit_usd - self.commission - self.swap


@dataclass
class TradingCycle:
    """Trading cycle (chu kỳ giao dịch)"""
    cycle_id: int
    cycle_type: OrderType  # BUY or SELL
    anchor_price: float
    start_time: datetime
    period: int  # 1, 2, 3, or 0 (outside hours)
    orders: List[Order] = field(default_factory=list)
    is_active: bool = True
    total_profit: float = 0.0


class BoxEASimulator:
    """
    Simulator cho Box-EA trading logic
    """

    def __init__(self, config: BacktestConfig):
        self.config = config
        self.balance = config.initial_balance
        self.equity = config.initial_balance
        self.orders: List[Order] = []
        self.closed_orders: List[Order] = []
        self.cycles: List[TradingCycle] = []

        # State variables (mirror từ EA)
        self.anchor_price = 0.0
        self.daily_profit = 0.0
        self.daily_target_hit = False
        self.current_day = None
        self.next_ticket = 1

        # Cycle tracking
        self.active_buy_cycles = 0
        self.active_sell_cycles = 0

        # Period order counts
        self.period1_orders = 0
        self.period2_orders = 0
        self.period3_orders = 0
        self.outside_hours_orders = 0

        # Performance tracking
        self.equity_curve = []
        self.balance_curve = []
        self.trades_log = []

        logger.info(f"EA Simulator initialized with balance: ${self.balance}")

    def reset(self):
        """Reset simulator state"""
        self.balance = self.config.initial_balance
        self.equity = self.config.initial_balance
        self.orders = []
        self.closed_orders = []
        self.cycles = []
        self.daily_profit = 0.0
        self.daily_target_hit = False
        self.equity_curve = []
        self.balance_curve = []
        self.trades_log = []
        self.next_ticket = 1

    def on_tick(
        self,
        current_bar: pd.Series,
        ai_market_range: float,
        ai_imbalance: float = 0.0
    ):
        """
        Process tick (mirror OnTick() trong EA)

        Args:
            current_bar: Current OHLC bar
            ai_market_range: Market range từ AI
            ai_imbalance: Market imbalance từ AI
        """
        current_time = current_bar.name
        current_price = current_bar['close']

        # Check new day
        self._check_new_day(current_time)

        # Update all open positions
        self._update_open_positions(current_price)

        # Check TPs and SLs
        self._check_take_profits_stops(current_bar)

        # Update anchor price nếu cần
        if self.anchor_price == 0:
            self.anchor_price = current_price

        # Check if can trade
        if self.daily_target_hit:
            return

        # Get current period
        period = self._get_current_period(current_time)

        # Get period settings
        first_entry_distance, extra_distance, max_orders, tp = self._get_period_settings(period)

        # Apply AI market range
        adjusted_distance = first_entry_distance + (ai_market_range * 0.01)  # Convert points to adjustment

        # Check for new trades
        self._check_for_new_trades(
            current_price,
            current_time,
            period,
            adjusted_distance,
            extra_distance,
            max_orders,
            tp
        )

        # Track equity
        self.equity_curve.append({
            'datetime': current_time,
            'equity': self.equity,
            'balance': self.balance,
            'open_orders': len(self.orders)
        })

    def _check_new_day(self, current_time: datetime):
        """Check if new day started"""
        if self.current_day is None:
            self.current_day = current_time.date()
            return

        if current_time.date() != self.current_day:
            logger.info(f"New day: {current_time.date()}, Daily profit: ${self.daily_profit:.2f}")

            # Reset daily counters
            self.daily_profit = 0.0
            self.daily_target_hit = False
            self.period1_orders = 0
            self.period2_orders = 0
            self.period3_orders = 0
            self.outside_hours_orders = 0
            self.current_day = current_time.date()

    def _get_current_period(self, current_time: datetime) -> int:
        """Get current trading period (1, 2, 3, or 0 for outside)"""
        hour = current_time.hour

        if self.config.period1_start_hour <= hour < self.config.period1_end_hour:
            return 1
        elif self.config.period2_start_hour <= hour < self.config.period2_end_hour:
            return 2
        elif self.config.period3_start_hour <= hour < self.config.period3_end_hour:
            return 3
        else:
            return 0  # Outside hours

    def _get_period_settings(self, period: int) -> Tuple[float, float, int, float]:
        """Get settings cho current period"""
        if period == 1:
            return (
                self.config.period1_first_entry_distance,
                self.config.period1_extra_distance,
                self.config.period1_max_orders,
                self.config.period1_tp
            )
        elif period == 2:
            return (
                self.config.period2_first_entry_distance,
                self.config.period2_extra_distance,
                self.config.period2_max_orders,
                self.config.period2_tp
            )
        elif period == 3:
            return (
                self.config.period3_first_entry_distance,
                self.config.period3_extra_distance,
                self.config.period3_max_orders,
                self.config.period3_tp
            )
        else:  # Outside hours
            return (
                self.config.outside_hours_first_entry_distance,
                self.config.outside_hours_extra_distance,
                self.config.outside_hours_max_orders,
                self.config.period1_tp  # Use period1 TP as default
            )

    def _check_for_new_trades(
        self,
        current_price: float,
        current_time: datetime,
        period: int,
        first_entry_distance: float,
        extra_distance: float,
        max_orders: int,
        tp: float
    ):
        """Check và mở trades mới nếu cần"""

        # Count current orders
        buy_orders = sum(1 for o in self.orders if o.order_type == OrderType.BUY)
        sell_orders = sum(1 for o in self.orders if o.order_type == OrderType.SELL)

        # Check if can open new cycles
        if self.active_buy_cycles + self.active_sell_cycles >= self.config.max_simultaneous_cycles:
            return

        # Distance from anchor
        distance_from_anchor = abs(current_price - self.anchor_price)

        # Check for BUY signal
        if current_price < self.anchor_price - first_entry_distance:
            if buy_orders < max_orders:
                self._open_order(
                    order_type=OrderType.BUY,
                    price=current_price,
                    time=current_time,
                    lot_size=self.config.default_lot_size,
                    tp_distance=tp,
                    period=period
                )

        # Check for SELL signal
        elif current_price > self.anchor_price + first_entry_distance:
            if sell_orders < max_orders:
                self._open_order(
                    order_type=OrderType.SELL,
                    price=current_price,
                    time=current_time,
                    lot_size=self.config.default_lot_size,
                    tp_distance=tp,
                    period=period
                )

    def _open_order(
        self,
        order_type: OrderType,
        price: float,
        time: datetime,
        lot_size: float,
        tp_distance: float,
        period: int
    ) -> Optional[Order]:
        """Open new order"""

        # Calculate TP and SL
        if order_type == OrderType.BUY:
            take_profit = price + tp_distance
            stop_loss = price - self.config.stop_loss if self.config.stop_loss < 50000 else 0
        else:
            take_profit = price - tp_distance
            stop_loss = price + self.config.stop_loss if self.config.stop_loss < 50000 else 0

        # Calculate commission
        commission = self.config.commission_per_lot * lot_size

        # Create order
        order = Order(
            ticket=self.next_ticket,
            order_type=order_type,
            open_price=price,
            lot_size=lot_size,
            open_time=time,
            take_profit=take_profit,
            stop_loss=stop_loss,
            commission=commission,
            comment=f"Period{period}"
        )

        self.next_ticket += 1
        self.orders.append(order)

        # Update period counters
        if period == 1:
            self.period1_orders += 1
        elif period == 2:
            self.period2_orders += 1
        elif period == 3:
            self.period3_orders += 1
        else:
            self.outside_hours_orders += 1

        logger.debug(
            f"Opened {order_type.name} #{order.ticket} @ {price:.2f}, "
            f"TP: {take_profit:.2f}, SL: {stop_loss:.2f}"
        )

        return order

    def _update_open_positions(self, current_price: float):
        """Update all open positions"""
        total_profit = 0.0

        for order in self.orders:
            order.profit = order.calculate_profit(current_price, point_value=1.0)
            total_profit += order.profit

        self.equity = self.balance + total_profit

    def _check_take_profits_stops(self, current_bar: pd.Series):
        """Check TP and SL for all orders"""
        orders_to_close = []

        for order in self.orders:
            close_price = None
            close_reason = None

            if order.order_type == OrderType.BUY:
                # Check TP
                if order.take_profit > 0 and current_bar['high'] >= order.take_profit:
                    close_price = order.take_profit
                    close_reason = "TP"

                # Check SL
                elif order.stop_loss > 0 and current_bar['low'] <= order.stop_loss:
                    close_price = order.stop_loss
                    close_reason = "SL"

            else:  # SELL
                # Check TP
                if order.take_profit > 0 and current_bar['low'] <= order.take_profit:
                    close_price = order.take_profit
                    close_reason = "TP"

                # Check SL
                elif order.stop_loss > 0 and current_bar['high'] >= order.stop_loss:
                    close_price = order.stop_loss
                    close_reason = "SL"

            if close_price:
                orders_to_close.append((order, close_price, close_reason, current_bar.name))

        # Close orders
        for order, close_price, close_reason, close_time in orders_to_close:
            self._close_order(order, close_price, close_time, close_reason)

    def _close_order(
        self,
        order: Order,
        close_price: float,
        close_time: datetime,
        reason: str = ""
    ):
        """Close order"""
        order.close_price = close_price
        order.close_time = close_time
        order.status = OrderStatus.CLOSED
        order.profit = order.calculate_profit(close_price, point_value=1.0)

        # Update balance
        self.balance += order.profit
        self.daily_profit += order.profit

        # Move to closed orders
        self.orders.remove(order)
        self.closed_orders.append(order)

        # Log trade
        self.trades_log.append({
            'ticket': order.ticket,
            'type': order.order_type.name,
            'open_time': order.open_time,
            'open_price': order.open_price,
            'close_time': close_time,
            'close_price': close_price,
            'lot_size': order.lot_size,
            'profit': order.profit,
            'reason': reason,
            'comment': order.comment
        })

        logger.debug(
            f"Closed {order.order_type.name} #{order.ticket} @ {close_price:.2f}, "
            f"Profit: ${order.profit:.2f} ({reason})"
        )

        # Check daily target
        if self.config.enable_daily_profit_limit and self.daily_profit >= self.config.daily_profit_target:
            logger.info(f"Daily target hit! Profit: ${self.daily_profit:.2f}")
            self.daily_target_hit = True
            self._close_all_orders(close_price, close_time, "Daily Target")

    def _close_all_orders(self, current_price: float, current_time: datetime, reason: str = ""):
        """Close all open orders"""
        for order in self.orders[:]:  # Copy list vì sẽ modify
            self._close_order(order, current_price, current_time, reason)

    def get_statistics(self) -> Dict:
        """Get trading statistics"""
        if not self.closed_orders:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'gross_profit': 0.0,
                'gross_loss': 0.0,
                'net_profit': 0.0,
                'profit_factor': 0.0,
                'final_balance': self.balance,
                'final_equity': self.equity,
                'return_pct': 0.0
            }

        winning_trades = [o for o in self.closed_orders if o.profit > 0]
        losing_trades = [o for o in self.closed_orders if o.profit < 0]

        gross_profit = sum(o.profit for o in winning_trades)
        gross_loss = abs(sum(o.profit for o in losing_trades))
        net_profit = self.balance - self.config.initial_balance

        stats = {
            'total_trades': len(self.closed_orders),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': len(winning_trades) / len(self.closed_orders) * 100 if self.closed_orders else 0,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss,
            'net_profit': net_profit,
            'profit_factor': gross_profit / gross_loss if gross_loss > 0 else 0,
            'final_balance': self.balance,
            'final_equity': self.equity,
            'return_pct': (net_profit / self.config.initial_balance) * 100,
            'avg_win': gross_profit / len(winning_trades) if winning_trades else 0,
            'avg_loss': gross_loss / len(losing_trades) if losing_trades else 0,
        }

        return stats

    def get_equity_curve(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        if not self.equity_curve:
            return pd.DataFrame()

        df = pd.DataFrame(self.equity_curve)
        df = df.set_index('datetime')
        return df

    def get_trades_log(self) -> pd.DataFrame:
        """Get trades log as DataFrame"""
        if not self.trades_log:
            return pd.DataFrame()

        return pd.DataFrame(self.trades_log)
