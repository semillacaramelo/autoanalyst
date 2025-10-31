"""
Alpaca Markets API Connector
Handles both Trading and Market Data clients with safety checks
"""
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional
import logging
from src.config.settings import settings
from src.crew.orchestrator import trading_orchestrator

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
            logger.critical(
                "DANGER: Live API URL detected but DRY_RUN=True. "
                "Forcing paper mode."
            )
            self.base_url = "https://paper-api.alpaca.markets"
            self.is_paper = True
        
        self._trading_client = None
        self._data_client = None
        
        logger.info(
            f"AlpacaManager initialized (mode: {'PAPER' if self.is_paper else 'LIVE'})"
        )
    
    @property
    def trading_client(self) -> TradingClient:
        """Lazy-loaded trading client."""
        if not self._trading_client:
            self._trading_client = TradingClient(
                api_key=self.api_key,
                secret_key=self.secret_key,
                paper=self.is_paper
            )
            logger.debug("Trading client initialized")
        return self._trading_client
    
    @property
    def data_client(self) -> StockHistoricalDataClient:
        """Lazy-loaded market data client."""
        if not self._data_client:
            self._data_client = StockHistoricalDataClient(
                api_key=self.api_key,
                secret_key=self.secret_key
            )
            logger.debug("Data client initialized")
        return self._data_client
    
    def get_account(self) -> dict:
        """
        Get account information.
        
        Returns:
            Dict with keys: equity, buying_power, cash, portfolio_value
        """
        try:
            trading_orchestrator.global_rate_limiter.register_api_call('alpaca')
            account = self.trading_client.get_account()
            return {
                "equity": float(account.equity),
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "status": account.status,
                "trading_blocked": account.trading_blocked
            }
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise
    
    def fetch_historical_bars(
        self,
        symbol: str,
        timeframe: str = "1Min",
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Fetch historical OHLCV data.
        
        Args:
            symbol: Stock symbol (e.g., "SPY")
            timeframe: Bar timeframe ("1Min", "5Min", "1Hour", etc.)
            limit: Number of bars to fetch
        
        Returns:
            DataFrame with columns: open, high, low, close, volume
        """
        try:
            trading_orchestrator.global_rate_limiter.register_api_call('alpaca')
            # Improved timeframe parsing
            import re
            timeframe_lower = timeframe.lower()
            # This regex handles formats like "1m", "5Min", "1Hour", "1h", "1 day", "1d"
            match = re.match(r'(\d+)\s*(m|min|h|hour|d|day)', timeframe_lower)
            if not match:
                raise ValueError(f"Invalid timeframe format: {timeframe}")

            amount = int(match.group(1))
            unit_str = match.group(2)

            if 'm' in unit_str:
                tf_unit = TimeFrameUnit.Minute
            elif 'h' in unit_str:
                tf_unit = TimeFrameUnit.Hour
            elif 'd' in unit_str:
                tf_unit = TimeFrameUnit.Day
            else:
                raise ValueError(f"Unrecognized timeframe unit in: {timeframe}")

            tf = TimeFrame(amount, tf_unit)
            
            # Calculate start/end times
            end = datetime.now()
            # Rough estimate: for 1Min bars, go back limit minutes
            start = end - timedelta(minutes=limit * amount)
            
            request_params = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=tf,
                start=start,
                end=end
            )
            
            bars = self.data_client.get_stock_bars(request_params)
            df = bars.df
            
            # Flatten multi-index if present
            if isinstance(df.index, pd.MultiIndex):
                df = df.reset_index(level=0, drop=True)
            
            logger.info(
                f"Fetched {len(df)} bars for {symbol} ({timeframe})"
            )
            return df
        
        except Exception as e:
            logger.error(f"Failed to fetch bars: {e}")
            raise
    
    def place_market_order(
        self,
        symbol: str,
        qty: int,
        side: str  # "BUY" or "SELL"
    ) -> dict:
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
            logger.warning(
                f"DRY RUN: Would place {side} order for {qty} {symbol}"
            )
            return {
                "status": "dry_run",
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "order_id": "DRY_RUN_123"
            }
        
        try:
            trading_orchestrator.global_rate_limiter.register_api_call('alpaca')
            order_request = MarketOrderRequest(
                symbol=symbol,
                qty=qty,
                side=OrderSide[side.upper()],
                time_in_force=TimeInForce.DAY
            )
            
            order = self.trading_client.submit_order(order_request)
            
            logger.info(
                f"Order placed: {symbol} {side} {qty} shares (ID: {order.id})"
            )
            
            return {
                "status": "submitted",
                "symbol": symbol,
                "qty": qty,
                "side": side,
                "order_id": order.id,
                "submitted_at": order.submitted_at,
                "filled_avg_price": order.filled_avg_price
            }
        
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def get_positions(self) -> list:
        """Get all open positions."""
        try:
            trading_orchestrator.global_rate_limiter.register_api_call('alpaca')
            positions = self.trading_client.get_all_positions()
            return [
                {
                    "symbol": p.symbol,
                    "qty": int(p.qty),
                    "side": "long" if int(p.qty) > 0 else "short",
                    "market_value": float(p.market_value),
                    "avg_entry_price": float(p.avg_entry_price),
                    "unrealized_pl": float(p.unrealized_pl)
                }
                for p in positions
            ]
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    def get_recent_orders(self, limit: int = 10) -> list:
        """Get recent closed orders."""
        try:
            trading_orchestrator.global_rate_limiter.register_api_call('alpaca')
            request = GetOrdersRequest(
                status=QueryOrderStatus.CLOSED,
                limit=limit
            )
            orders = self.trading_client.get_orders(request)
            
            return [
                {
                    "order_id": o.id,
                    "symbol": o.symbol,
                    "side": o.side.value,
                    "qty": int(o.qty),
                    "filled_avg_price": float(o.filled_avg_price) if o.filled_avg_price else None,
                    "status": o.status.value,
                    "submitted_at": o.submitted_at,
                    "filled_at": o.filled_at
                }
                for o in orders
            ]
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise


# Global singleton
alpaca_manager = AlpacaConnectionManager()
