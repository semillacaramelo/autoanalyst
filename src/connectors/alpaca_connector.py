"""
Alpaca Markets API Connector
Handles both Trading and Market Data clients with safety checks
"""

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient, CryptoHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging
from src.config.settings import settings
from src.utils.asset_classifier import AssetClassifier

logger = logging.getLogger(__name__)


class AlpacaConnectionManager:
    """
    Manages connections to Alpaca Trading and Market Data APIs.
    Includes safety checks for paper trading mode.
    """

    def __init__(self):
        self.api_key = settings.alpaca_api_key
        self.secret_key = settings.alpaca_secret_key
        self.base_url = settings.alpaca_base_url

        # Safety check
        self.is_paper = "paper" in self.base_url.lower()
        if not self.is_paper and settings.dry_run:
            logger.critical("DANGER: Live API URL detected but DRY_RUN=True. " "Forcing paper mode.")
            self.base_url = "https://paper-api.alpaca.markets"
            self.is_paper = True

        self._trading_client = None
        self._data_client = None
        self._crypto_client = None

        logger.info(f"AlpacaManager initialized (mode: {'PAPER' if self.is_paper else 'LIVE'})")

    @property
    def trading_client(self) -> TradingClient:
        """Lazy-loaded trading client."""
        if not self._trading_client:
            self._trading_client = TradingClient(api_key=self.api_key, secret_key=self.secret_key, paper=self.is_paper)
            logger.debug("Trading client initialized")
        return self._trading_client

    @property
    def data_client(self) -> StockHistoricalDataClient:
        """Lazy-loaded market data client."""
        if not self._data_client:
            self._data_client = StockHistoricalDataClient(api_key=self.api_key, secret_key=self.secret_key)
            logger.debug("Data client initialized")
        return self._data_client

    @property
    def crypto_client(self) -> CryptoHistoricalDataClient:
        """Lazy-loaded crypto data client."""
        if not self._crypto_client:
            self._crypto_client = CryptoHistoricalDataClient(api_key=self.api_key, secret_key=self.secret_key)
            logger.debug("Crypto client initialized")
        return self._crypto_client

    def get_account(self) -> dict:
        """
        Get account information.

        Returns:
            Dict with keys: equity, buying_power, cash, portfolio_value
        """
        try:
            account = self.trading_client.get_account()
            return {
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "status": account.status,
                "trading_blocked": account.trading_blocked,
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise

    def fetch_historical_bars(
        self,
        symbol: str,
        timeframe: str = "1Min",
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 100,
        asset_class: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data with automatic asset class detection.

        Args:
            symbol: Symbol to fetch (e.g., "SPY", "BTC/USD", "EUR/USD")
            timeframe: Bar timeframe ("1Min", "5Min", "1Hour", etc.)
            start: Start date string (YYYY-MM-DD)
            end: End date string (YYYY-MM-DD)
            limit: Number of bars to fetch if start/end are not provided
            asset_class: Optional asset class override ("US_EQUITY", "CRYPTO", "FOREX").
                        If None, auto-detects from symbol.

        Returns:
            DataFrame with columns: open, high, low, close, volume (and others)
        """
        # Auto-detect asset class if not provided
        if asset_class is None:
            try:
                classification = AssetClassifier.classify(symbol)
                asset_class = classification["type"]
                logger.debug(f"Auto-detected {symbol} as {asset_class}")
            except ValueError as e:
                logger.error(f"Failed to classify symbol {symbol}: {e}")
                raise

        # Route to appropriate client based on asset class
        if asset_class == "CRYPTO":
            return self._fetch_crypto_bars(symbol, timeframe, start, end, limit)
        elif asset_class == "FOREX":
            # Forex not yet implemented, but placeholder for future
            raise NotImplementedError("Forex data fetching not yet implemented. " "Alpaca forex support is in beta.")
        else:  # US_EQUITY
            return self._fetch_stock_bars(symbol, timeframe, start, end, limit)

    def _fetch_stock_bars(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[str],
        end: Optional[str],
        limit: int,
    ) -> pd.DataFrame:
        """
        Fetch stock (equity) historical bars.

        (Original implementation from fetch_historical_bars)
        """
        try:
            # Improved timeframe parsing
            import re

            timeframe_lower = timeframe.lower()
            # This regex handles formats like "1m", "5Min", "1Hour", "1h", "1 day", "1d"
            match = re.match(r"(\d+)\s*(m|min|h|hour|d|day)", timeframe_lower)
            if not match:
                raise ValueError(f"Invalid timeframe format: {timeframe}")

            amount = int(match.group(1))
            unit_str = match.group(2)

            if "m" in unit_str:
                tf_unit = TimeFrameUnit.Minute
            elif "h" in unit_str:
                tf_unit = TimeFrameUnit.Hour
            elif "d" in unit_str:
                tf_unit = TimeFrameUnit.Day
            else:
                raise ValueError(f"Unrecognized timeframe unit in: {timeframe}")

            tf = TimeFrame(amount, tf_unit)

            # Calculate start/end times
            if start and end:
                start_dt = pd.to_datetime(start)
                if start_dt.tzinfo is None or start_dt.tzinfo.utcoffset(start_dt) is None:
                    start_dt = start_dt.tz_localize("America/New_York")
                else:
                    start_dt = start_dt.tz_convert("America/New_York")
                end_dt = pd.to_datetime(end)
                if end_dt.tzinfo is None or end_dt.tzinfo.utcoffset(end_dt) is None:
                    end_dt = end_dt.tz_localize("America/New_York")
                else:
                    end_dt = end_dt.tz_convert("America/New_York")
            else:
                end_dt = datetime.now()
                if tf_unit == TimeFrameUnit.Day:
                    start_dt = end_dt - timedelta(days=limit * amount)
                elif tf_unit == TimeFrameUnit.Hour:
                    start_dt = end_dt - timedelta(hours=limit * amount)
                else:  # Minute
                    start_dt = end_dt - timedelta(minutes=limit * amount)

            request_params = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=tf,
                start=start_dt,
                end=end_dt,
                feed=settings.alpaca_data_feed,
            )

            bars = self.data_client.get_stock_bars(request_params)
            df = bars.df

            # Flatten multi-index if present
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index(level=0, drop=True)

            logger.info(f"Fetched {len(df)} bars for {symbol} ({timeframe}) from {start_dt} to {end_dt}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch stock bars: {e}")
            raise

    def _fetch_crypto_bars(
        self,
        symbol: str,
        timeframe: str,
        start: Optional[str],
        end: Optional[str],
        limit: int,
    ) -> pd.DataFrame:
        """
        Fetch cryptocurrency historical bars.

        Uses CryptoHistoricalDataClient with crypto-specific requests.
        Crypto data is available 24/7 with no market hours restrictions.

        Note: Alpaca crypto API requires symbols with slash (BTC/USD, not BTCUSD)
        """
        try:
            # Normalize crypto symbol to slash format (Alpaca requirement)
            if "/" not in symbol:
                # BTCUSD → BTC/USD, ETHUSD → ETH/USD, BTCUSDT → BTC/USDT
                if symbol.endswith("USDT"):
                    base = symbol[:-4]  # Remove USDT
                    symbol = f"{base}/USDT"
                elif symbol.endswith("USD"):
                    base = symbol[:-3]  # Remove USD
                    symbol = f"{base}/USD"
                else:
                    raise ValueError(f"Cannot normalize crypto symbol: {symbol}")
                logger.debug(f"Normalized crypto symbol to: {symbol}")

            # Parse timeframe (same logic as stocks)
            import re

            timeframe_lower = timeframe.lower()
            match = re.match(r"(\d+)\s*(m|min|h|hour|d|day)", timeframe_lower)
            if not match:
                raise ValueError(f"Invalid timeframe format: {timeframe}")

            amount = int(match.group(1))
            unit_str = match.group(2)

            if "m" in unit_str:
                tf_unit = TimeFrameUnit.Minute
            elif "h" in unit_str:
                tf_unit = TimeFrameUnit.Hour
            elif "d" in unit_str:
                tf_unit = TimeFrameUnit.Day
            else:
                raise ValueError(f"Unrecognized timeframe unit in: {timeframe}")

            tf = TimeFrame(amount, tf_unit)

            # Calculate start/end times (crypto is 24/7, use UTC)
            if start and end:
                start_dt = pd.to_datetime(start)
                if start_dt.tzinfo is None or start_dt.tzinfo.utcoffset(start_dt) is None:
                    start_dt = start_dt.tz_localize("UTC")
                else:
                    start_dt = start_dt.tz_convert("UTC")
                end_dt = pd.to_datetime(end)
                if end_dt.tzinfo is None or end_dt.tzinfo.utcoffset(end_dt) is None:
                    end_dt = end_dt.tz_localize("UTC")
                else:
                    end_dt = end_dt.tz_convert("UTC")
            else:
                end_dt = datetime.now()
                if tf_unit == TimeFrameUnit.Day:
                    start_dt = end_dt - timedelta(days=limit * amount)
                elif tf_unit == TimeFrameUnit.Hour:
                    start_dt = end_dt - timedelta(hours=limit * amount)
                else:  # Minute
                    start_dt = end_dt - timedelta(minutes=limit * amount)

            # Use CryptoBarsRequest (different from StockBarsRequest)
            request_params = CryptoBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=tf,
                start=start_dt,
                end=end_dt,
            )

            bars = self.crypto_client.get_crypto_bars(request_params)
            df = bars.df

            # Flatten multi-index if present
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index(level=0, drop=True)

            logger.info(f"Fetched {len(df)} crypto bars for {symbol} ({timeframe}) from {start_dt} to {end_dt}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch crypto bars: {e}")
            raise

    def place_market_order(self, symbol: str, qty: int, side: str) -> dict:  # "BUY" or "SELL"
        """
        Place a market order.

        Args:
            symbol: Stock symbol
            qty: Quantity of shares
            side: "BUY" or "SELL"

        Returns:
            Dict with order details
        """
        if settings.dry_run:
            logger.warning(f"DRY RUN: Would place {side} order for {qty} {symbol}")
            return {
                "status": "dry_run",
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "order_id": "DRY_RUN_123",
            }

        try:
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide[side.upper()],
                time_in_force=TimeInForce.DAY,
            )

            order = self.trading_client.submit_order(order_request)

            logger.info(f"Order placed: {symbol} {side} {qty} shares (ID: {order.id})")

            return {
                "status": "submitted",
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "order_id": order.id,
                "submitted_at": order.submitted_at,
                "filled_avg_price": order.filled_avg_price,
            }

        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    def get_positions(self) -> list:
        """Get all open positions."""
        try:
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": int(p.qty),
                    "side": "long" if int(p.qty) > 0 else "short",
                    "market_value": float(p.market_value),
                    "avg_entry_price": float(p.avg_entry_price),
                    "unrealized_pl": float(p.unrealized_pl),
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_recent_orders(self, limit: int = 10) -> list:
        """Get recent closed orders."""
        try:
            request = GetOrdersRequest(status=QueryOrderStatus.CLOSED, limit=limit)
            orders = self.trading_client.get_orders(request)

            return [
                {
                    "order_id": o.id,
                    "symbol": o.symbol,
                    "side": o.side.value,
                    "qty": int(o.qty),
                    "filled_avg_price": (float(o.filled_avg_price) if o.filled_avg_price else None),
                    "status": o.status.value,
                    "submitted_at": o.submitted_at,
                    "filled_at": o.filled_at,
                }
                for o in orders
            ]
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise


# Global singleton
alpaca_manager = AlpacaConnectionManager()
