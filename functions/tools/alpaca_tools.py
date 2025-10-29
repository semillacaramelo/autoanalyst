from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
import pandas as pd
from config.config import ALPACA_CONFIG
from typing import Optional, List, Dict, Any

def get_alpaca_trading_client() -> Optional[TradingClient]:
    """Initializes and returns an Alpaca TradingClient."""
    try:
        client = TradingClient(ALPACA_CONFIG['key_id'], ALPACA_CONFIG['secret_key'], paper=ALPACA_CONFIG['paper'])
        client.get_account()
        print("Successfully connected to Alpaca Trading API.")
        return client
    except Exception as e:
        print(f"Error connecting to Alpaca Trading API: {e}")
        return None

def fetch_historical_data(symbol: str, timeframe: TimeFrame, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """Fetches historical OHLCV data for a given symbol."""
    client = StockHistoricalDataClient(ALPACA_CONFIG['key_id'], ALPACA_CONFIG['secret_key'])
    try:
        request_params = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=timeframe,
            start=pd.to_datetime(start_date),
            end=pd.to_datetime(end_date)
        )
        bars = client.get_stock_bars(request_params)
        print(f"Successfully fetched {len(bars.df)} bars for {symbol}.")
        return bars.df
    except Exception as e:
        print(f"Error fetching historical data for {symbol}: {e}")
        return None

def fetch_1_minute_historical_data(symbol: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
    """A specialized tool that fetches only 1-minute historical data."""
    return fetch_historical_data(symbol, TimeFrame.Minute, start_date, end_date)

def place_market_order(symbol: str, qty: float, side: str):
    """Places a market order via the Alpaca API."""
    trading_client = get_alpaca_trading_client()
    if not trading_client:
        return None

    try:
        market_order_data = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide[side.upper()],
            time_in_force=TimeInForce.DAY
        )
        market_order = trading_client.submit_order(order_data=market_order_data)
        print(f"Market order placed for {symbol}: {market_order.id}")
        return market_order
    except Exception as e:
        print(f"Error placing market order for {symbol}: {e}")
        return None

def get_trade_history() -> List[Dict[str, Any]]:
    """Retrieves closed orders/trade history from Alpaca."""
    trading_client = get_alpaca_trading_client()
    if not trading_client:
        raise Exception("Could not connect to Alpaca.")
    try:
        request_params = GetOrdersRequest(status=QueryOrderStatus.CLOSED)
        closed_orders = trading_client.get_orders(filter=request_params)
        history = [
            {
                "symbol": order.symbol,
                "qty": order.filled_qty,
                "side": order.side.value,
                "avg_fill_price": order.filled_avg_price,
                "status": order.status.value,
            }
            for order in closed_orders
        ]
        return history
    except Exception as e:
        raise Exception(f"Error fetching trade history from Alpaca: {e}")
