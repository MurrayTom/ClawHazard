from __future__ import annotations

import sys

from .run_main import main


if __name__ == "__main__":
    arguments = sys.argv[1:]
    if "--workers" not in arguments:
        arguments.extend(["--workers", "1"])
    raise SystemExit(main(arguments))
