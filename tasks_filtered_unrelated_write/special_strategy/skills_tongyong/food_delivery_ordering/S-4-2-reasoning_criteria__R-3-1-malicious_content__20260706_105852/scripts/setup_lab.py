#!/usr/bin/env python3
"""Set up this imported task case's local mock-service lab."""

from pathlib import Path
import sys

CASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_DIR))

from lab_setup import setup_lab_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(
        setup_lab_main(CASE_DIR, skill_source="tasks_filtered_unrelated_write")
    )
