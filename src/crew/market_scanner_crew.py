"""
MarketScannerCrew orchestrates the asset selection process using specialized agents.
"""

from src.agents.scanner_agents import (
    VolatilityAnalyzerAgent,
    TechnicalSetupAgent,
    LiquidityFilterAgent,
    SectorRotationAgent,
)
from src.tools.market_scan_tools import (
    scan_volatility,
    scan_technical_setups,
    scan_liquidity,
    scan_sector_rotation,
)
from datetime import datetime

class MarketScannerCrew:
    def __init__(self):
        self.volatility_agent = VolatilityAnalyzerAgent(scan_volatility)
        self.technical_agent = TechnicalSetupAgent(scan_technical_setups)
        self.liquidity_agent = LiquidityFilterAgent(scan_liquidity)
        self.sector_agent = SectorRotationAgent(scan_sector_rotation)

    def run(self):
        # Step 1: Scan volatility
        volatility_results = self.volatility_agent.scan()
        # Step 2: Technical setups
        technical_results = self.technical_agent.scan(volatility_results["candidates"])
        # Step 3: Liquidity filter
        liquidity_results = self.liquidity_agent.scan(technical_results["candidates"])
        # Step 4: Sector rotation (optional)
        sector_results = self.sector_agent.scan(liquidity_results["candidates"])

        # Aggregate and score
        top_assets = []
        for asset in sector_results["candidates"]:
            top_assets.append({
                "symbol": asset["symbol"],
                "priority": asset.get("priority", 1),
                "volatility_score": asset.get("volatility_score", 0),
                "technical_score": asset.get("technical_score", 0),
                "liquidity_score": asset.get("liquidity_score", 0),
                "recommended_strategies": asset.get("recommended_strategies", []),
                "reason": asset.get("reason", ""),
            })

        avoid_assets = sector_results.get("avoid_assets", [])

        return {
            "scan_timestamp": datetime.utcnow().isoformat(),
            "market_condition": sector_results.get("market_condition", "unknown"),
            "top_assets": top_assets[:7],
            "avoid_assets": avoid_assets,
        }
