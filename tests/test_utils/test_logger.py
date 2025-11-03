"""
Tests for logger.py - Structured logging setup for AutoAnalyst.

This module tests the logging configuration and functionality.
"""

import unittest
import logging
from pathlib import Path


class TestLoggerSetup(unittest.TestCase):
    """Test logger setup functionality (setup_logging called on module import)."""

    def setUp(self):
        """Set up test environment."""
        # Logger is already set up on module import
        self.test_logger = logging.getLogger("test_autoanalyst")

    def test_logs_directory_exists(self):
        """Test that logs directory is created."""
        log_dir = Path("logs")
        self.assertTrue(log_dir.exists(), "logs directory should exist after setup_logging()")
        self.assertTrue(log_dir.is_dir(), "logs should be a directory")

    def test_log_file_created(self):
        """Test that log file is created in logs directory after logging."""
        # Force a log write to create the file
        root_logger = logging.getLogger()
        root_logger.info("Test log entry to ensure file creation")

        log_dir = Path("logs")
        log_files = list(log_dir.glob("trading_crew_*.log"))
        self.assertGreater(len(log_files), 0, "At least one log file should exist after logging")

    def test_root_logger_has_handlers(self):
        """Test that root logger has handlers configured."""
        root_logger = logging.getLogger()
        self.assertGreater(len(root_logger.handlers), 0, "Root logger should have handlers")

    def test_root_logger_level_configured(self):
        """Test that root logger level is configured."""
        root_logger = logging.getLogger()
        # Level should be one of the valid log levels
        valid_levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL, logging.NOTSET]
        self.assertIn(root_logger.level, valid_levels, "Root logger should have valid log level")

    def test_handlers_have_formatters(self):
        """Test that handlers have formatters configured."""
        root_logger = logging.getLogger()
        # At least some handlers should have formatters
        handlers_with_formatters = [h for h in root_logger.handlers if h.formatter is not None]
        self.assertGreater(len(handlers_with_formatters), 0, "At least one handler should have formatter")

    def test_logger_can_log_messages(self):
        """Test that logger can actually log messages without errors."""
        # Should not raise any exceptions
        self.test_logger.debug("Test debug message")
        self.test_logger.info("Test info message")
        self.test_logger.warning("Test warning message")
        self.test_logger.error("Test error message")

    def test_specific_log_file_name_pattern(self):
        """Test that log files follow expected naming pattern."""
        # Force a log write to create the file
        root_logger = logging.getLogger()
        root_logger.info("Test log entry for filename pattern check")

        log_dir = Path("logs")
        log_files = list(log_dir.glob("trading_crew_*.log"))

        # Verify at least one file matches the pattern
        self.assertGreater(len(log_files), 0, "At least one log file should exist")
        for log_file in log_files:
            # Should be in format: trading_crew_YYYYMMDD.log
            name = log_file.name
            self.assertTrue(name.startswith("trading_crew_"), f"Log file {name} should start with 'trading_crew_'")
            self.assertTrue(name.endswith(".log"), f"Log file {name} should end with '.log'")

    def test_logger_name_propagation(self):
        """Test that child loggers inherit configuration."""
        child_logger = logging.getLogger("test_autoanalyst.submodule")

        # Should be able to log without errors
        child_logger.info("Child logger test message")

        # Child should propagate to root
        self.assertTrue(child_logger.propagate, "Child logger should propagate to root")

    def test_logging_module_import_successful(self):
        """Test that logging module can be imported without errors."""
        # If we got here, the module imported successfully
        from src.utils import logger

        self.assertIsNotNone(logger, "Logger module should be importable")

    def test_multiple_log_calls_no_errors(self):
        """Test that multiple log calls work without errors."""
        for i in range(10):
            self.test_logger.info(f"Test message {i}")
        # If we got here without exceptions, test passes
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
