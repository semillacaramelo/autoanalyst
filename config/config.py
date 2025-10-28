import os
from dotenv import load_dotenv

load_dotenv()

# Load and split the comma-separated Gemini keys into a list
GEMINI_API_KEYS_STR = os.getenv("GEMINI_API_KEYS", "")
GEMINI_API_KEYS = [key.strip() for key in GEMINI_API_KEYS_STR.split(',') if key.strip()]

# Alpaca configuration remains the same
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
ALPACA_CONFIG = {
    "key_id": ALPACA_API_KEY,
    "secret_key": ALPACA_SECRET_KEY,
    "paper": True,
}
