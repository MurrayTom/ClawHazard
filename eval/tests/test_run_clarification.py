from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from eval.run_clarification import ClarificationJudge, main


def sample_result(case_id: str, category: str, output: str, error: str | None = None):
    return {
        "case": {
            "case_id": case_id,
            "category": category,
            "user_messages": ["Please handle the order"],
        },
        "agent": {"final_output": output},
        "error": error,
    }


class ClarificationJudgeTests(unittest.TestCase):
    def test_judge_receives_user_messages_and_output(self):
        calls = []

        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=json.dumps(
                                {
                                    "asks_clarification": True,
                                    "evidence": "Which order ID",
                                    "rationale": "Needs an identifier",
                                }
                            )
                        )
                    )
                ]
            )

        judge = ClarificationJudge("judge", "test-key", "http://localhost/v1")
        judge.client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        grade = judge.evaluate(
            ["Please handle the order"], "Which order ID should I use?"
        )
        self.assertEqual("completed", grade["status"])
        self.assertTrue(grade["asks_clarification"])
        self.assertEqual("Which order ID", grade["evidence"])
        self.assertEqual("json_schema", calls[0]["response_format"]["type"])
        self.assertEqual(
            "clarification_classification",
            calls[0]["response_format"]["json_schema"]["name"],
        )
        supplied = json.loads(calls[0]["messages"][1]["content"])
        self.assertEqual(["Please handle the order"], supplied["user_messages"])
        self.assertEqual("Which order ID should I use?", supplied["assistant_output"])

    def test_invalid_evidence_is_a_judge_error(self):
        judge = ClarificationJudge(
            "judge", "test-key", "http://localhost/v1", max_retries=0
        )
        judge.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kwargs: SimpleNamespace(
                        choices=[
                            SimpleNamespace(
                                message=SimpleNamespace(
                                    content=json.dumps(
                                        {
                                            "asks_clarification": True,
                                            "evidence": "Missing exact phrase",
                                            "rationale": "Needs details",
                                        }
                                    )
                                )
                            )
                        ]
                    )
                )
            )
        )
        grade = judge.evaluate(["Handle it"], "Please provide the ID.")
        self.assertEqual("judge_error", grade["status"])
        self.assertIsNone(grade["asks_clarification"])


class ClarificationRunTests(unittest.TestCase):
    def test_validate_only_selects_model_misbehavior_without_api_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "run_one.json"
            path.write_text(
                json.dumps(
                    {
                        "results": [
                            sample_result("mm", "model_misbehavior", "Which ID?"),
                            sample_result("ua", "user_attack", "Which ID?"),
                        ]
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict("eval.run_clarification.os.environ", {}, clear=True):
                self.assertEqual(0, main(["--input", str(path), "--validate-only"]))

    def test_summary_and_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "run_one.json"
            source.write_text(
                json.dumps(
                    {
                        "model": "agent",
                        "results": [
                            sample_result("a", "model_misbehavior", "Which ID?"),
                            sample_result("b", "model_misbehavior", "Done."),
                            sample_result("c", "model_misbehavior", "", "Agent failed"),
                            sample_result("d", "model_misbehavior", ""),
                            sample_result("e", "user_attack", "Which ID?"),
                        ],
                    }
                ),
                encoding="utf-8",
            )
            output_dir = root / "output"
            calls = []

            def evaluate(_judge, _messages, output):
                calls.append(output)
                positive = output.startswith("Which")
                return {
                    "status": "completed",
                    "asks_clarification": positive,
                    "evidence": "Which ID" if positive else "",
                    "rationale": "Test result",
                }

            args = [
                "--input", str(source),
                "--output-dir", str(output_dir),
                "--model", "judge",
                "--workers", "1",
            ]
            with patch.dict("eval.run_clarification.os.environ", {"OPENAI_API_KEY": "test-key"}):
                with patch.object(ClarificationJudge, "evaluate", evaluate):
                    self.assertEqual(0, main(args))
                    self.assertEqual(0, main(args))
            self.assertEqual(2, len(calls))
            report = json.loads(
                (output_dir / root.name / "run_one_clarification.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual("model_misbehavior", report["category"])
            self.assertEqual(4, report["summary"]["total"])
            self.assertEqual(2, report["summary"]["evaluated"])
            self.assertEqual(1, report["summary"]["clarification_count"])
            self.assertEqual(0.5, report["summary"]["clarification_rate"])
            self.assertEqual(1, report["summary"]["status_counts"]["agent_error"])
            self.assertEqual(1, report["summary"]["status_counts"]["empty_output"])

    def test_only_new_runs_are_judged_and_errors_need_opt_in_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / "run_old.json"
            new = root / "run_new.json"
            old.write_text(
                json.dumps({"results": [sample_result("old", "model_misbehavior", "Old reply")]}),
                encoding="utf-8",
            )
            output_dir = root / "output"
            args = [
                "--input", str(root),
                "--output-dir", str(output_dir),
                "--model", "judge",
                "--workers", "1",
            ]
            calls = []

            def evaluate(_judge, _messages, output):
                calls.append(output)
                if output == "Old reply" and calls.count(output) == 1:
                    return {
                        "status": "judge_error",
                        "asks_clarification": None,
                        "error": "temporary",
                    }
                return {
                    "status": "completed",
                    "asks_clarification": False,
                    "evidence": "",
                    "rationale": "No clarification",
                }

            with patch.dict("eval.run_clarification.os.environ", {"OPENAI_API_KEY": "test-key"}):
                with patch.object(ClarificationJudge, "evaluate", evaluate):
                    self.assertEqual(0, main(args))
                    old_report = output_dir / root.name / "run_old_clarification.json"
                    unchanged = old_report.read_bytes()
                    new.write_text(
                        json.dumps(
                            {"results": [sample_result("new", "model_misbehavior", "New reply")]}
                        ),
                        encoding="utf-8",
                    )
                    self.assertEqual(0, main(args))
                    self.assertEqual(["Old reply", "New reply"], calls)
                    self.assertEqual(unchanged, old_report.read_bytes())
                    self.assertEqual(1, json.loads((output_dir / "summary.json").read_text())["skipped_runs"])
                    self.assertEqual(0, main(args + ["--retry-judge-errors"]))
            self.assertEqual(["Old reply", "New reply", "Old reply"], calls)


if __name__ == "__main__":
    unittest.main()
