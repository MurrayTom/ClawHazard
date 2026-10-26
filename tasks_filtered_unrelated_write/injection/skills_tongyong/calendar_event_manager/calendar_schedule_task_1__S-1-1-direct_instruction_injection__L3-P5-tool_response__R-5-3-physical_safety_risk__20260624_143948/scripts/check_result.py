#!/usr/bin/env python3
"""Evaluate captured state and tool-call evidence for this task case."""

from pathlib import Path
import sys

CASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(PROJECT_DIR))

from task_check_result import check_result_main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(check_result_main(CASE_DIR))
