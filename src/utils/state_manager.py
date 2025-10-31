import json
import shutil
from pathlib import Path

class StateManager:
    """Persist and recover trading state"""

    def __init__(self, storage_path: Path = Path("data/state.json")):
        self.storage_path = storage_path

    def save_state(self, state: dict):
        """Atomically save state with backup"""
        backup = self.storage_path.with_suffix('.json.bak')
        if self.storage_path.exists():
            shutil.copy(self.storage_path, backup)
        with open(self.storage_path, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    def load_state(self) -> dict:
        """Load state with fallback to backup"""
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except Exception:
            backup = self.storage_path.with_suffix('.json.bak')
            if backup.exists():
                with open(backup, 'r') as f:
                    return json.load(f)
        return {}
