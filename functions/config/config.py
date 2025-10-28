import os

# Load and split the comma-separated Gemini keys into a list
GEMINI_API_KEYS_STR = os.environ.get("GEMINI_API_KEYS", "")
GEMINI_API_KEYS = [key.strip() for key in GEMINI_API_KEYS_STR.split(',') if key.strip()]

# Alpaca configuration
ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
ALPACA_CONFIG = {
    "key_id": ALPACA_API_KEY,
    "secret_key": ALPACA_SECRET_KEY,
    "paper": True,
}