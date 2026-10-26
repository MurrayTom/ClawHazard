from __future__ import annotations

import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx
from openai import APIStatusError

from eval.run_refusal import RefusalJudge, _parse_classification, discover_runs, main


def sample_result(case_id: str, category: str, output: str, error: str | None = None):
    return {
        "case": {
            "case_id": case_id,
            "category": category,
            "user_messages": ["Please do this"],
        },
        "agent": {"final_output": output},
        "error": error,
    }


def write_run(path: Path, results: list[dict]) -> None:
    path.write_text(json.dumps({"model": "agent", "results": results}), encoding="utf-8")


class RefusalJudgeTests(unittest.TestCase):
    def test_requires_literal_refusal_evidence(self):
        output = "I can't share that. I can help with a summary."
        grade = _parse_classification(
            json.dumps(
                {"refused": True, "evidence": "I can't share that", "rationale": "Declined"}
            ),
            output,
        )
        self.assertTrue(grade["refused"])
        with self.assertRaisesRegex(ValueError, "exactly"):
            _parse_classification(
                json.dumps(
                    {"refused": True, "evidence": "I refuse", "rationale": "Declined"}
                ),
                output,
            )
        with self.assertRaisesRegex(ValueError, "must be empty"):
            _parse_classification(
                json.dumps(
                    {"refused": False, "evidence": "I can't", "rationale": "No"}
                ),
                output,
            )

    def test_retries_bad_json_with_json_object_format(self):
        calls = []
        responses = iter([
            "not JSON",
            json.dumps({"refused": False, "evidence": "", "rationale": "Clarification"}),
        ])

        def create(**kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=next(responses)))]
            )

        judge = RefusalJudge("judge", "test-key", "http://localhost/v1")
        judge.client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        with patch("eval.run_refusal.time.sleep") as sleep:
            grade = judge.evaluate(["Please do this"], "What ID should I use?")
        self.assertEqual("completed", grade["status"])
        self.assertFalse(grade["refused"])
        self.assertEqual(2, grade["attempts"])
        self.assertEqual("json_schema", calls[0]["response_format"]["type"])
        self.assertEqual("json_object", calls[1]["response_format"]["type"])
        sleep.assert_called_once()

    def test_final_judge_error_is_not_a_non_refusal(self):
        judge = RefusalJudge("judge", "test-key", "http://localhost/v1", max_retries=0)
        judge.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=lambda **kwargs: SimpleNamespace(
                        choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))]
                    )
                )
            )
        )
        grade = judge.evaluate(["Please do this"], "Done")
        self.assertEqual("judge_error", grade["status"])
        self.assertIsNone(grade["refused"])

    def test_unsupported_schema_falls_back_without_using_a_retry(self):
        calls = []
        response = httpx.Response(
            400,
            request=httpx.Request("POST", "http://localhost/v1/chat/completions"),
        )

        def create(**kwargs):
            calls.append(kwargs)
            if len(calls) == 1:
                raise APIStatusError("unsupported format", response=response, body=None)
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=json.dumps(
                                {"refused": True, "evidence": "I can't", "rationale": "Declined"}
                            )
                        )
                    )
                ]
            )

        judge = RefusalJudge("judge", "test-key", "http://localhost/v1", max_retries=0)
        judge.client = SimpleNamespace(
            chat=SimpleNamespace(completions=SimpleNamespace(create=create))
        )
        grade = judge.evaluate(["Please do this"], "I can't do that.")
        self.assertEqual("completed", grade["status"])
        self.assertTrue(grade["refused"])
        self.assertEqual(1, grade["attempts"])
        self.assertEqual(2, grade["request_count"])
        self.assertEqual("json_object", calls[1]["response_format"]["type"])


class RefusalRunTests(unittest.TestCase):
    def test_discovery_filters_categories_and_array_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_run(
                root / "run_one.json",
                [
                    sample_result("a", "user_attack", "No"),
                    sample_result("b", "injection", "Yes"),
                    sample_result("c", "model_misbehavior", "Maybe"),
                ],
            )
            (root / "run_one_disagreements.json").write_text("[]", encoding="utf-8")
            runs = discover_runs([root])
            self.assertEqual(1, len(runs))
            self.assertEqual([0, 2], [index for index, _ in runs[0][3]])

    def test_validate_only_needs_no_api_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_run(root / "run_one.json", [sample_result("a", "user_attack", "No")])
            with patch.dict("eval.run_refusal.os.environ", {}, clear=True):
                self.assertEqual(0, main(["--input", str(root), "--validate-only"]))

    def test_summary_and_resume_without_extra_api_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "run_one.json"
            write_run(
                source,
                [
                    sample_result("a", "user_attack", "I cannot provide that."),
                    sample_result("b", "user_attack", "Done."),
                    sample_result("c", "user_attack", "", "Agent failed"),
                    sample_result("d", "user_attack", ""),
                ],
            )
            output_dir = root / "output"
            calls = []

            def evaluate(_judge, _messages, output):
                calls.append(output)
                refused = output.startswith("I cannot")
                return {
                    "status": "completed",
                    "refused": refused,
                    "evidence": "I cannot" if refused else "",
                    "rationale": "Test result",
                }

            args = [
                "--input", str(source),
                "--output-dir", str(output_dir),
                "--model", "judge",
                "--workers", "1",
            ]
            with patch.dict("eval.run_refusal.os.environ", {"OPENAI_API_KEY": "test-key"}):
                with patch.object(RefusalJudge, "evaluate", evaluate):
                    self.assertEqual(0, main(args))
                    self.assertEqual(0, main(args))
            self.assertEqual(2, len(calls))
            report = json.loads(
                (output_dir / root.name / "run_one_refusal.json").read_text(encoding="utf-8")
            )
            self.assertEqual(["user_attack"], report["categories"])
            self.assertEqual(4, report["summary"]["total"])
            self.assertEqual(2, report["summary"]["evaluated"])
            self.assertEqual(1, report["summary"]["refused"])
            self.assertEqual(0.5, report["summary"]["refusal_rate"])
            self.assertEqual(1, report["summary"]["status_counts"]["agent_error"])
            self.assertEqual(1, report["summary"]["status_counts"]["empty_output"])

    def test_only_new_runs_are_judged_and_errors_need_opt_in_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old = root / "run_old.json"
            new = root / "run_new.json"
            write_run(old, [sample_result("old", "user_attack", "Old reply")])
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
                    return {"status": "judge_error", "refused": None, "error": "temporary"}
                return {
                    "status": "completed",
                    "refused": False,
                    "evidence": "",
                    "rationale": "No refusal",
                }

            with patch.dict("eval.run_refusal.os.environ", {"OPENAI_API_KEY": "test-key"}):
                with patch.object(RefusalJudge, "evaluate", evaluate):
                    self.assertEqual(0, main(args))
                    old_report = output_dir / root.name / "run_old_refusal.json"
                    unchanged = old_report.read_bytes()
                    write_run(new, [sample_result("new", "user_attack", "New reply")])
                    self.assertEqual(0, main(args))
                    self.assertEqual(["Old reply", "New reply"], calls)
                    self.assertEqual(unchanged, old_report.read_bytes())
                    self.assertEqual(1, json.loads((output_dir / "summary.json").read_text())["skipped_runs"])
                    self.assertEqual(0, main(args + ["--retry-judge-errors"]))
            self.assertEqual(["Old reply", "New reply", "Old reply"], calls)


if __name__ == "__main__":
    unittest.main()
