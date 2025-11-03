"""
Execution Tools
Order placement, position sizing, and risk management calculations.
"""

import logging
from typing import Dict, Optional
from src.connectors.alpaca_connector import alpaca_manager
from src.config.settings import settings

logger = logging.getLogger(__name__)


class ExecutionTools:
    """Tools for trade execution and risk management."""

    @staticmethod
    def calculate_position_size(signal: str, current_price: float, atr: float, account_equity: float) -> Dict:
        """
        Calculate position size based on risk parameters.

        Position Sizing Formula:
        shares = (account_equity * max_risk_per_trade) / atr

        Args:
            signal: "BUY" or "SELL"
            current_price: Current asset price
            atr: Average True Range (volatility)
            account_equity: Total account equity

        Returns:
            Dict with position size calculation
        """
        try:
            # Calculate risk-adjusted position size
            risk_amount = account_equity * settings.max_risk_per_trade

            # Position size based on ATR (volatility-adjusted)
            if atr > 0:
                shares = int(risk_amount / atr)
            else:
                # Fallback to fixed percentage
                shares = int((account_equity * 0.01) / current_price)

            # Ensure at least 1 share
            shares = max(1, shares)

            # Calculate total cost
            total_cost = shares * current_price

            # Calculate risk as percentage
            risk_pct = (shares * atr) / account_equity * 100

            return {
                "shares": shares,
                "total_cost": float(total_cost),
                "risk_amount": float(risk_amount),
                "risk_percentage": float(risk_pct),
                "price_per_share": float(current_price),
                "atr_used": float(atr),
            }

        except Exception as e:
            logger.error(f"Position size calculation failed: {e}")
            return {"shares": 1, "error": str(e)}  # Minimum fallback

    @staticmethod
    def check_portfolio_constraints() -> Dict:
        """
        Check if portfolio constraints allow new trades.

        Checks:
        1. Max open positions
        2. Daily loss limit
        3. Trading blocked status

        Returns:
            Dict with constraint check results
        """
        try:
            # Get account info
            account = alpaca_manager.get_account()

            # Get current positions
            positions = alpaca_manager.get_positions()
            num_positions = len(positions)

            # Check 1: Max positions
            can_open_position = num_positions < settings.max_open_positions

            # Check 2: Daily loss limit
            # Calculate today's P&L percentage using equity vs last_equity
            equity = account.get("equity")
            last_equity = account.get("last_equity")

            if last_equity is None or last_equity == "":
                # Cannot calculate today's P&L reliably; default to 0 and allow trading
                logger.warning("last_equity missing or empty; skipping daily loss limit check.")
                daily_loss_pct = 0.0
            else:
                try:
                    last_equity_float = float(last_equity)
                    if last_equity_float == 0:
                        logger.warning("last_equity is zero; skipping daily loss limit check.")
                        daily_loss_pct = 0.0
                    else:
                        daily_loss_pct = (float(equity) / last_equity_float) - 1.0
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid last_equity value '{last_equity}': {e}; skipping daily loss limit check.")
                    daily_loss_pct = 0.0

            # within limit if today's loss is greater than negative allowed limit
            # settings.daily_loss_limit is expressed as a fraction (e.g., 0.05 for 5%)
            within_loss_limit = daily_loss_pct > -float(settings.daily_loss_limit)

            # Check 3: Account status
            trading_allowed = not account.get("trading_blocked", False)

            # Overall approval
            approved = can_open_position and within_loss_limit and trading_allowed

            return {
                "approved": approved,
                "checks": {
                    "max_positions": {
                        "passed": can_open_position,
                        "current": num_positions,
                        "limit": settings.max_open_positions,
                    },
                    "daily_loss": {
                        "passed": within_loss_limit,
                        # Report as percentage
                        "current_loss_pct": float(daily_loss_pct * 100),
                        "limit_pct": settings.daily_loss_limit * 100,
                    },
                    "trading_status": {"passed": trading_allowed, "blocked": account.get("trading_blocked", False)},
                },
                "account_info": {"equity": account["equity"], "buying_power": account["buying_power"]},
            }

        except Exception as e:
            logger.error(f"Portfolio constraint check failed: {e}")
            return {"approved": False, "error": str(e)}

    @staticmethod
    def place_order(symbol: str, qty: int, side: str) -> Dict:
        """
        Place a market order with validation.

        Args:
            symbol: Stock symbol
            qty: Number of shares
            side: "BUY" or "SELL"

        Returns:
            Dict with order result
        """
        try:
            # Validate inputs
            if side not in ["BUY", "SELL"]:
                raise ValueError(f"Invalid side: {side}. Must be 'BUY' or 'SELL'")

            if qty <= 0:
                raise ValueError(f"Invalid quantity: {qty}. Must be positive")

            # Check constraints first
            constraints = ExecutionTools.check_portfolio_constraints()

            if not constraints["approved"]:
                logger.warning("Trade rejected by portfolio constraints")
                return {"success": False, "reason": "constraints_failed", "constraints": constraints}

            # Place order via Alpaca
            order_result = alpaca_manager.place_market_order(symbol=symbol, qty=qty, side=side)

            if order_result["status"] in ["submitted", "dry_run"]:
                logger.info(f"✓ Order executed: {side} {qty} {symbol} " f"(ID: {order_result['order_id']})")
                return {"success": True, "order": order_result, "constraints": constraints}
            else:
                logger.error(f"Order placement failed: {order_result}")
                return {"success": False, "reason": "order_failed", "details": order_result}

        except Exception as e:
            logger.error(f"Order placement error: {e}")
            return {"success": False, "reason": "exception", "error": str(e)}

    @staticmethod
    def get_position_for_symbol(symbol: str) -> Optional[Dict]:
        """
        Get current position for a specific symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dict with position info or None
        """
        try:
            positions = alpaca_manager.get_positions()

            for pos in positions:
                if pos["symbol"] == symbol:
                    return pos

            return None

        except Exception as e:
            logger.error(f"Failed to get position: {e}")
            return None


# Global instance
execution_tools = ExecutionTools()
