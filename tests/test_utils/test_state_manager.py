"""
Tests for state_manager.py - State persistence and recovery.

This module tests state saving, loading, backup, and error handling.
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch
from src.utils.state_manager import StateManager


class TestStateManagerInit(unittest.TestCase):
    """Test state manager initialization."""
    
    def test_initialization_creates_directory(self):
        """Test initialization creates storage directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "data" / "state.json"
            manager = StateManager(storage_path)
            
            self.assertEqual(manager.storage_path, storage_path)
            self.assertTrue(storage_path.parent.exists())
    
    def test_initialization_with_existing_directory(self):
        """Test initialization with existing directory works."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "state.json"
            # Directory already exists
            storage_path.parent.mkdir(exist_ok=True)
            
            manager = StateManager(storage_path)
            
            self.assertEqual(manager.storage_path, storage_path)


class TestSaveState(unittest.TestCase):
    """Test state saving functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "state.json"
        self.manager = StateManager(self.storage_path)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_save_state_creates_file(self):
        """Test saving state creates file with correct content."""
        state = {"symbol": "SPY", "strategy": "3ma", "position": "LONG"}
        
        self.manager.save_state(state)
        
        self.assertTrue(self.storage_path.exists())
        with open(self.storage_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded["symbol"], "SPY")
        self.assertEqual(loaded["strategy"], "3ma")
    
    def test_save_state_creates_backup(self):
        """Test saving state creates backup of existing file."""
        initial_state = {"version": 1}
        updated_state = {"version": 2}
        
        # Save initial state
        self.manager.save_state(initial_state)
        
        # Save updated state (should create backup)
        self.manager.save_state(updated_state)
        
        backup_path = self.storage_path.with_suffix('.json.bak')
        self.assertTrue(backup_path.exists())
        
        with open(backup_path, 'r') as f:
            backup = json.load(f)
        self.assertEqual(backup["version"], 1)
        
        with open(self.storage_path, 'r') as f:
            current = json.load(f)
        self.assertEqual(current["version"], 2)
    
    def test_save_state_handles_complex_data(self):
        """Test saving state with complex nested data."""
        state = {
            "portfolio": {
                "positions": [
                    {"symbol": "SPY", "qty": 100},
                    {"symbol": "QQQ", "qty": 50}
                ],
                "cash": 10000.50
            },
            "trades": [1, 2, 3, 4, 5]
        }
        
        self.manager.save_state(state)
        
        with open(self.storage_path, 'r') as f:
            loaded = json.load(f)
        self.assertEqual(loaded["portfolio"]["cash"], 10000.50)
        self.assertEqual(len(loaded["portfolio"]["positions"]), 2)
    
    @patch('src.utils.state_manager.logger')
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_save_state_logs_errors(self, mock_open, mock_logger):
        """Test save_state logs errors on failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "state.json"
            manager = StateManager(storage_path)
            
            # save_state will fail due to mocked open() raising PermissionError
            manager.save_state({"data": "value"})
            
            # Verify error was logged
            mock_logger.error.assert_called()


class TestLoadState(unittest.TestCase):
    """Test state loading functionality."""
    
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "state.json"
        self.manager = StateManager(self.storage_path)
    
    def tearDown(self):
        self.temp_dir.cleanup()
    
    def test_load_state_returns_saved_data(self):
        """Test loading state returns previously saved data."""
        state = {"symbol": "AAPL", "price": 150.25}
        self.manager.save_state(state)
        
        loaded = self.manager.load_state()
        
        self.assertEqual(loaded["symbol"], "AAPL")
        self.assertEqual(loaded["price"], 150.25)
    
    def test_load_state_returns_empty_dict_when_no_file(self):
        """Test loading state returns empty dict when no file exists."""
        loaded = self.manager.load_state()
        
        self.assertEqual(loaded, {})
    
    def test_load_state_falls_back_to_backup(self):
        """Test loading state falls back to backup if main file corrupted."""
        # Create a valid backup
        backup_path = self.storage_path.with_suffix('.json.bak')
        backup_state = {"backup": True, "version": 1}
        with open(backup_path, 'w') as f:
            json.dump(backup_state, f)
        
        # Create a corrupted main file
        with open(self.storage_path, 'w') as f:
            f.write("invalid json {{{")
        
        loaded = self.manager.load_state()
        
        self.assertEqual(loaded["backup"], True)
        self.assertEqual(loaded["version"], 1)
    
    def test_load_state_returns_empty_dict_when_both_files_corrupted(self):
        """Test loading state returns empty dict when both files corrupted."""
        # Create corrupted main file
        with open(self.storage_path, 'w') as f:
            f.write("invalid json")
        
        # Create corrupted backup file
        backup_path = self.storage_path.with_suffix('.json.bak')
        with open(backup_path, 'w') as f:
            f.write("also invalid")
        
        loaded = self.manager.load_state()
        
        self.assertEqual(loaded, {})
    
    @patch('src.utils.state_manager.logger')
    def test_load_state_logs_warnings(self, mock_logger):
        """Test load_state logs warnings on errors."""
        # Create corrupted file
        with open(self.storage_path, 'w') as f:
            f.write("invalid")
        
        self.manager.load_state()
        
        # Verify warning was logged
        mock_logger.warning.assert_called()


class TestStateManagerRoundTrip(unittest.TestCase):
    """Test full save/load cycle."""
    
    def test_round_trip_preserves_data(self):
        """Test saving and loading preserves all data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            storage_path = Path(temp_dir) / "state.json"
            manager = StateManager(storage_path)
            
            original_state = {
                "symbol": "SPY",
                "strategy": "rsi_breakout",
                "position_size": 100,
                "entry_price": 420.50,
                "metadata": {
                    "timestamp": "2025-01-15T10:30:00",
                    "market": "US_EQUITY"
                }
            }
            
            manager.save_state(original_state)
            loaded_state = manager.load_state()
            
            self.assertEqual(original_state, loaded_state)


if __name__ == "__main__":
    unittest.main()
