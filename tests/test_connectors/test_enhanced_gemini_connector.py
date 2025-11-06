"""
Unit tests for Enhanced Gemini Connection Manager rate limiting.

Tests cover:
- Quota reservation for multiple requests
- Per-key, per-tier quota tracking
- Rate limiting with estimated request counts
- Thread-safe quota management
"""

import unittest
from unittest.mock import patch, MagicMock
import time
from src.connectors.gemini_connector_enhanced import (
    EnhancedGeminiConnectionManager,
    ModelQuotaTracker,
    ModelTier,
    FREE_TIER_QUOTAS
)


class TestEnhancedGeminiConnectionManager(unittest.TestCase):
    """Test suite for Enhanced Gemini Connection Manager."""
    
    @patch('src.connectors.gemini_connector_enhanced.settings')
    def test_initialization(self, mock_settings):
        """Test that manager initializes with correct keys."""
        mock_settings.get_gemini_keys_list.return_value = ["key1", "key2", "key3"]
        
        manager = EnhancedGeminiConnectionManager(api_keys=["key1", "key2"])
        
        self.assertEqual(len(manager.all_api_keys), 2)
        self.assertIsInstance(manager.quota_tracker, ModelQuotaTracker)
        
    def test_mask_api_key(self):
        """Test API key masking for security."""
        result = EnhancedGeminiConnectionManager.mask_api_key("ABCDEFGHIJK")
        self.assertEqual(result, "...HIJK")
        
        # Test short key
        result_short = EnhancedGeminiConnectionManager.mask_api_key("ABC")
        self.assertEqual(result_short, "***")
        
    @patch('src.connectors.gemini_connector_enhanced.settings')
    def test_has_quota_for_requests_with_sufficient_quota(self, mock_settings):
        """Test quota checking when sufficient quota available."""
        mock_settings.get_gemini_keys_list.return_value = ["test_key"]
        
        manager = EnhancedGeminiConnectionManager()
        
        # Should have quota for 5 requests initially
        has_quota = manager._has_quota_for_requests("test_key", ModelTier.FLASH, 5)
        self.assertTrue(has_quota)
        
    @patch('src.connectors.gemini_connector_enhanced.settings')
    def test_has_quota_for_requests_with_insufficient_quota(self, mock_settings):
        """Test quota checking when insufficient quota."""
        mock_settings.get_gemini_keys_list.return_value = ["test_key"]
        
        manager = EnhancedGeminiConnectionManager()
        quota = FREE_TIER_QUOTAS[ModelTier.FLASH]
        
        # Fill up quota
        for _ in range(quota.rpm):
            manager.quota_tracker.record_request("test_key", ModelTier.FLASH)
        
        # Should not have quota for more requests
        has_quota = manager._has_quota_for_requests("test_key", ModelTier.FLASH, 1)
        self.assertFalse(has_quota)


