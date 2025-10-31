import unittest
from unittest.mock import patch, MagicMock
from src.connectors.gemini_connector import GeminiConnectionManager

class TestGeminiConnector(unittest.TestCase):

    @patch('src.connectors.gemini_connector.ChatGoogleGenerativeAI')
    @patch('src.connectors.gemini_connector.time.sleep') # Mock sleep to speed up tests
    def test_key_rotation_and_health_tracking(self, mock_sleep, mock_chat_google):
        # Arrange
        api_keys = ["key1", "key2", "key3"]
        gemini_manager = GeminiConnectionManager(api_keys=api_keys)

        # Mock the invoke method to simulate API calls
        mock_instance_key1 = MagicMock()
        mock_instance_key1.invoke.side_effect = Exception("Invalid API key for key1")

        mock_instance_key2 = MagicMock()
        mock_instance_key2.invoke.return_value = "successful response"

        mock_chat_google.side_effect = [
            mock_instance_key1, # First call for key1 will fail on invoke
            mock_instance_key2, # Second call for key2 will succeed
        ]

        # Act
        client = gemini_manager.get_client()

        # Assert
        self.assertIsNotNone(client)

        # Verify ChatGoogleGenerativeAI was called correctly
        self.assertEqual(mock_chat_google.call_count, 2)
        # First call used key1, second used key2 (best available after failure)
        self.assertEqual(mock_chat_google.call_args_list[0].kwargs['google_api_key'], "key1")
        self.assertEqual(mock_chat_google.call_args_list[1].kwargs['google_api_key'], "key2")

        # Verify invoke was called for the health check
        mock_instance_key1.invoke.assert_called_once_with("hello")
        mock_instance_key2.invoke.assert_called_once_with("hello")

        # Verify the client returned is the one that succeeded
        self.assertIs(client, mock_instance_key2)

        # Verify health tracker state
        health_tracker = gemini_manager.key_health_tracker
        self.assertEqual(health_tracker.key_health["key1"]["failure"], 1)
        self.assertEqual(health_tracker.key_health["key1"]["success"], 0)
        self.assertGreater(health_tracker.key_health["key1"]["backoff_until"], 0)

        self.assertEqual(health_tracker.key_health["key2"]["success"], 1)
        self.assertEqual(health_tracker.key_health["key2"]["failure"], 0)


    @patch('src.connectors.gemini_connector.ChatGoogleGenerativeAI')
    def test_get_best_key_logic(self, mock_chat_google):
        # Arrange
        api_keys = ["key1", "key2", "key3"]
        gemini_manager = GeminiConnectionManager(api_keys=api_keys)
        health_tracker = gemini_manager.key_health_tracker

        # Manually set health stats
        health_tracker.key_health["key1"] = {"success": 8, "failure": 2, "last_used": 0, "backoff_until": 0} # score = 0.80
        health_tracker.key_health["key2"] = {"success": 10, "failure": 1, "last_used": 0, "backoff_until": 0} # score = 0.90
        health_tracker.key_health["key3"] = {"success": 5, "failure": 5, "last_used": 0, "backoff_until": 0}  # score = 0.50

        # Act
        sorted_keys = health_tracker.get_available_keys_sorted()

        # Assert
        self.assertEqual(sorted_keys, ["key2", "key1"]) # key3 is below the 0.7 threshold

if __name__ == '__main__':
    unittest.main()
