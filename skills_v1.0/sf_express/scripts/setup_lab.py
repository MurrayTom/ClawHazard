#!/usr/bin/env python3
"""Set up this skills_v1.0 skill lab."""

from pathlib import Path
import sys

SKILL_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_DIR))

from lab_setup import setup_lab_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(setup_lab_main(SKILL_DIR))
