#!/usr/bin/env python3
"""Evaluate this skills_v2.0 injection case from captured artifacts."""

from pathlib import Path
import sys

SKILL_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_DIR))

from v2_check_result import check_result_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(check_result_main(SKILL_DIR))
