from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Any


DECISIVE_STATUSES = {"passed", "failed"}
UNRESOLVED_STATUSES = {"needs_judge", "not_configured"}
DIMENSIONS = ("safety", "utility")


def disagreement_dimensions(
    result: dict[str, Any],
    dimensions: tuple[str, ...] = DIMENSIONS,
    include_unresolved: bool = False,
) -> list[str]:
    mismatches = []
    for dimension in dimensions:
        evaluation = result.get(dimension, {})
        if not isinstance(evaluation, dict):
            continue
        executable = evaluation.get("executable", {})
        rubric = evaluation.get("rubric", {})
        if not isinstance(executable, dict) or not isinstance(rubric, dict):
            continue
        executable_status = executable.get("status")
        rubric_status = rubric.get("status")
        if rubric_status not in DECISIVE_STATUSES:
            continue
        opposite = (
            executable_status in DECISIVE_STATUSES
            and executable_status != rubric_status
        )
        unresolved = (
            include_unresolved and executable_status in UNRESOLVED_STATUSES
        )
        if opposite or unresolved:
            mismatches.append(dimension)
    return mismatches


def find_disagreements(
    document: dict[str, Any],
    dimensions: tuple[str, ...] = DIMENSIONS,
    include_unresolved: bool = False,
) -> list[dict[str, Any]]:
    results = document.get("results")
    if not isinstance(results, list):
        raise ValueError("Input JSON must contain a results array")
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            raise ValueError(f"results[{index}] must be an object")
    return [
        result
        for result in results
        if disagreement_dimensions(result, dimensions, include_unresolved)
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Save result items where executable and rubric judgments disagree."
    )
    parser.add_argument("input", type=Path, help="Evaluation result JSON file")
    parser.add_argument(
        "--output",
        type=Path,
        help="Output JSON array; defaults to <input_stem>_disagreements.json",
    )
    parser.add_argument(
        "--dimension", choices=("all", *DIMENSIONS), default="all"
    )
    parser.add_argument(
        "--include-unresolved",
        action="store_true",
        help="Also include needs_judge/not_configured vs. decisive rubric results",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    document = json.loads(args.input.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise SystemExit("Input JSON must be an object")
    dimensions = DIMENSIONS if args.dimension == "all" else (args.dimension,)
    selected = find_disagreements(document, dimensions, args.include_unresolved)
    output = args.output or args.input.with_name(
        f"{args.input.stem}_disagreements.json"
    )
    if output.resolve() == args.input.resolve():
        raise SystemExit("Output must differ from input")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(selected, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    counts = Counter(
        dimension
        for result in selected
        for dimension in disagreement_dimensions(
            result, dimensions, args.include_unresolved
        )
    )
    print(
        f"Wrote {len(selected)} result items "
        f"(safety={counts['safety']}, utility={counts['utility']}) to {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
