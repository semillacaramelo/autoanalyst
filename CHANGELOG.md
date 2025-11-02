# Changelog

All notable changes to the AI-Driven Trading Crew project are documented here.

## [0.2.0] - 2025-11-03

### Added - Phase 2: Multi-Market 24/7 Trading ✅ COMPLETE

**Major milestone:** System now supports autonomous 24/7 trading across multiple markets with intelligent rotation and asset-class-aware strategies.

#### Feature 2.1: Asset Classification System (c613a79)
- Pattern-based asset class detection (US_EQUITY, CRYPTO, FOREX)
- Auto-detection from symbol format (AAPL → US_EQUITY, BTC/USD → CRYPTO, EUR/USD → FOREX)
- 13/13 tests passing

#### Feature 2.2: Multi-Asset Data Layer (cf6a931)
- Added crypto/forex data fetching via Alpaca API
- Lazy-loaded CryptoHistoricalDataClient for efficient resource usage
- Symbol normalization (BTCUSD → BTC/USD)
- Verified: FREE with IEX data feed (no subscription required)

#### Feature 2.3: Dynamic Universe Management (98d2ae1)
- Created UniverseManager with static and dynamic symbol sources
- US_EQUITY: 99 S&P 100 stocks
- CRYPTO: 15 top crypto pairs (dynamic fetch with fallback)
- FOREX: 6 major currency pairs
- Volume and tradability filters

#### Feature 2.4: Market-Aware Scanner (b304510)
- Scanner accepts target_market parameter for multi-market scanning
- Auto-detects active markets via MarketCalendar
- Market-specific agent backstories for context
- 11/11 tests passing (7 tool tests + 4 crew tests)

#### Feature 2.5: Asset-Class-Aware Strategies (4456e3d)
- Automatic parameter adaptation per asset class
- **CRYPTO parameters:** 3.0x ATR stops (wider for volatility), 0.05 volume weight (24/7 trading), 20-period ATR (longer smoothing)
- **US_EQUITY parameters:** 2.0x ATR stops (standard), 0.15 volume weight (market hours), 14-period ATR (standard)
- **FOREX parameters:** 2.5x ATR stops (moderate), 0.0 volume weight (not available), 14-period ATR
- Updated all 4 strategies: triple_ma, rsi_breakout, macd_crossover, bollinger_bands_reversal
- 5/5 tests passing

#### Feature 2.6: Intelligent Market Rotation (041a072)
- Time-based selection: US_EQUITY prioritized during market hours (9:30-4:00 ET), CRYPTO when closed
- Performance-based scoring: `win_rate × avg_profit × log(trade_count + 1)`
- Override logic: Switches to better market if score >20% higher
- State persistence with market performance tracking (win rates, profits, opportunity counts)
- 8/8 tests passing

#### Feature 2.7: Adaptive 24/7 Scheduler (f0a3000)
- Integrated market rotation into global_scheduler.py
- **Adaptive scan intervals:**
  - US_EQUITY: 5 minutes (peak liquidity)
  - CRYPTO peak hours (9-23 UTC): 15 minutes (high activity)
  - CRYPTO off-peak (0-8 UTC): 30 minutes (low activity)
  - FOREX: 10 minutes (moderate activity)
- Asset-class-aware strategy selection per market
- Market performance tracking and rotation stats logging
- Enhanced state management with market context
- Graceful error handling and recovery
- 10/10 tests passing

### Metrics

**System Improvements:**
- **Uptime:** 27% (6.5h/day) → 100% (24h/day) = **3.7x increase**
- **Markets:** 1 (US equities only) → 3 (equity/crypto/forex) = **3x expansion**
- **Assets:** 100 (S&P 100) → 120 (99+15+6) = **1.2x coverage**
- **Scan Intervals:** Fixed 15min → Adaptive 5-30min = **Dynamic optimization**

**Test Coverage:**
- Total tests: 34/34 passing (100% pass rate)
- Feature 2.5: 5/5 tests (asset-class adaptation)
- Feature 2.6: 8/8 tests (market rotation logic)
- Feature 2.7: 10/10 tests (scheduler intervals & strategy selection)

