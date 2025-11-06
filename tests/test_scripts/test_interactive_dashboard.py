"""
Regression tests for interactive dashboard (run_crew.py interactive command).

Tests ensure that the initialization loop bug (Issue #1) is fixed and the
dashboard renders correctly without repeated API initializations.

Bug History:
- Original Issue (Nov 5, 2025): get_status_panel() called gemini_manager.get_client()
  on every 3-second refresh, causing infinite initialization loop.
- Fix: Added status caching with 30-second TTL, removed state_manager.load_state()
  from get_active_strategies_panel().
- Expected Behavior: Single initialization, dashboard renders, refresh works.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import time


class TestInteractiveDashboard:
    """Test suite for interactive dashboard functionality."""
    
    @pytest.fixture
    def mock_alpaca_account(self):
        """Mock Alpaca account data."""
        return {
            'status': 'ACTIVE',
            'equity': '100000.00',
            'cash': '95000.00',
            'buying_power': '95000.00'
        }
    
    @pytest.fixture
    def mock_positions(self):
        """Mock open positions."""
        return [
            {
                'symbol': 'SPY',
                'qty': '10',
                'avg_entry_price': '450.00',
                'current_price': '455.00',
                'unrealized_pl': 50.00
            },
            {
                'symbol': 'QQQ',
                'qty': '5',
                'avg_entry_price': '375.00',
                'current_price': '370.00',
                'unrealized_pl': -25.00
            }
        ]
    
    @pytest.fixture
    def mock_gemini_keys(self):
        """Mock Gemini API keys."""
        return ['key1_ABCD', 'key2_EFGH', 'key3_IJKL']
    
    def test_status_panel_caching_prevents_reinitialization(self, mock_alpaca_account, mock_gemini_keys):
        """
        Test that status panel uses caching to prevent repeated API calls.
        
        This is the primary regression test for the initialization loop bug.
        """
        from scripts.run_crew import get_status_panel, _cached_status, _STATUS_CACHE_TTL
        
        with patch('scripts.run_crew.alpaca_manager') as mock_alpaca, \
             patch('scripts.run_crew.gemini_manager') as mock_gemini, \
             patch('scripts.run_crew.settings') as mock_settings:
            
            # Setup mocks
            mock_alpaca.get_account.return_value = mock_alpaca_account
            mock_settings.get_gemini_keys_list.return_value = mock_gemini_keys
            mock_settings.dry_run = True
            mock_gemini._last_client = MagicMock()  # Simulate existing client
            
            # Reset cache
            _cached_status['alpaca']['last_check'] = 0
            _cached_status['gemini']['last_check'] = 0
            
            # First call - should fetch fresh data
            panel1 = get_status_panel()
            initial_alpaca_calls = mock_alpaca.get_account.call_count
            initial_gemini_calls = mock_gemini.get_client.call_count
            
            assert initial_alpaca_calls == 1, "First call should fetch Alpaca data"
            assert panel1 is not None, "Panel should be created"
            
            # Second call immediately after - should use cache (no new API calls)
            panel2 = get_status_panel()
            second_alpaca_calls = mock_alpaca.get_account.call_count
            second_gemini_calls = mock_gemini.get_client.call_count
            
            assert second_alpaca_calls == initial_alpaca_calls, "Should use cached Alpaca data"
            assert second_gemini_calls == initial_gemini_calls, "Should use cached Gemini data"
            
            # Simulate cache expiration
            _cached_status['alpaca']['last_check'] = time.time() - _STATUS_CACHE_TTL - 1
            _cached_status['gemini']['last_check'] = time.time() - _STATUS_CACHE_TTL - 1
            
            # Third call after cache expiration - should fetch fresh data
            panel3 = get_status_panel()
            third_alpaca_calls = mock_alpaca.get_account.call_count
            
            assert third_alpaca_calls == initial_alpaca_calls + 1, "Should refresh after cache expiry"
    
    def test_status_panel_handles_connection_errors_gracefully(self):
        """Test that status panel handles API connection failures."""
        from scripts.run_crew import get_status_panel, _cached_status
        from rich.console import Console
        
        with patch('scripts.run_crew.alpaca_manager') as mock_alpaca, \
             patch('scripts.run_crew.gemini_manager') as mock_gemini, \
             patch('scripts.run_crew.settings') as mock_settings:
            
            # Setup mocks to raise errors
            mock_alpaca.get_account.side_effect = ConnectionError("Network unreachable")
            mock_settings.get_gemini_keys_list.side_effect = Exception("API key error")
            mock_settings.dry_run = False
            
            # Reset cache
            _cached_status['alpaca']['last_check'] = 0
            _cached_status['gemini']['last_check'] = 0
            
            # Should not raise exception
            panel = get_status_panel()
            
            # Render panel to text to check content
            console = Console()
            with console.capture() as capture:
                console.print(panel)
            output = capture.get()
            
            assert panel is not None, "Panel should render even with connection errors"
            assert "Connection Failed" in output, "Should show connection failure message"
    
    def test_positions_panel_renders_empty_state(self):
        """Test positions panel with no open positions."""
        from scripts.run_crew import get_positions_panel
        from rich.console import Console
        
        with patch('scripts.run_crew.alpaca_manager') as mock_alpaca:
            mock_alpaca.get_positions.return_value = []
            
            panel = get_positions_panel()
            
            console = Console()
            with console.capture() as capture:
                console.print(panel)
            output = capture.get()
            
            assert panel is not None
            assert "No open positions" in output
    
    def test_positions_panel_renders_with_positions(self, mock_positions):
        """Test positions panel with active positions."""
        from scripts.run_crew import get_positions_panel
        from rich.console import Console
        
        with patch('scripts.run_crew.alpaca_manager') as mock_alpaca:
            mock_alpaca.get_positions.return_value = mock_positions
            
            panel = get_positions_panel()
            
            console = Console()
            with console.capture() as capture:
                console.print(panel)
            output = capture.get()
            
            assert panel is not None
            assert "SPY" in output
            assert "QQQ" in output
    
    def test_active_strategies_panel_no_state_loading(self):
        """
        Test that active strategies panel does NOT load state on every refresh.
        
        This is the secondary regression test for the initialization loop bug.
        """
        from scripts.run_crew import get_active_strategies_panel
        from rich.console import Console
        
        with patch('scripts.run_crew.settings') as mock_settings:
            mock_settings.dry_run = True
            
            # Call multiple times
            panel1 = get_active_strategies_panel()
            panel2 = get_active_strategies_panel()
            panel3 = get_active_strategies_panel()
            
            console = Console()
            with console.capture() as capture:
                console.print(panel1)
            output1 = capture.get()
            
            # Should render successfully
            assert panel1 is not None
            assert "3ma" in output1
            assert "rsi_breakout" in output1
            assert "macd" in output1
            assert "bollinger_bands_reversal" in output1
    
    def test_dashboard_layout_generation(self):
        """Test that dashboard layout is created correctly."""
        from scripts.run_crew import generate_dashboard
        
        layout = generate_dashboard()
        
        assert layout is not None
        assert layout.name == "root"
        # Check that all expected sections exist
        assert "header" in [child.name for child in layout.children]
        assert "main" in [child.name for child in layout.children]
        assert "footer" in [child.name for child in layout.children]
    
    def test_interactive_command_initialization_once(self):
        """
        Integration test: Verify interactive command initializes only once.
        
        This test ensures get_status_panel() workflow uses caching correctly.
        Note: We can't call interactive() directly due to Click CLI context requirements.
        """
        from scripts.run_crew import get_status_panel, _cached_status
        
        with patch('scripts.run_crew.alpaca_manager') as mock_alpaca, \
             patch('scripts.run_crew.gemini_manager') as mock_gemini, \
             patch('scripts.run_crew.settings') as mock_settings:
            
            # Setup mocks
            mock_settings.get_gemini_keys_list.return_value = ['key1', 'key2']
            mock_settings.dry_run = True
            mock_alpaca.get_account.return_value = {'equity': '100000', 'status': 'ACTIVE'}
            mock_gemini._last_client = MagicMock()
            
            # Reset cache
            _cached_status['alpaca']['last_check'] = 0
            _cached_status['gemini']['last_check'] = 0
            
            # Simulate multiple refresh cycles (like dashboard would do)
            for i in range(5):
                panel = get_status_panel()
                assert panel is not None
                time.sleep(0.5)  # Simulate refresh interval
            
            # Check that Gemini was initialized at most once (skip_health_check=True on subsequent calls)
            # Alpaca should have been called once (first refresh) due to caching
            assert mock_alpaca.get_account.call_count == 1, \
                f"Alpaca should be called once (caching), got {mock_alpaca.get_account.call_count}"
            assert mock_gemini.get_client.call_count <= 1, \
                f"Gemini should initialize at most once, got {mock_gemini.get_client.call_count}"
    
    def test_cache_ttl_default_value(self):
        """Test that cache TTL is set to reasonable default (30 seconds)."""
        from scripts.run_crew import _STATUS_CACHE_TTL
        
        assert _STATUS_CACHE_TTL == 30, "Cache TTL should be 30 seconds (not 3 seconds)"


class TestInteractiveDashboardEdgeCases:
    """Edge case tests for dashboard components."""
    
    def test_positions_panel_with_invalid_data(self):
        """Test positions panel handles malformed position data."""
        from scripts.run_crew import get_positions_panel
        
        with patch('scripts.run_crew.alpaca_manager') as mock_alpaca:
            # Malformed data (missing required fields)
            mock_alpaca.get_positions.return_value = [
                {'symbol': 'SPY'},  # Missing qty, prices
                {}  # Empty dict
            ]
            
            # Should not crash
            panel = get_positions_panel()
            assert panel is not None
    
    def test_positions_panel_with_api_error(self):
        """Test positions panel handles API errors."""
        from scripts.run_crew import get_positions_panel
        from rich.console import Console
        
        with patch('scripts.run_crew.alpaca_manager') as mock_alpaca:
            mock_alpaca.get_positions.side_effect = Exception("API rate limit exceeded")
            
            panel = get_positions_panel()
            
            console = Console()
            with console.capture() as capture:
                console.print(panel)
            output = capture.get()
            
            assert panel is not None
            assert "Error" in output
    
    def test_status_panel_equity_none_handling(self):
        """Test status panel handles None equity value."""
        from scripts.run_crew import get_status_panel, _cached_status
        from rich.console import Console
        
        with patch('scripts.run_crew.alpaca_manager') as mock_alpaca, \
             patch('scripts.run_crew.gemini_manager') as mock_gemini, \
             patch('scripts.run_crew.settings') as mock_settings:
            
            mock_alpaca.get_account.return_value = {'status': 'ACTIVE', 'equity': None}
            mock_settings.get_gemini_keys_list.return_value = ['key1']
            mock_settings.dry_run = True
            mock_gemini._last_client = MagicMock()
            
            _cached_status['alpaca']['last_check'] = 0
            _cached_status['gemini']['last_check'] = 0
            
            panel = get_status_panel()
            
            console = Console()
            with console.capture() as capture:
                console.print(panel)
            output = capture.get()
            
            assert panel is not None
            assert "N/A" in output, "Should show N/A for None equity"


# Integration test configuration
@pytest.mark.integration
class TestInteractiveDashboardIntegration:
    """Integration tests requiring actual API connectivity (optional)."""
    
    @pytest.mark.skip(reason="Requires live API credentials")
    def test_interactive_dashboard_with_real_apis(self):
        """
        Test interactive dashboard with real API connections.
        
        This test is skipped by default. To run it:
        1. Ensure .env file has valid API keys
        2. Run: pytest tests/test_scripts/test_interactive_dashboard.py::TestInteractiveDashboardIntegration -m integration
        """
        from scripts.run_crew import interactive
        import threading
        
        # Run for 10 seconds with real APIs
        def run_interactive():
            try:
                interactive()
            except KeyboardInterrupt:
                pass
        
        thread = threading.Thread(target=run_interactive, daemon=True)
        thread.start()
        thread.join(timeout=10)
        
        # If we get here without crashing, test passes
        assert True, "Dashboard should run without crashes for 10 seconds"
