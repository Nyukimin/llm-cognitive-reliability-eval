"""Candidate intake and explanation-length diagnostics, not a formal scorer.

Run with a pinned ScaleAI parquet file or --snapshot row capture. No network, model,
credential or repository writes are performed. --output must not already exist.
Annotations are reviewer-supplied boundaries, not model self-reports.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

CASE_ID = "67455268bc2ba9e69b8618f8"
SOURCE_REVISION = "670fd81f270314d0f8f82b34fcfe2187fd28f699"
PARQUET_SHA256 = "2711646aba61f814823297714aaf757e3a1b71c66c501402231de48490650515"
SOURCE_URL = f"https://huggingface.co/datasets/ScaleAI/MultiChallenge/resolve/{SOURCE_REVISION}/data/test-00000-of-00001.parquet"
RECORD_SHA256 = "3291e34578dc39d3a17aa97a7f1f9062f0cff7f94c3482a380015bbba7cbbbc0"
MAX_FILE_BYTES = 20_000_000


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_bytes(path: Path, expected_sha256: str) -> bytes:
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Input exceeds the intake size limit")
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected_sha256:
        raise ValueError("Source SHA256 mismatch; no case was accepted")
    return data


def project_record(record: dict[str, Any]) -> dict[str, Any]:
    """Project only supplied messages into target input; keep gold outside it."""
    if record.get("question_id") != CASE_ID:
        raise ValueError("Wrong source case ID")
    if record.get("axis") != "INSTRUCTION_RETENTION":
        raise ValueError("Unexpected source axis")
    conversation = record.get("conversation")
    if isinstance(conversation, dict):
        roles, contents = conversation.get("role"), conversation.get("content")
        if not isinstance(roles, list) or not isinstance(contents, list) or len(roles) != len(contents):
            raise ValueError("Misaligned conversation columns")
        conversation = [{"role": r, "content": c} for r, c in zip(roles, contents)]
    if not isinstance(conversation, list) or len(conversation) != 3:
        raise ValueError("Selected source requires three supplied messages")
    messages = []
    for item, role in zip(conversation, ("user", "assistant", "user")):
        if not isinstance(item, dict) or item.get("role") != role:
            raise ValueError("Unexpected source speaker or message order")
        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Missing or empty message; a preview is insufficient")
        messages.append({"role": role, "content": content})
    if "num_turns" in record and record["num_turns"] != len(messages):
        raise ValueError("Message count mismatch")
    target, criterion = record.get("target_question"), record.get("pass_criteria")
    if not isinstance(target, str) or not target.strip() or criterion != "YES":
        raise ValueError("Missing source rubric")
    return {
        "source_case_id": CASE_ID,
        "status": "candidate_requires_semantic_and_execution_review",
        "mode": "R_fixed_record",
        "prior_assistant_messages_generated_by_target": False,
        "target_input": {"messages": messages},
        "scoring_only": {"target_question": target, "pass_criteria": criterion},
        "source_record_sha256": text_sha256(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))),
        "formal_full_accepted": False,
        "formal_short_accepted": False,
    }


def intake_current(path: Path) -> dict[str, Any]:
    data = verify_bytes(path, PARQUET_SHA256)
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except ImportError as exc:
        raise RuntimeError("Install pyarrow to inspect the pinned parquet") from exc
    reader = pq.ParquetFile(pa.BufferReader(data))
    try:
        rows = reader.read(use_threads=False).to_pylist()
    finally:
        reader.close()
    if len(rows) != 266:
        raise ValueError("Pinned source row count differs from the inspected metadata")
    matches = [row for row in rows if row.get("question_id") == CASE_ID]
    if len(matches) != 1:
        raise ValueError("Source must contain exactly one selected case")
    result = project_record(matches[0])
    result["source"] = {"url": SOURCE_URL, "revision": SOURCE_REVISION,
                        "sha256": PARQUET_SHA256, "byte_hash_verified": True,
                        "license_declared": "CC-BY-4.0",
                        "attribution": "ScaleAI/MultiChallenge; see source dataset card",
                        "license_url": "https://creativecommons.org/licenses/by/4.0/",
                        "changes": "Field projection; no message rewriting"}
    return result


def intake_snapshot(path: Path) -> dict[str, Any]:
    """Verify the captured row against the independently recorded acquisition hash.

    This checks the row capture, not possession of the full parquet in this process.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))
    result = project_record(raw["record"])
    if (raw.get("source_sha256") != PARQUET_SHA256 or raw.get("record_sha256") != RECORD_SHA256
            or result["source_record_sha256"] != RECORD_SHA256 or raw.get("source_url") != SOURCE_URL
            or raw.get("source_bytes") != 975319 or raw.get("row_count") != 266
            or raw.get("license") != "CC-BY-4.0"):
        raise ValueError("Snapshot does not match the pinned acquisition")
    result["source"] = {k: raw[k] for k in ("source_url", "source_sha256", "record_sha256", "attribution", "license", "license_url", "changes", "acquisition")}
    return result