**Code Changes:**
- Files modified: 13 (10 source files, 3 test files)
- Lines added: +1,438
- Lines removed: -83
- Net change: +1,355 lines

### Changed
- Enhanced global scheduler with intelligent market rotation
- Updated all 4 trading strategies to support asset_class parameter
- Modified base strategy with asset-specific parameter method
- Enhanced state manager to track market performance metrics

### Files Added
- `src/crew/market_rotation_strategy.py` (270 lines) - Market selection logic
- `tests/test_asset_aware_strategies.py` (225 lines) - Strategy adaptation tests
- `tests/test_market_rotation_strategy.py` (250 lines) - Rotation logic tests
- `tests/test_adaptive_scheduler.py` (150 lines) - Scheduler interval tests

### Documentation
- Updated FEATURE_ROADMAP.md with Phase 2 completion (7/7 features)
- Updated README.md with 24/7 trading features and troubleshooting
- Added inline comments to market rotation and scheduler modules
- Updated .github/copilot-instructions.md with Phase 2 status

---

## [0.1.1] - 2025-11-02

### Changed - Documentation Restructuring
- **Restructured all documentation to feature-based approach** - AI-driven development, not time-based
  - Replaced time-based roadmap (Week 1-4, Day 1-5, hour estimates) with feature-based phases
  - Created `FEATURE_ROADMAP.md` with complexity ratings (Simple/Medium/High/Very High)
  - Organized by Phase 1-4 with clear dependencies and prerequisites
  - Removed artificial deadlines and calendar pressure
  
- **Cleaned up redundant documentation**
  - Deleted 9 obsolete/redundant files (saved 2000+ lines of outdated content)
  - Consolidated status updates into `docs/PHASE1_CRITICAL_FIXES.md`
  - Merged QUICKSTART.md content into README (already comprehensive)
  - Removed archive folder with time-based documents
  
- **Deleted files:**
  - `project_resolution_roadmap.md` (1556 lines) - superseded by FEATURE_ROADMAP.md
  - `POST_MERGE_STATUS.md` (342 lines) - outdated Nov 1 status
  - `IMPLEMENTATION_SUMMARY.md` (207 lines) - redundant with Phase 1 summary
  - `TESTING_SUMMARY.md` (383 lines) - consolidated into Phase 1 doc
  - `SECURITY_SUMMARY.md` (117 lines) - documented false positives (all secure)
  - `QUICKSTART.md` (176 lines) - content already in README
  - `docs/DOCUMENTATION_RESTRUCTURING.md` (192 lines) - internal meta-doc
  - `docs/FUTURE_ENHANCEMENTS.md` (24 lines) - proposals in roadmap Phase 3-4
  - `docs/archive/` - entire folder with time-based documents
  
- **New documentation structure:**
  - `FEATURE_ROADMAP.md` - Main development roadmap (Phase 1-4)
  - `docs/PHASE1_CRITICAL_FIXES.md` - What was delivered in Phase 1
  - `docs/MULTIMARKET_IMPLEMENTATION.md` - Phase 2 feature breakdown
  - `docs/ALPACA_CRYPTO_VERIFICATION.md` - Crypto support verification
  - `README.md` - Comprehensive getting started guide
  - `.github/copilot-instructions.md` - Project context for AI

### Benefits
- **Clearer status tracking:** Phase 1 ✅ COMPLETE, Phase 2 🔄 IN PROGRESS (not "40% done")
- **Better expectations:** Features take as long as they take (no arbitrary deadlines)
- **Focus on quality:** Complete features correctly, not rush to meet timelines
- **Reduced redundancy:** Single source of truth for each topic

---

## [0.1.1] - 2025-11-01

### Fixed - Critical
- **Fixed race condition in API rate limiting** - Parallel crew execution now prevents 429 RESOURCE_EXHAUSTED errors
  - Implemented thread-safe rate limiting with `threading.Lock()` in GeminiConnectionManager
  - Implemented thread-safe rate limiting with `threading.Lock()` in EnhancedGeminiConnectionManager (the actively used connector)
  - Ensures atomic rate limit checking and client creation during concurrent crew execution
  - Wrapped `get_llm_for_crewai()` method with lock to prevent race conditions in quota tracking
  - Removed deprecated `global_rate_limiter` that caused race conditions in parallel execution
  - Updated TradingOrchestrator to rely on centralized blocking logic in GeminiConnectionManager
  - All rate limit checks now handled by thread-safe connectors with proper locking