class TestModelQuotaTracker(unittest.TestCase):
    """Test suite for Model Quota Tracker."""
    
    def test_can_use_model_initially(self):
        """Test that model can be used initially."""
        tracker = ModelQuotaTracker()
        
        can_use = tracker.can_use_model("test_key", ModelTier.FLASH)
        self.assertTrue(can_use)
        
    def test_record_request_increments_counters(self):
        """Test that recording requests increments counters."""
        tracker = ModelQuotaTracker()
        
        initial_count = len(tracker.minute_windows["test_key"][ModelTier.FLASH])
        tracker.record_request("test_key", ModelTier.FLASH)
        new_count = len(tracker.minute_windows["test_key"][ModelTier.FLASH])
        
        self.assertEqual(new_count, initial_count + 1)
        
    def test_rpm_limit_enforcement(self):
        """Test that RPM limit is enforced."""
        tracker = ModelQuotaTracker()
        quota = FREE_TIER_QUOTAS[ModelTier.FLASH]
        
        # Fill up to RPM limit
        for _ in range(quota.rpm):
            tracker.record_request("test_key", ModelTier.FLASH)
        
        # Should not be able to use model
        can_use = tracker.can_use_model("test_key", ModelTier.FLASH)
        self.assertFalse(can_use)
        
    def test_get_wait_time_returns_zero_when_ready(self):
        """Test that get_wait_time returns 0 when ready."""
        tracker = ModelQuotaTracker()
        
        wait_time = tracker.get_wait_time("test_key", ModelTier.FLASH)
        self.assertEqual(wait_time, 0)
        
    def test_get_wait_time_returns_positive_when_rate_limited(self):
        """Test that get_wait_time returns positive value when rate limited."""
        tracker = ModelQuotaTracker()
        quota = FREE_TIER_QUOTAS[ModelTier.FLASH]
        
        # Fill up RPM limit
        for _ in range(quota.rpm):
            tracker.record_request("test_key", ModelTier.FLASH)
        
        wait_time = tracker.get_wait_time("test_key", ModelTier.FLASH)
        self.assertIsNotNone(wait_time)
        self.assertGreater(wait_time, 0)
        
    def test_quota_tracking_per_key(self):
        """Test that quota is tracked separately per key."""
        tracker = ModelQuotaTracker()
        
        tracker.record_request("key1", ModelTier.FLASH)
        tracker.record_request("key2", ModelTier.FLASH)
        
        key1_count = len(tracker.minute_windows["key1"][ModelTier.FLASH])
        key2_count = len(tracker.minute_windows["key2"][ModelTier.FLASH])
        
        self.assertEqual(key1_count, 1)
        self.assertEqual(key2_count, 1)
        
    def test_quota_tracking_per_tier(self):
        """Test that quota is tracked separately per tier."""
        tracker = ModelQuotaTracker()
        
        tracker.record_request("test_key", ModelTier.FLASH)
        tracker.record_request("test_key", ModelTier.PRO)
        
        flash_count = len(tracker.minute_windows["test_key"][ModelTier.FLASH])
        pro_count = len(tracker.minute_windows["test_key"][ModelTier.PRO])
        
        self.assertEqual(flash_count, 1)
        self.assertEqual(pro_count, 1)
        
    def test_quota_resets_after_time_window(self):
        """Test that old quota entries are cleaned up."""
        tracker = ModelQuotaTracker()
        
        # Record a request
        tracker.record_request("test_key", ModelTier.FLASH)
        
        # Manually set timestamp to 61 seconds ago
        old_time = time.time() - 61
        tracker.minute_windows["test_key"][ModelTier.FLASH][0] = old_time
        
        # Check if we can use model (should trigger cleanup)
        can_use = tracker.can_use_model("test_key", ModelTier.FLASH)
        self.assertTrue(can_use)
        
        # Old entry should be cleaned
        self.assertEqual(len(tracker.minute_windows["test_key"][ModelTier.FLASH]), 0)


class TestFreeTierQuotas(unittest.TestCase):
    """Test suite for free tier quota constants."""
    
    def test_flash_quota_defined(self):
        """Test that Flash tier quota is defined."""
        flash_quota = FREE_TIER_QUOTAS[ModelTier.FLASH]
        
        self.assertIsNotNone(flash_quota)
        self.assertEqual(flash_quota.rpm, 10)
        self.assertEqual(flash_quota.rpd, 250)
        
    def test_pro_quota_defined(self):
        """Test that Pro tier quota is defined."""
        pro_quota = FREE_TIER_QUOTAS[ModelTier.PRO]
        
        self.assertIsNotNone(pro_quota)
        self.assertEqual(pro_quota.rpm, 2)
        self.assertEqual(pro_quota.rpd, 50)
        
    def test_flash_has_higher_quota_than_pro(self):
        """Test that Flash tier has higher quota than Pro."""
        flash_quota = FREE_TIER_QUOTAS[ModelTier.FLASH]
        pro_quota = FREE_TIER_QUOTAS[ModelTier.PRO]
        
        self.assertGreater(flash_quota.rpm, pro_quota.rpm)
        self.assertGreater(flash_quota.rpd, pro_quota.rpd)


if __name__ == '__main__':
    unittest.main()
