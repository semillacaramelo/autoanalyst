"""
State Manager
Persists and recovers the trading application's state.
"""
import json
import shutil
from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class StateManager:
    """Persist and recover trading state."""

    def __init__(self, storage_path: Path = Path("data/state.json")):
        self.storage_path = storage_path
        self.storage_path.parent.mkdir(exist_ok=True)

    def save_state(self, state: Dict):
        """Atomically save state with backup."""
        backup_path = self.storage_path.with_suffix('.json.bak')
        try:
            if self.storage_path.exists():
                shutil.copy(self.storage_path, backup_path)

            with open(self.storage_path, 'w') as f:
                json.dump(state, f, indent=2, default=str)
            logger.info(f"Successfully saved state to {self.storage_path}")

        except Exception as e:
            logger.error(f"Failed to save state: {e}", exc_info=True)

    def load_state(self) -> Dict:
        """Load state with fallback to backup."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r') as f:
                    logger.info(f"Loading state from {self.storage_path}")
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load main state file: {e}. Trying backup.")

        backup_path = self.storage_path.with_suffix('.json.bak')
        if backup_path.exists():
            try:
                with open(backup_path, 'r') as f:
                    logger.warning(f"Loading state from backup file {backup_path}")
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load backup state file: {e}")

        logger.info("No existing state file found. Starting with a fresh state.")
        return {}  # Fresh start