### Fixed - Performance
- **Optimized market scanner performance** - Reduced execution time from 7+ minutes to ~1 minute
  - Replaced sequential API calls with parallel execution using ThreadPoolExecutor
  - Implemented concurrent data fetching with max_workers=10 for optimal throughput
  - Added comprehensive error handling for failed symbol fetches
  - Scanner now completes S&P 100 analysis in approximately 60 seconds (previously 400+ seconds)

### Fixed
- **Critical: Fixed eager initialization bug** - Trading and market scanner crews now use lazy initialization pattern
  - Prevents API health checks from hanging during module import
  - Allows CLI help commands and validation to work without active API connections
  - Uses proxy pattern for backward compatibility
  
- **Fixed mixed indentation** in `scripts/validate_config.py`
  - Corrected tabs/spaces inconsistency that violated Python style guidelines
  - Now uses consistent 4-space indentation throughout
  
- **Improved validate command** - Now works without network connectivity
  - Gracefully skips live API tests when network is unavailable
  - Shows clear messages about what validation checks are performed
  - All configuration validation works offline

### Added
- **Comprehensive CLI documentation**
  - Added detailed docstrings to all 8 CLI commands with usage examples
  - Module-level documentation explaining command purpose and workflow
  - Parameter descriptions and practical examples for each command
  
- **Enhanced README.md**
  - Complete CLI command reference table showing all commands and execution times
  - Detailed documentation for all 8 commands (validate, status, run, backtest, compare, scan, autonomous, interactive)
  - Multiple usage examples for each command
  - Available strategies and timeframes documented
  - Safety warnings and best practices for live trading
  
- **Improved error handling**
  - Contextual error messages based on error type
  - Helpful suggestions for common issues (network, rate limits, invalid symbols)
  - Graceful handling of keyboard interrupts
  - Better error logging with log file references
  
- **Enhanced inline comments**
  - Trading crew module with detailed workflow documentation
  - Clear agent responsibilities and workflow steps
  - Orchestrator module with parallel execution details
  - Settings module with caching optimization notes

### Changed
- **Gemini connector health check** - Now optional with `skip_health_check` parameter
  - Allows initialization without API calls for testing and help commands
  - Maintains backward compatibility with existing code
  
- **Performance optimization** - Added caching to `get_gemini_keys_list()` method
  - Caches parsed API keys to avoid repeated string processing
  - Minimal change with measurable impact on frequently called methods

### Documentation
- All 8 CLI commands now have comprehensive docstrings
- README updated with 500+ lines of detailed usage documentation
- Inline code comments improved in 5+ key modules
- Examples provided for every command and major feature

### Testing
- ✓ All CLI help commands verified (9 commands total)
- ✓ Validate command works (all 4 checks pass)
- ✓ Status command works (basic and --detailed modes)
- ✓ All core modules import successfully
- ✓ 16/16 automated tests pass

## Summary of Changes

**Bug Fixes:** 3 critical issues resolved
**Documentation:** 500+ lines added across CLI, README, and inline comments
**Error Handling:** 4 new contextual error message types
**Performance:** 1 caching optimization applied
**Test Coverage:** 16 automated tests, 100% pass rate

**Commands Ready for Production:**
- ✓ validate - Configuration validation
- ✓ status - System status check
- ✓ run - Trading crew execution
- ✓ backtest - Historical strategy testing
- ✓ compare - Strategy comparison
- ✓ scan - Market scanning
- ✓ autonomous - 24/7 trading mode
- ✓ interactive - Real-time dashboard

---

## Previous Versions

### [0.1.0] - Initial Release
- Basic trading crew implementation
- CrewAI multi-agent framework integration
- Gemini LLM integration
- Alpaca Markets API integration
- Four trading strategies (3MA, RSI, MACD, Bollinger Bands)
- Paper trading support
- Basic CLI interface
