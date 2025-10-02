"""Package providing bundled data assets for Vibe Check."""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent
RESPONSE_BANK_PATH = DATA_DIR / "response_bank.json"

__all__ = ["DATA_DIR", "RESPONSE_BANK_PATH"]
