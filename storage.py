"""
storage.py — JSON persistence layer for bot data.

Handles loading/saving:
  - welcomed_users.json  (list of user IDs who already got the welcome)
  - verification_timestamps.json  (user_id -> unix timestamp of verification)
"""

import json
from typing import Any, Set, Dict

WELCOMED_FILE = "welcomed_users.json"
TIMESTAMPS_FILE = "verification_timestamps.json"


def _load(path: str, default: Any = None) -> Any:
    """Load JSON data from a file, returning `default` on failure."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else {}


def _save(path: str, data: Any) -> None:
    """Write JSON data to a file."""
    with open(path, "w") as f:
        json.dump(data, f)


# ── Welcomed users (set of ints) ────────────────────────────────

def load_welcomed_users() -> Set[int]:
    return set(_load(WELCOMED_FILE, []))


def save_welcomed_users(users: Set[int]) -> None:
    _save(WELCOMED_FILE, list(users))


# ── Verification timestamps (str(user_id) → float) ──────────────

def load_timestamps() -> Dict[str, float]:
    return _load(TIMESTAMPS_FILE, {})


def save_timestamps(timestamps: Dict[str, float]) -> None:
    _save(TIMESTAMPS_FILE, timestamps)