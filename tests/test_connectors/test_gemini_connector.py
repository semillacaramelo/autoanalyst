import unittest
from unittest.mock import patch, MagicMock, call
import time

from src.connectors.gemini_connector import GeminiConnectionManager, KeyHealthTracker, RateLimiter
from src.config.settings import settings


# Mock the Google API error since it might not be installed in test environments
class MockGoogleAPICallError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.message = message
        self.code = code

# This allows us to patch the class inside the gemini_connector module
gemini_connector_path = 'src.connectors.gemini_connector'
mock_google_api_error_path = f'{gemini_connector_path}.GoogleAPICallError'

class TestGeminiConnector(unittest.TestCase):

    @patch(f'{gemini_connector_path}.settings')
    def test_initialization_with_valid_keys(self, mock_settings):
        """
        Verify that the GeminiConnectionManager initializes correctly with keys from settings.
        """
        # Arrange
        mock_settings.get_gemini_keys_list.return_value = ["key1", "key2"]
        mock_settings.primary_llm_models = ["gemini-pro"]
        mock_settings.fallback_llm_models = ["gemini-1.0-pro"]
        mock_settings.key_health_threshold = 0.5
        mock_settings.rate_limit_rpm = 60
        mock_settings.rate_limit_rpd = 1500

        # Act
        manager = GeminiConnectionManager()

        # Assert
        self.assertEqual(manager.api_keys, ["key1", "key2"])
        self.assertIsInstance(manager.key_health_tracker, KeyHealthTracker)
        self.assertEqual(manager.key_health_tracker.keys, ["key1", "key2"])
        self.assertIsInstance(manager.rate_limiter, RateLimiter)
        self.assertEqual(manager.rate_limiter.rpm, 60)
        self.assertEqual(manager.rate_limiter.rpd, 1500)

    def test_initialization_no_keys_raises_error(self):
        """
        Verify that a ValueError is raised if no API keys are provided.
        """
        # Arrange
        with patch(f'{gemini_connector_path}.settings') as mock_settings:
            mock_settings.get_gemini_keys_list.return_value = []

            # Act & Assert
            with self.assertRaises(ValueError) as context:
                GeminiConnectionManager()
            self.assertIn("No Gemini API keys configured", str(context.exception))

    @patch(f'{gemini_connector_path}.ChatGoogleGenerativeAI')
    @patch(f'{gemini_connector_path}.settings')
    def test_get_client_success_first_key(self, mock_settings, mock_chat_google):
        """
        Verify that the client is successfully returned on the first attempt with the first key.
        """
        # Arrange
        mock_settings.get_gemini_keys_list.return_value = ["key1", "key2"]
        mock_settings.primary_llm_models = ["gemini-pro"]
        mock_settings.fallback_llm_models = []
        mock_settings.key_health_threshold = 0.5
        mock_settings.rate_limit_rpm = 60
        mock_settings.rate_limit_rpd = 1500
        mock_settings.rate_limit_rpm = 60
        mock_settings.rate_limit_rpd = 1500
        mock_client_instance = MagicMock()
        mock_client_instance.invoke.return_value = "hello"
        mock_chat_google.return_value = mock_client_instance

        manager = GeminiConnectionManager()

        # Act
        client = manager.get_client()

        # Assert
        self.assertIsNotNone(client)
        mock_chat_google.assert_called_once_with(
            model="gemini-pro",
            google_api_key="key1",
            temperature=manager.temperature,
            verbose=False
        )
        mock_client_instance.invoke.assert_called_once_with("hello")
        self.assertEqual(manager.key_health_tracker.key_health["key1"]["success"], 1)

    @patch(mock_google_api_error_path, new=MockGoogleAPICallError)
    @patch(f'{gemini_connector_path}.ChatGoogleGenerativeAI')
    @patch(f'{gemini_connector_path}.settings')
    def test_get_client_rotates_on_auth_failure(self, mock_settings, mock_chat_google):
        """
        Verify that the manager rotates to the next key if the first key fails with an auth error.
        """
        # Arrange
        mock_settings.get_gemini_keys_list.return_value = ["key1_bad", "key2_good"]
        mock_settings.primary_llm_models = ["gemini-pro"]
        mock_settings.fallback_llm_models = []
        mock_settings.key_health_threshold = 0.5
        mock_settings.rate_limit_rpm = 60
        mock_settings.rate_limit_rpd = 1500

        # Simulate failure on the first key, success on the second
        mock_good_client = MagicMock()
        mock_good_client.invoke.return_value = "hello"
        mock_chat_google.side_effect = [
            MockGoogleAPICallError("Auth error", code=403),
            mock_good_client
        ]

        manager = GeminiConnectionManager()

        # Act
        client = manager.get_client()

        # Assert
        self.assertIsNotNone(client)
        self.assertEqual(mock_chat_google.call_count, 2)
        mock_chat_google.assert_has_calls([
            call(model="gemini-pro", google_api_key="key1_bad", temperature=manager.temperature, verbose=False),
            call(model="gemini-pro", google_api_key="key2_good", temperature=manager.temperature, verbose=False)
        ])
        self.assertEqual(manager.key_health_tracker.key_health["key1_bad"]["failure"], 1)
        self.assertGreater(manager.key_health_tracker.key_health["key1_bad"]["backoff_until"], time.time())
        self.assertEqual(manager.key_health_tracker.key_health["key2_good"]["success"], 1)

    @patch(mock_google_api_error_path, new=MockGoogleAPICallError)
    @patch(f'{gemini_connector_path}.ChatGoogleGenerativeAI')
    @patch(f'{gemini_connector_path}.settings')
    def test_get_client_skips_key_in_backoff(self, mock_settings, mock_chat_google):
        """
        Verify that a key currently in a backoff period is skipped.
        """
        # Arrange
        mock_settings.get_gemini_keys_list.return_value = ["key1_backoff", "key2_good"]
        mock_settings.primary_llm_models = ["gemini-pro"]
        mock_settings.fallback_llm_models = []
        mock_settings.key_health_threshold = 0.5
        mock_settings.rate_limit_rpm = 60
        mock_settings.rate_limit_rpd = 1500
        mock_chat_google.return_value = MagicMock()

        manager = GeminiConnectionManager()
        # Manually put key1 in backoff
        manager.key_health_tracker.record_failure("key1_backoff")

        # Act
        manager.get_client()

        # Assert
        # Check that ChatGoogleGenerativeAI was initialized directly with the second key
        mock_chat_google.assert_called_once_with(
            model="gemini-pro",
            google_api_key="key2_good",
            temperature=manager.temperature,
            verbose=False
        )

    @patch(f'{gemini_connector_path}.time.sleep')
    @patch(mock_google_api_error_path, new=MockGoogleAPICallError)
    @patch(f'{gemini_connector_path}.ChatGoogleGenerativeAI')
    @patch(f'{gemini_connector_path}.settings')
    def test_get_client_raises_runtime_error_if_all_keys_fail(self, mock_settings, mock_chat_google, mock_sleep):
        """
        Verify that a RuntimeError is raised if all keys fail repeatedly.
        """
        # Arrange
        mock_settings.get_gemini_keys_list.return_value = ["key1_bad", "key2_bad"]
        mock_settings.primary_llm_models = ["gemini-pro"]
        mock_settings.fallback_llm_models = []
        mock_settings.key_health_threshold = 0.5
        mock_settings.rate_limit_rpm = 60
        mock_settings.rate_limit_rpd = 1500
        # All calls to the API fail
        mock_chat_google.side_effect = MockGoogleAPICallError("Permanent failure", code=403)

        manager = GeminiConnectionManager()

        # Act & Assert
        with self.assertRaises(RuntimeError) as context:
            manager.get_client()

        self.assertIn("Failed to get a working Gemini client", str(context.exception))
        # Each key is tried once and then put in backoff. Since time is mocked, backoff never expires.
        self.assertEqual(manager.key_health_tracker.key_health["key1_bad"]["failure"], 1)
        self.assertEqual(manager.key_health_tracker.key_health["key2_bad"]["failure"], 1)
        self.assertGreaterEqual(mock_sleep.call_count, 2) # At least one 60s wait between cycles

    @patch(mock_google_api_error_path, new=MockGoogleAPICallError)
    @patch(f'{gemini_connector_path}.ChatGoogleGenerativeAI')
    @patch(f'{gemini_connector_path}.settings')
    def test_get_client_falls_back_to_secondary_model(self, mock_settings, mock_chat_google):
        """
        Verify that the manager tries a fallback model if the primary model fails with a non-auth error.
        """
        # Arrange
        mock_settings.get_gemini_keys_list.return_value = ["key1_good"]
        mock_settings.primary_llm_models = ["primary_model_bad"]
        mock_settings.fallback_llm_models = ["fallback_model_good"]
        mock_settings.key_health_threshold = 0.5
        mock_settings.rate_limit_rpm = 60
        mock_settings.rate_limit_rpd = 1500

        mock_good_client = MagicMock()
        mock_good_client.invoke.return_value = "hello"
        # Simulate a non-auth API error on the primary model, then success on the fallback
        mock_chat_google.side_effect = [
            MockGoogleAPICallError("Model unavailable", code=500),
            mock_good_client
        ]

        manager = GeminiConnectionManager()

        # Act
        client = manager.get_client()

        # Assert
        self.assertIsNotNone(client)
        self.assertEqual(mock_chat_google.call_count, 2)
        # It should try the primary model first, then the fallback model with the SAME key
        mock_chat_google.assert_has_calls([
            call(model="primary_model_bad", google_api_key="key1_good", temperature=manager.temperature, verbose=False),
            call(model="fallback_model_good", google_api_key="key1_good", temperature=manager.temperature, verbose=False)
        ])
        # The key itself did not fail, so it should not be penalized
        self.assertEqual(manager.key_health_tracker.key_health["key1_good"]["failure"], 0)
        self.assertEqual(manager.key_health_tracker.key_health["key1_good"]["success"], 1)

    @patch(f'{gemini_connector_path}.time.sleep')
    def test_rate_limiter_waits_when_rpm_exceeded(self, mock_sleep):
        """
        Verify that the rate limiter sleeps when the requests per minute limit is hit.
        """
        # Arrange
        # Set a low RPM limit for testing
        limiter = RateLimiter(rpm=2, rpd=100)

        # Act
        limiter.wait_if_needed() # Request 1
        limiter.wait_if_needed() # Request 2

        # This call should trigger the sleep
        limiter.wait_if_needed() # Request 3

        # Assert
        mock_sleep.assert_called_once()
        # Check that it sleeps for a duration close to 60 seconds
        self.assertGreater(mock_sleep.call_args[0][0], 59.0)

if __name__ == '__main__':
    unittest.main()