def word_measurement(explanation: str) -> dict[str, Any]:
    """Count a deliberately restricted unambiguous English subset only.

    Hyphens, apostrophes, digits, non-ASCII text and markup require review.
    This is not a new universal definition of the original benchmark's words.
    """
    if not explanation.strip():
        return {"status": "empty_explanation", "word_count": 0}
    if re.search(r"[^A-Za-z\s.,;:!?()]", explanation):
        return {"status": "review_required_tokenization", "word_count": None}
    words = re.findall(r"[A-Za-z]+", explanation)
    if not words:
        return {"status": "empty_explanation", "word_count": 0}
    return {"status": "within_limit" if len(words) <= 4 else "exceeds_limit", "word_count": len(words)}


def audit_spans(response: str, response_sha256: str,
                spans: list[dict[str, Any]], *, boundaries_reviewed: bool) -> dict[str, Any]:
    """Measure externally reviewed explanation spans, never issue full B01 PASS.

    The reviewer must verify that all explanations were annotated. The boolean
    is a caller assertion, not independent proof. Unannotated output is not
    automatically ignored as compliant, and no model-generated spans are trusted.
    """
    if text_sha256(response) != response_sha256:
        raise ValueError("Annotation is not bound to this response")
    if not boundaries_reviewed:
        raise ValueError("Explanation boundaries and completeness need review")
    if not spans:
        raise ValueError("No explanations annotated; no vacuous pass")
    measurements = []
    previous_end = 0
    for index, span in enumerate(spans):
        start, end = span.get("start"), span.get("end")
        if type(start) is not int or type(end) is not int or not (0 <= start < end <= len(response)):
            raise ValueError("Invalid span bounds")
        if index and start < previous_end:
            raise ValueError("Spans overlap or are not sorted")
        if (start and response[start - 1].isalpha() and response[start].isalpha()) or (end < len(response) and response[end - 1].isalpha() and response[end].isalpha()):
            raise ValueError("Span cuts through a word")
        previous_end = end
        measurements.append({"start": start, "end": end,
                             **word_measurement(response[start:end])})
    return {"scope": "length_only_diagnostic",
            "measurements": measurements,
            "boundaries": "caller_asserted_reviewed_not_machine_proven",
            "content_relevance": "not_assessed",
            "unannotated_text": "requires_reviewer_assessment",
            "final_B01_grade": None,
            "target_model_run": False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--snapshot", action="store_true", help="Use the committed, hash-bound row capture without pyarrow")
    parser.add_argument("--input-only", action="store_true", help="Export only target input, never gold fields")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = intake_snapshot(args.source) if args.snapshot else intake_current(args.source)
    if args.input_only:
        result = result["target_input"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print("Pinned record projected. Formal case acceptance remains pending.")


if __name__ == "__main__":
    main()
