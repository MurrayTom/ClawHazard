from __future__ import annotations

from collections import Counter
from typing import Any


def _component_metrics(
    results: list[dict[str, Any]], dimension: str, component: str | None
) -> dict[str, Any]:
    statuses: Counter[str] = Counter()
    scores: list[float] = []
    for result in results:
        dimension_result = result.get(dimension, {})
        value = dimension_result if component is None else dimension_result.get(component, {})
        if not isinstance(value, dict):
            continue
        status = value.get("status")
        if component == "rubric" and isinstance(value.get("threshold_passed"), bool):
            status = "passed" if value["threshold_passed"] else "failed"
        if not isinstance(status, str):
            continue
        statuses[status] += 1
        if status not in {"passed", "failed"}:
            continue
        score = value.get("score")
        if score is None and dimension == "safety" and isinstance(value.get("safe"), bool):
            score = float(value["safe"])
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            scores.append(float(score))
    evaluated = statuses["passed"] + statuses["failed"]
    return {
        "status_counts": dict(statuses),
        "pass_rate": statuses["passed"] / evaluated if evaluated else None,
        "mean_score": sum(scores) / len(scores) if scores else None,
        "evaluated": evaluated,
        "scored": len(scores),
        "not_applicable": statuses["not_applicable"],
    }


def aggregate_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    completed = [result for result in results if not result.get("error")]
    judge_results = [result.get("judge", {}) for result in completed]
    judge_status = Counter(
        judge.get("status", "unknown") for judge in judge_results
    )
    dimensions: dict[str, dict[str, Any]] = {}
    for dimension in ("safety", "utility"):
        combined = _component_metrics(completed, dimension, None)
        executable = _component_metrics(completed, dimension, "executable")
        rubric = _component_metrics(completed, dimension, "rubric")
        dimensions[dimension] = {
            **combined,
            "executable_status_counts": executable["status_counts"],
            "rubric_status_counts": rubric["status_counts"],
            "executable": executable,
            "rubric": rubric,
        }
    return {
        "total": len(results),
        "completed": len(completed),
        "errors": len(results) - len(completed),
        "judge_status_counts": dict(judge_status),
        "judge_retries_total": sum(judge.get("retry_count", 0) for judge in judge_results),
        "judge_retried_cases": sum(
            judge.get("retry_count", 0) > 0 for judge in judge_results
        ),
        "judge_request_total": sum(
            judge.get("request_count", 0) for judge in judge_results
        ),
        **dimensions,
    }
