"""Offline contract tests plus captured-row checks; no model or network use."""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("case_intake", ROOT / "scripts/q01/inspect_multichallenge_case.py")
m = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(m)


def fixture():
    return {"question_id": m.CASE_ID, "axis": "INSTRUCTION_RETENTION",
            "conversation": [{"role": "user", "content": "Synthetic requirement."},
                             {"role": "assistant", "content": "Synthetic prior response."},
                             {"role": "user", "content": "Synthetic follow-up."}],
            "target_question": "SCORING_ONLY_SENTINEL", "pass_criteria": "YES", "num_turns": 3,
            "answerKey": "MUST_NOT_LEAK", "justification": "MUST_NOT_LEAK"}


class ContractTests(unittest.TestCase):
    def test_gold_excluded(self):
        import json
        result = m.project_record(fixture())
        self.assertNotIn("SCORING_ONLY_SENTINEL", json.dumps(result["target_input"]))
        self.assertNotIn("MUST_NOT_LEAK", json.dumps(result["target_input"]))
        self.assertEqual(result["mode"], "R_fixed_record")
        self.assertFalse(result["formal_full_accepted"])
    def test_columnar_conversation(self):
        record = fixture()
        record["conversation"] = {k: [x[k] for x in record["conversation"]] for k in ("role", "content")}
        self.assertEqual(len(m.project_record(record)["target_input"]["messages"]), 3)
    def test_wrong_id(self):
        record = fixture(); record["question_id"] = "other"
        with self.assertRaises(ValueError): m.project_record(record)
    def test_wrong_axis(self):
        record = fixture(); record["axis"] = "OTHER"
        with self.assertRaises(ValueError): m.project_record(record)
    def test_missing_message(self):
        record = fixture(); record["conversation"][-1]["content"] = ""
        with self.assertRaises(ValueError): m.project_record(record)
    def test_wrong_speaker(self):
        record = fixture(); record["conversation"][1]["role"] = "user"
        with self.assertRaises(ValueError): m.project_record(record)
    def test_wrong_turn_count(self):
        record = fixture(); record["num_turns"] = 9
        with self.assertRaises(ValueError): m.project_record(record)
    def test_missing_rubric(self):
        record = fixture(); del record["target_question"]
        with self.assertRaises(ValueError): m.project_record(record)
    def test_misaligned_columns(self):
        record = fixture(); record["conversation"] = {"role": ["user"], "content": []}
        with self.assertRaises(ValueError): m.project_record(record)
    def test_source_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source"; path.write_bytes(b"synthetic")
            self.assertEqual(m.verify_bytes(path, hashlib.sha256(b"synthetic").hexdigest()), b"synthetic")
            with self.assertRaises(ValueError): m.verify_bytes(path, m.PARQUET_SHA256)
    def test_four_words(self):
        self.assertEqual(m.word_measurement("Shared meanings shape belonging.")["status"], "within_limit")
    def test_five_words(self):
        self.assertEqual(m.word_measurement("Shared meanings shape social belonging.")["status"], "exceeds_limit")
    def test_ambiguous_tokenization(self):
        for text in ("In-group norms shape belonging.", "Members' values shape belonging.", "所属を形成する", "One/two define groups."):
            with self.subTest(text=text):
                self.assertEqual(m.word_measurement(text)["status"], "review_required_tokenization")
    def test_empty_explanation(self):
        self.assertEqual(m.word_measurement("...")["status"], "empty_explanation")
    def test_title_not_explanation(self):
        response = "A Long Theory Title: Shared meanings shape belonging."
        start = response.index("Shared")
        result = m.audit_spans(response, m.text_sha256(response), [{"start": start, "end": len(response)}], boundaries_reviewed=True)
        self.assertEqual(result["measurements"][0]["word_count"], 4)
        self.assertIsNone(result["final_B01_grade"])
        self.assertEqual(result["content_relevance"], "not_assessed")
    def test_each_explanation_separately(self):
        response = "A: Groups define belonging.\nB: Norms guide behavior."
        spans = [{"start": response.index("Groups"), "end": response.index("\n")},
                 {"start": response.index("Norms"), "end": len(response)}]
        result = m.audit_spans(response, m.text_sha256(response), spans, boundaries_reviewed=True)
        self.assertEqual([x["word_count"] for x in result["measurements"]], [3, 3])
    def test_missing_annotations(self):
        with self.assertRaises(ValueError): m.audit_spans("", m.text_sha256(""), [], boundaries_reviewed=True)
    def test_unreviewed_boundaries(self):
        with self.assertRaises(ValueError): m.audit_spans("Text", m.text_sha256("Text"), [{"start": 0, "end": 4}], boundaries_reviewed=False)
    def test_wrong_response_hash(self):
        with self.assertRaises(ValueError): m.audit_spans("Text", m.text_sha256("Other"), [{"start": 0, "end": 4}], boundaries_reviewed=True)
    def test_invalid_span(self):
        for span in ({"start": -1, "end": 4}, {"start": True, "end": 4}, {"start": 0, "end": 90}):
            with self.subTest(span=span):
                with self.assertRaises(ValueError): m.audit_spans("Text", m.text_sha256("Text"), [span], boundaries_reviewed=True)
    def test_overlapping_spans(self):
        with self.assertRaises(ValueError): m.audit_spans("Text here", m.text_sha256("Text here"), [{"start": 0, "end": 4}, {"start": 0, "end": 9}], boundaries_reviewed=True)
    def test_mid_word(self):
        with self.assertRaises(ValueError): m.audit_spans("Text", m.text_sha256("Text"), [{"start": 1, "end": 4}], boundaries_reviewed=True)
    def test_word_limit_is_not_task_success(self):
        result = m.audit_spans("Unknown.", m.text_sha256("Unknown."), [{"start": 0, "end": 8}], boundaries_reviewed=True)
        self.assertEqual(result["measurements"][0]["status"], "within_limit")
        self.assertIsNone(result["final_B01_grade"])
    def test_pinned_real_record_capture(self):
        result = m.intake_snapshot(ROOT / "data/q01/case_reviews/A04_IR001_source.json")
        self.assertEqual(result["source_record_sha256"], m.RECORD_SHA256)
        self.assertEqual(len(result["target_input"]["messages"]), 3)
        self.assertFalse(result["prior_assistant_messages_generated_by_target"])
    def test_modified_snapshot_rejected(self):
        import json
        record = json.loads((ROOT / "data/q01/case_reviews/A04_IR001_source.json").read_text())
        record["record"]["conversation"]["content"][-1] += " changed"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "modified.json"
            path.write_text(json.dumps(record))
            with self.assertRaises(ValueError): m.intake_snapshot(path)
    def test_snapshot_source_pointer_tampering(self):
        import json
        raw = json.loads((ROOT / "data/q01/case_reviews/A04_IR001_source.json").read_text())
        raw["source_url"] = "https://example.invalid/other"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "modified.json"
            path.write_text(json.dumps(raw))
            with self.assertRaises(ValueError): m.intake_snapshot(path)
    def test_input_projection_does_not_mutate_source(self):
        record = fixture(); saved = copy.deepcopy(record)
        projected = m.project_record(record)
        projected["target_input"]["messages"][0]["content"] = "modified"
        self.assertEqual(record, saved)


if __name__ == "__main__":
    unittest.main()
