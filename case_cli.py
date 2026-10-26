"""Backward-compatible wrapper for the canonical CLI in main.py."""

from main import main


if __name__ == "__main__":
    raise SystemExit(main())
