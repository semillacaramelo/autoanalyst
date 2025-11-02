"""Asset Universe Management

Manages tradable asset universes across multiple markets (US Equity, Crypto, Forex).
Supports both static (pre-defined) and dynamic (API-fetched) universes.

Usage:
    from src.tools.universe_manager import UniverseManager
    
    manager = UniverseManager()
    equity_symbols = manager.get_active_universe("US_EQUITY")  # Returns S&P 100
    crypto_symbols = manager.get_active_universe("CRYPTO")     # Returns top 20 crypto by volume
"""

import logging
from typing import List, Dict
from src.connectors.alpaca_connector import alpaca_manager
from alpaca.trading.enums import AssetClass, AssetStatus

logger = logging.getLogger(__name__)

# Import S&P 100 from existing market scan tools
from src.tools.market_scan_tools import SP_100_SYMBOLS


class UniverseManager:
    """Manages tradable asset universes across multiple markets."""
    
    # Universe definitions with metadata
    UNIVERSES = {
        "US_EQUITY": {
            "source": "static",  # Pre-defined list
            "symbols": SP_100_SYMBOLS,
            "min_volume": 1_000_000,  # shares/day
            "active_hours": "US_EQUITY",
            "description": "S&P 100 large-cap US equities"
        },
        "CRYPTO": {
            "source": "dynamic",  # Fetch from Alpaca API
            "filters": {
                "min_volume_24h": 5_000_000,  # $5M USD volume/day (relaxed for testing)
                "exclude": ["SHIB/USD", "SHIB/USDT"],  # Optional blacklist
                "preferred_quote": "USD"  # Prefer USD over USDT pairs
            },
            "active_hours": "CRYPTO",  # 24/7
            "description": "Top cryptocurrencies by volume"
        },
        "FOREX": {
            "source": "static",
            "symbols": ["EUR/USD", "GBP/USD", "USD/JPY", "AUD/USD", "USD/CAD", "NZD/USD"],
            "active_hours": "FOREX",
            "description": "Major forex currency pairs"
        }
    }
    
    def __init__(self):
        """Initialize UniverseManager."""
        self._crypto_cache = None  # Cache for dynamic crypto universe
        self._cache_timestamp = None
        logger.debug("UniverseManager initialized")
    
    def get_active_universe(self, market: str, max_symbols: int = None) -> List[str]:
        """
        Returns list of symbols for the given market.
        
        Args:
            market: Market name ("US_EQUITY", "CRYPTO", "FOREX")
            max_symbols: Optional limit on number of symbols (for dynamic universes)
        
        Returns:
            List of symbol strings
        
        Examples:
            >>> manager = UniverseManager()
            >>> manager.get_active_universe("US_EQUITY")
            ['AAPL', 'MSFT', 'AMZN', ...]  # 100 symbols
            
            >>> manager.get_active_universe("CRYPTO", max_symbols=10)
            ['BTC/USD', 'ETH/USD', 'SOL/USD', ...]  # Top 10 by volume
        """
        if market not in self.UNIVERSES:
            logger.error(f"Unknown market: {market}")
            return []
        
        universe_config = self.UNIVERSES[market]
        
        if universe_config["source"] == "static":
            symbols = universe_config["symbols"]
            if max_symbols:
                symbols = symbols[:max_symbols]
            logger.info(f"Loaded {len(symbols)} symbols from {market} (static)")
            return symbols
        
        elif universe_config["source"] == "dynamic":
            symbols = self._fetch_dynamic_universe(market, universe_config["filters"])
            if max_symbols:
                symbols = symbols[:max_symbols]
            logger.info(f"Loaded {len(symbols)} symbols from {market} (dynamic)")
            return symbols
        
        else:
            logger.error(f"Unknown source type: {universe_config['source']}")
            return []
    
    def _fetch_dynamic_universe(self, market: str, filters: Dict) -> List[str]:
        """
        Fetch tradable assets from Alpaca API with filters.
        
        For CRYPTO:
            1. Get all crypto assets from Alpaca Trading API
            2. Filter by tradable, active status
            3. Apply volume and blacklist filters
            4. Return sorted by symbol name
        
        Args:
            market: Market name (currently only "CRYPTO" supported)
            filters: Filter criteria dict
        
        Returns:
            List of symbol strings
        """
        if market == "CRYPTO":
            return self._fetch_crypto_universe(filters)
        else:
            logger.error(f"Dynamic universe not implemented for {market}")
            return []
    
    def _fetch_crypto_universe(self, filters: Dict) -> List[str]:
        """
        Fetch tradable crypto assets from Alpaca.
        
        Uses Alpaca Trading API to get all available crypto assets.
        Filters by:
        - AssetClass.CRYPTO
        - AssetStatus.ACTIVE
        - Tradable flag
        - Exclusion list
        - Preferred quote currency
        
        Returns:
            List of crypto symbols (e.g., ['BTC/USD', 'ETH/USD', ...])
        """
        try:
            # Get all assets from Alpaca Trading API
            # Note: Alpaca may return new asset classes (crypto_perp) not in SDK enum
            # We use try-except to handle validation errors gracefully
            try:
                all_assets = alpaca_manager.trading_client.get_all_assets()
            except Exception as validation_error:
                logger.warning(
                    f"Alpaca API returned unsupported asset classes (likely crypto_perp). "
                    f"Using fallback. Error: {validation_error}"
                )
                raise  # Re-raise to trigger fallback
            
            # Filter for active, tradable crypto
            crypto_assets = [
                asset for asset in all_assets
                if (
                    asset.asset_class == AssetClass.CRYPTO and
                    asset.status == AssetStatus.ACTIVE and
                    asset.tradable and
                    asset.symbol not in filters.get("exclude", [])
                )
            ]
            
            # Prefer USD quote currency if specified
            if filters.get("preferred_quote") == "USD":
                # Prioritize /USD pairs, then /USDT
                usd_pairs = [a for a in crypto_assets if a.symbol.endswith("/USD")]
                usdt_pairs = [a for a in crypto_assets if a.symbol.endswith("/USDT") 
                             and not any(u.symbol.replace("/USD", "") == a.symbol.replace("/USDT", "") 
                                        for u in usd_pairs)]
                crypto_assets = usd_pairs + usdt_pairs
            
            # Extract symbols
            symbols = [asset.symbol for asset in crypto_assets]
            
            # Sort alphabetically for consistency
            symbols.sort()
            
            logger.info(f"Fetched {len(symbols)} crypto assets from Alpaca API")
            
            # Log first 10 for debugging
            if symbols:
                logger.debug(f"Top 10 crypto: {symbols[:10]}")
            
            return symbols if symbols else self._get_fallback_crypto()
            
        except Exception as e:
            logger.error(f"Failed to fetch crypto universe: {e}")
            return self._get_fallback_crypto()
    
    def _get_fallback_crypto(self) -> List[str]:
        """
        Return fallback list of major cryptocurrencies.
        
        Used when Alpaca API is unavailable or returns validation errors.
        Based on Alpaca crypto verification (62 tradable pairs confirmed).
        """
        fallback = [
            "BTC/USD", "ETH/USD", "SOL/USD", "ADA/USD", "AVAX/USD",
            "DOT/USD", "MATIC/USD", "LINK/USD", "UNI/USD", "ATOM/USD",
            "XRP/USD", "LTC/USD", "BCH/USD", "ALGO/USD", "AAVE/USD"
        ]
        logger.warning(f"Using fallback crypto universe ({len(fallback)} symbols)")
        return fallback
    
    def get_universe_info(self, market: str) -> Dict:
        """
        Get metadata about a universe.
        
        Returns:
            Dict with universe configuration and metadata
        """
        if market not in self.UNIVERSES:
            return {}
        return self.UNIVERSES[market]
    
    def list_available_markets(self) -> List[str]:
        """
        List all available markets.
        
        Returns:
            List of market names
        """
        return list(self.UNIVERSES.keys())


# Global singleton instance
universe_manager = UniverseManager()
