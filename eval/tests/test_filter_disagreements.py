from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from eval.filter_disagreements import (
    disagreement_dimensions,
    find_disagreements,
    main,
)


def sample_result(case_id, executable_status, rubric_status, utility_pair=None):
    def grade(pair):
        return {
            "executable": {"status": pair[0], "score": 0.0, "checks": []},
            "rubric": {
                "status": pair[1],
                "score": 1.0,
                "rationale": "Judge explanation",
                "criteria": [{"criterion": "S1", "passed": True, "evidence": "Evidence"}],
            },
        }

    return {
        "case": {
            "case_id": case_id,
            "category": "injection",
            "skill_name": "demo",
            "task_dir": "/tmp/demo",
            "user_messages": ["Find the item"],
        },
        "safety": grade((executable_status, rubric_status)),
        "utility": grade(utility_pair or ("passed", "passed")),
        "agent": {
            "tool_executions": [
                {
                    "operation": "find_item",
                    "params": {"id": "I1"},
                    "response": {"success": True},
                    "error": None,
                }
            ],
            "final_output": "The item is here.",
        },
        "environment": {"state_before": {}, "state_after": {}},
    }


class FilterDisagreementsTests(unittest.TestCase):
    def setUp(self):
        self.document = {
            "results": [
                sample_result("opposite", "passed", "failed", ("failed", "passed")),
                sample_result("unresolved", "needs_judge", "passed"),
                sample_result("judge-error", "failed", "error"),
                sample_result("agreed", "passed", "passed"),
            ]
        }

    def test_only_decisive_opposites_are_selected_by_default(self):
        selected = find_disagreements(self.document)
        self.assertEqual([self.document["results"][0]], selected)
        self.assertIs(self.document["results"][0], selected[0])
        self.assertEqual(
            ["safety", "utility"], disagreement_dimensions(selected[0])
        )

    def test_unresolved_is_opt_in_and_dimension_filter_applies(self):
        selected = find_disagreements(
            self.document, ("safety",), include_unresolved=True
        )
        self.assertEqual(self.document["results"][:2], selected)

    def test_default_output_is_plain_json_array(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            input_path.write_text(json.dumps(self.document), encoding="utf-8")
            self.assertEqual(0, main([str(input_path)]))
            output_path = Path(directory) / "input_disagreements.json"
            selected = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual([self.document["results"][0]], selected)

    def test_json_output_preserves_selected_case(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "selected.json"
            input_path.write_text(json.dumps(self.document), encoding="utf-8")
            self.assertEqual(
                0,
                main([str(input_path), "--output", str(output_path)]),
            )
            selected = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual([self.document["results"][0]], selected)


if __name__ == "__main__":
    unittest.main()
