"""
Data Loader for Backtest
Load historical market data từ nhiều nguồn (CSV, MetaTrader, Yahoo Finance, v.v.)
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Tuple
from pathlib import Path
import yfinance as yf
from loguru import logger


class DataLoader:
    """Load và xử lý historical market data"""

    def __init__(self, symbol: str = "XAUUSD"):
        self.symbol = symbol
        self.data = None

    def load_from_csv(
        self,
        filepath: str,
        date_column: str = "datetime",
        parse_dates: bool = True
    ) -> pd.DataFrame:
        """
        Load data từ CSV file

        Expected columns: datetime, open, high, low, close, volume
        """
        logger.info(f"Loading data from CSV: {filepath}")

        df = pd.read_csv(filepath)

        if parse_dates:
            df[date_column] = pd.to_datetime(df[date_column])

        df = df.sort_values(date_column).reset_index(drop=True)
        df = df.set_index(date_column)

        # Normalize column names
        df.columns = [col.lower() for col in df.columns]

        self.data = df
        logger.info(f"Loaded {len(df)} rows from {filepath}")

        return df

    def load_from_mt5_csv(self, filepath: str) -> pd.DataFrame:
        """
        Load data từ MetaTrader 5 CSV export

        MT5 format: Date,Time,Open,High,Low,Close,Volume
        """
        logger.info(f"Loading MT5 data from: {filepath}")

        df = pd.read_csv(filepath)

        # Combine Date and Time columns
        if 'Date' in df.columns and 'Time' in df.columns:
            df['datetime'] = pd.to_datetime(
                df['Date'] + ' ' + df['Time'],
                format='%Y.%m.%d %H:%M'
            )
        elif 'Date' in df.columns:
            df['datetime'] = pd.to_datetime(df['Date'])

        df = df.set_index('datetime')
        df.columns = [col.lower() for col in df.columns]

        # Drop Date, Time columns if they exist
        df = df.drop(columns=['date', 'time'], errors='ignore')

        self.data = df
        logger.info(f"Loaded {len(df)} rows from MT5 CSV")

        return df

    def load_from_yahoo(
        self,
        ticker: str = "GC=F",  # Gold Futures
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        interval: str = "5m"
    ) -> pd.DataFrame:
        """
        Load data từ Yahoo Finance

        Args:
            ticker: Symbol (GC=F for Gold, ^GSPC for S&P 500)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            interval: 1m, 5m, 15m, 1h, 1d, etc.
        """
        logger.info(f"Loading data from Yahoo Finance: {ticker}")

        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Download data
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval=interval,
            progress=False
        )

        if df.empty:
            logger.error(f"No data downloaded from Yahoo Finance for {ticker}")
            return pd.DataFrame()

        # Normalize columns
        df.columns = [col.lower() for col in df.columns]

        # Convert to points (multiply by 100 for gold)
        if ticker == "GC=F":
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col] * 100

        self.data = df
        logger.info(f"Loaded {len(df)} rows from Yahoo Finance")

        return df

    def generate_synthetic_data(
        self,
        start_date: str,
        end_date: str,
        timeframe: str = "M5",
        base_price: float = 2000.0,
        volatility: float = 0.005
    ) -> pd.DataFrame:
        """
        Generate synthetic OHLCV data cho testing

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            timeframe: M1, M5, M15, H1, H4, D1
            base_price: Starting price
            volatility: Price volatility (standard deviation)
        """
        logger.info("Generating synthetic data...")

        # Parse dates
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        # Determine frequency
        freq_map = {
            "M1": "1min",
            "M5": "5min",
            "M15": "15min",
            "M30": "30min",
            "H1": "1H",
            "H4": "4H",
            "D1": "1D"
        }
        freq = freq_map.get(timeframe, "5min")

        # Generate datetime index
        date_range = pd.date_range(start=start, end=end, freq=freq)

        # Generate random walks
        n = len(date_range)
        returns = np.random.normal(0, volatility, n)
        price = base_price * np.exp(np.cumsum(returns))

        # Generate OHLC from price
        data = []
        for i in range(n):
            # Generate open and close around base price
            noise_oc = np.random.uniform(0.999, 1.001, 2)
            open_price = price[i] * noise_oc[0]
            close_price = price[i] * noise_oc[1]

            # High must be >= max(open, close)
            base_high = max(open_price, close_price)
            high_price = base_high * np.random.uniform(1.0, 1.002)

            # Low must be <= min(open, close)
            base_low = min(open_price, close_price)
            low_price = base_low * np.random.uniform(0.998, 1.0)

            data.append({
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': np.random.randint(100, 10000)
            })

        df = pd.DataFrame(data, index=date_range)
        df.index.name = 'datetime'

        self.data = df
        logger.info(f"Generated {len(df)} synthetic data points")

        return df

    def resample_data(self, timeframe: str) -> pd.DataFrame:
        """
        Resample data sang timeframe khác

        Args:
            timeframe: M1, M5, M15, H1, H4, D1
        """
        if self.data is None:
            raise ValueError("No data loaded. Load data first.")

        freq_map = {
            "M1": "1min",
            "M5": "5min",
            "M15": "15min",
            "M30": "30min",
            "H1": "1H",
            "H4": "4H",
            "D1": "1D"
        }
        freq = freq_map.get(timeframe, "5min")

        logger.info(f"Resampling data to {timeframe}")

        # Resample OHLC
        resampled = self.data.resample(freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()

        self.data = resampled
        logger.info(f"Resampled to {len(resampled)} rows")

        return resampled

    def add_indicators(self) -> pd.DataFrame:
        """Thêm technical indicators"""
        if self.data is None:
            raise ValueError("No data loaded")

        df = self.data.copy()

        # ATR (Average True Range)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=14).mean()

        # Moving Averages
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['ema_12'] = df['close'].ewm(span=12).mean()
        df['ema_26'] = df['close'].ewm(span=26).mean()

        # Volatility
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=20).std()

        self.data = df

        return df

    def get_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """Get loaded data với optional date filter"""
        if self.data is None:
            raise ValueError("No data loaded")

        df = self.data.copy()

        if start_date:
            df = df[df.index >= start_date]
        if end_date:
            df = df[df.index <= end_date]

        return df

    def validate_data(self) -> Tuple[bool, str]:
        """Validate data quality"""
        if self.data is None:
            return False, "No data loaded"

        required_columns = ['open', 'high', 'low', 'close']
        missing_cols = [col for col in required_columns if col not in self.data.columns]

        if missing_cols:
            return False, f"Missing columns: {missing_cols}"

        # Check for nulls
        nulls = self.data[required_columns].isnull().sum()
        if nulls.sum() > 0:
            return False, f"Found null values: {nulls.to_dict()}"

        # Check OHLC validity
        invalid = (
            (self.data['high'] < self.data['low']) |
            (self.data['high'] < self.data['open']) |
            (self.data['high'] < self.data['close']) |
            (self.data['low'] > self.data['open']) |
            (self.data['low'] > self.data['close'])
        )

        if invalid.sum() > 0:
            return False, f"Found {invalid.sum()} invalid OHLC rows"

        return True, "Data validation passed"


if __name__ == "__main__":
    # Test data loader
    loader = DataLoader("XAUUSD")

    # Generate synthetic data for testing
    df = loader.generate_synthetic_data(
        start_date="2024-01-01",
        end_date="2024-12-31",
        timeframe="M5",
        base_price=2000.0,
        volatility=0.002
    )

    print(f"\nGenerated {len(df)} data points")
    print(f"\nFirst 5 rows:\n{df.head()}")
    print(f"\nLast 5 rows:\n{df.tail()}")

    # Validate
    valid, message = loader.validate_data()
    print(f"\nValidation: {message}")
