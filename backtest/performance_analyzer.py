"""
Performance Analyzer
Tính toán các metrics: Profit, Drawdown, Sharpe, Win Rate, etc.
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from loguru import logger


class PerformanceAnalyzer:
    """Phân tích performance của backtest"""

    def __init__(self, initial_balance: float = 10000.0, risk_free_rate: float = 0.04):
        self.initial_balance = initial_balance
        self.risk_free_rate = risk_free_rate

    def calculate_metrics(
        self,
        equity_curve: pd.DataFrame,
        trades_log: pd.DataFrame
    ) -> Dict:
        """
        Calculate tất cả performance metrics

        Args:
            equity_curve: DataFrame với columns [equity, balance, open_orders]
            trades_log: DataFrame với trade details

        Returns:
            Dictionary chứa all metrics
        """
        metrics = {}

        # Basic metrics
        metrics.update(self._calculate_basic_metrics(equity_curve, trades_log))

        # Drawdown metrics
        metrics.update(self._calculate_drawdown_metrics(equity_curve))

        # Risk-adjusted metrics
        metrics.update(self._calculate_risk_metrics(equity_curve))

        # Trade analysis
        metrics.update(self._calculate_trade_metrics(trades_log))

        # Time analysis
        metrics.update(self._calculate_time_metrics(trades_log))

        return metrics

    def _calculate_basic_metrics(
        self,
        equity_curve: pd.DataFrame,
        trades_log: pd.DataFrame
    ) -> Dict:
        """Calculate basic metrics"""
        if equity_curve.empty:
            return {
                'final_balance': self.initial_balance,
                'final_equity': self.initial_balance,
                'total_return': 0.0,
                'total_return_pct': 0.0
            }

        final_balance = equity_curve['balance'].iloc[-1]
        final_equity = equity_curve['equity'].iloc[-1]
        total_return = final_balance - self.initial_balance
        total_return_pct = (total_return / self.initial_balance) * 100

        return {
            'initial_balance': self.initial_balance,
            'final_balance': final_balance,
            'final_equity': final_equity,
            'total_return': total_return,
            'total_return_pct': total_return_pct,
        }

    def _calculate_drawdown_metrics(self, equity_curve: pd.DataFrame) -> Dict:
        """Calculate drawdown metrics"""
        if equity_curve.empty:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
                'max_drawdown_duration_hours': 0,
                'current_drawdown': 0.0,
                'current_drawdown_pct': 0.0
            }

        equity = equity_curve['equity'].values
        running_max = np.maximum.accumulate(equity)
        drawdown = running_max - equity
        drawdown_pct = (drawdown / running_max) * 100

        max_dd = drawdown.max()
        max_dd_pct = drawdown_pct.max()

        # Calculate drawdown duration
        max_dd_duration = self._calculate_max_dd_duration(equity_curve)

        # Current drawdown
        current_dd = running_max[-1] - equity[-1]
        current_dd_pct = (current_dd / running_max[-1]) * 100 if running_max[-1] > 0 else 0

        return {
            'max_drawdown': max_dd,
            'max_drawdown_pct': max_dd_pct,
            'max_drawdown_duration_hours': max_dd_duration,
            'current_drawdown': current_dd,
            'current_drawdown_pct': current_dd_pct
        }

    def _calculate_max_dd_duration(self, equity_curve: pd.DataFrame) -> float:
        """Calculate maximum drawdown duration in hours"""
        equity = equity_curve['equity'].values
        running_max = np.maximum.accumulate(equity)

        in_drawdown = equity < running_max
        duration = 0
        max_duration = 0
        last_time = None

        for i, (idx, is_dd) in enumerate(zip(equity_curve.index, in_drawdown)):
            if is_dd:
                if last_time is None:
                    last_time = idx
                duration += 1
            else:
                if duration > 0:
                    time_diff = (idx - last_time).total_seconds() / 3600
                    max_duration = max(max_duration, time_diff)
                duration = 0
                last_time = None

        return max_duration

    def _calculate_risk_metrics(self, equity_curve: pd.DataFrame) -> Dict:
        """Calculate risk-adjusted metrics"""
        if equity_curve.empty or len(equity_curve) < 2:
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0,
                'volatility': 0.0
            }

        # Calculate returns
        equity = equity_curve['equity']
        returns = equity.pct_change().dropna()

        if len(returns) == 0:
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'calmar_ratio': 0.0,
                'volatility': 0.0
            }

        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252 * 24)  # Assuming hourly data

        # Sharpe Ratio
        excess_returns = returns - (self.risk_free_rate / (252 * 24))
        sharpe = excess_returns.mean() / returns.std() * np.sqrt(252 * 24) if returns.std() > 0 else 0

        # Sortino Ratio (only downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()
        sortino = excess_returns.mean() / downside_std * np.sqrt(252 * 24) if downside_std > 0 else 0

        # Calmar Ratio
        total_return = (equity.iloc[-1] - equity.iloc[0]) / equity.iloc[0]
        drawdown = self._calculate_drawdown_metrics(equity_curve)
        max_dd_pct = drawdown['max_drawdown_pct']
        calmar = (total_return * 100) / max_dd_pct if max_dd_pct > 0 else 0

        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino,
            'calmar_ratio': calmar,
            'volatility': volatility,
            'volatility_pct': volatility * 100
        }

    def _calculate_trade_metrics(self, trades_log: pd.DataFrame) -> Dict:
        """Calculate trade-specific metrics"""
        if trades_log.empty:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'avg_trade': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'avg_trade_duration_hours': 0.0,
                'expectancy': 0.0
            }

        total_trades = len(trades_log)
        winning_trades = trades_log[trades_log['profit'] > 0]
        losing_trades = trades_log[trades_log['profit'] < 0]

        num_wins = len(winning_trades)
        num_losses = len(losing_trades)
        win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0

        gross_profit = winning_trades['profit'].sum() if num_wins > 0 else 0
        gross_loss = abs(losing_trades['profit'].sum()) if num_losses > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0

        avg_win = winning_trades['profit'].mean() if num_wins > 0 else 0
        avg_loss = losing_trades['profit'].mean() if num_losses > 0 else 0
        avg_trade = trades_log['profit'].mean() if total_trades > 0 else 0

        largest_win = winning_trades['profit'].max() if num_wins > 0 else 0
        largest_loss = losing_trades['profit'].min() if num_losses > 0 else 0

        # Trade duration
        if 'open_time' in trades_log.columns and 'close_time' in trades_log.columns:
            durations = (trades_log['close_time'] - trades_log['open_time']).dt.total_seconds() / 3600
            avg_duration = durations.mean() if len(durations) > 0 else 0
        else:
            avg_duration = 0

        # Expectancy
        expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

        return {
            'total_trades': total_trades,
            'winning_trades': num_wins,
            'losing_trades': num_losses,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_trade': avg_trade,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_trade_duration_hours': avg_duration,
            'expectancy': expectancy,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss
        }

    def _calculate_time_metrics(self, trades_log: pd.DataFrame) -> Dict:
        """Calculate time-based metrics"""
        if trades_log.empty or 'close_time' not in trades_log.columns:
            return {
                'trades_per_day': 0.0,
                'best_day_profit': 0.0,
                'worst_day_profit': 0.0,
                'profitable_days': 0,
                'losing_days': 0
            }

        # Group by day
        trades_log['date'] = pd.to_datetime(trades_log['close_time']).dt.date
        daily_profit = trades_log.groupby('date')['profit'].sum()

        num_days = len(daily_profit)
        trades_per_day = len(trades_log) / num_days if num_days > 0 else 0

        best_day = daily_profit.max() if len(daily_profit) > 0 else 0
        worst_day = daily_profit.min() if len(daily_profit) > 0 else 0

        profitable_days = len(daily_profit[daily_profit > 0])
        losing_days = len(daily_profit[daily_profit < 0])

        return {
            'trades_per_day': trades_per_day,
            'best_day_profit': best_day,
            'worst_day_profit': worst_day,
            'profitable_days': profitable_days,
            'losing_days': losing_days,
            'total_days': num_days
        }

    def print_report(self, metrics: Dict):
        """Print formatted performance report"""
        print("\n" + "=" * 60)
        print("BACKTEST PERFORMANCE REPORT")
        print("=" * 60)

        print("\n📊 OVERALL PERFORMANCE")
        print(f"Initial Balance:      ${metrics.get('initial_balance', 0):,.2f}")
        print(f"Final Balance:        ${metrics.get('final_balance', 0):,.2f}")
        print(f"Final Equity:         ${metrics.get('final_equity', 0):,.2f}")
        print(f"Total Return:         ${metrics.get('total_return', 0):,.2f}")
        print(f"Total Return %:       {metrics.get('total_return_pct', 0):.2f}%")

        print("\n📈 TRADE STATISTICS")
        print(f"Total Trades:         {metrics.get('total_trades', 0)}")
        print(f"Winning Trades:       {metrics.get('winning_trades', 0)}")
        print(f"Losing Trades:        {metrics.get('losing_trades', 0)}")
        print(f"Win Rate:             {metrics.get('win_rate', 0):.2f}%")
        print(f"Profit Factor:        {metrics.get('profit_factor', 0):.2f}")

        print("\n💰 PROFIT/LOSS ANALYSIS")
        print(f"Gross Profit:         ${metrics.get('gross_profit', 0):,.2f}")
        print(f"Gross Loss:           ${metrics.get('gross_loss', 0):,.2f}")
        print(f"Average Win:          ${metrics.get('avg_win', 0):,.2f}")
        print(f"Average Loss:         ${metrics.get('avg_loss', 0):,.2f}")
        print(f"Largest Win:          ${metrics.get('largest_win', 0):,.2f}")
        print(f"Largest Loss:         ${metrics.get('largest_loss', 0):,.2f}")
        print(f"Expectancy:           ${metrics.get('expectancy', 0):,.2f}")

        print("\n📉 DRAWDOWN ANALYSIS")
        print(f"Max Drawdown:         ${metrics.get('max_drawdown', 0):,.2f}")
        print(f"Max Drawdown %:       {metrics.get('max_drawdown_pct', 0):.2f}%")
        print(f"Max DD Duration:      {metrics.get('max_drawdown_duration_hours', 0):.1f} hours")
        print(f"Current Drawdown:     ${metrics.get('current_drawdown', 0):,.2f}")
        print(f"Current Drawdown %:   {metrics.get('current_drawdown_pct', 0):.2f}%")

        print("\n📊 RISK METRICS")
        print(f"Sharpe Ratio:         {metrics.get('sharpe_ratio', 0):.2f}")
        print(f"Sortino Ratio:        {metrics.get('sortino_ratio', 0):.2f}")
        print(f"Calmar Ratio:         {metrics.get('calmar_ratio', 0):.2f}")
        print(f"Volatility:           {metrics.get('volatility_pct', 0):.2f}%")

        print("\n⏰ TIME ANALYSIS")
        print(f"Total Days:           {metrics.get('total_days', 0)}")
        print(f"Profitable Days:      {metrics.get('profitable_days', 0)}")
        print(f"Losing Days:          {metrics.get('losing_days', 0)}")
        print(f"Trades per Day:       {metrics.get('trades_per_day', 0):.1f}")
        print(f"Avg Trade Duration:   {metrics.get('avg_trade_duration_hours', 0):.1f} hours")
        print(f"Best Day Profit:      ${metrics.get('best_day_profit', 0):,.2f}")
        print(f"Worst Day Profit:     ${metrics.get('worst_day_profit', 0):,.2f}")

        print("\n" + "=" * 60)

    def plot_results(
        self,
        equity_curve: pd.DataFrame,
        trades_log: pd.DataFrame,
        save_path: Optional[str] = None
    ):
        """Plot backtest results"""
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('Backtest Results', fontsize=16, fontweight='bold')

        # 1. Equity Curve
        ax = axes[0, 0]
        ax.plot(equity_curve.index, equity_curve['equity'], label='Equity', linewidth=2)
        ax.plot(equity_curve.index, equity_curve['balance'], label='Balance', linewidth=2, alpha=0.7)
        ax.set_title('Equity & Balance Curve')
        ax.set_xlabel('Date')
        ax.set_ylabel('Value ($)')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # 2. Drawdown
        ax = axes[0, 1]
        equity = equity_curve['equity'].values
        running_max = np.maximum.accumulate(equity)
        drawdown_pct = ((running_max - equity) / running_max) * 100
        ax.fill_between(equity_curve.index, 0, drawdown_pct, color='red', alpha=0.3)
        ax.set_title('Drawdown %')
        ax.set_xlabel('Date')
        ax.set_ylabel('Drawdown (%)')
        ax.grid(True, alpha=0.3)

        # 3. Trade Distribution
        if not trades_log.empty:
            ax = axes[1, 0]
            profits = trades_log['profit']
            ax.hist(profits, bins=50, edgecolor='black', alpha=0.7)
            ax.axvline(0, color='red', linestyle='--', linewidth=2)
            ax.set_title('Profit Distribution')
            ax.set_xlabel('Profit ($)')
            ax.set_ylabel('Frequency')
            ax.grid(True, alpha=0.3)

            # 4. Cumulative Profit
            ax = axes[1, 1]
            cumulative_profit = trades_log['profit'].cumsum()
            ax.plot(range(len(cumulative_profit)), cumulative_profit, linewidth=2)
            ax.set_title('Cumulative Profit')
            ax.set_xlabel('Trade Number')
            ax.set_ylabel('Cumulative Profit ($)')
            ax.grid(True, alpha=0.3)

            # 5. Daily Profits
            ax = axes[2, 0]
            trades_log['date'] = pd.to_datetime(trades_log['close_time']).dt.date
            daily_profit = trades_log.groupby('date')['profit'].sum()
            colors = ['green' if x > 0 else 'red' for x in daily_profit]
            ax.bar(range(len(daily_profit)), daily_profit, color=colors, alpha=0.7)
            ax.set_title('Daily Profit/Loss')
            ax.set_xlabel('Day')
            ax.set_ylabel('Profit ($)')
            ax.axhline(0, color='black', linestyle='-', linewidth=1)
            ax.grid(True, alpha=0.3)

            # 6. Win/Loss Ratio Pie
            ax = axes[2, 1]
            wins = len(trades_log[trades_log['profit'] > 0])
            losses = len(trades_log[trades_log['profit'] < 0])
            ax.pie([wins, losses], labels=['Wins', 'Losses'], autopct='%1.1f%%',
                   colors=['green', 'red'], startangle=90)
            ax.set_title('Win/Loss Ratio')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"Plots saved to {save_path}")

        plt.show()


if __name__ == "__main__":
    # Test analyzer
    analyzer = PerformanceAnalyzer(initial_balance=10000)

    # Generate dummy data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='1H')
    equity = 10000 + np.cumsum(np.random.randn(len(dates)) * 50)

    equity_curve = pd.DataFrame({
        'equity': equity,
        'balance': equity,
        'open_orders': np.random.randint(0, 5, len(dates))
    }, index=dates)

    # Calculate metrics
    metrics = analyzer.calculate_metrics(equity_curve, pd.DataFrame())
    analyzer.print_report(metrics)
