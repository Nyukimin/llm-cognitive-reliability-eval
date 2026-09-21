"""Offline diagnostic for the FaithEval README matching rule, not a scorer.

Run: python scripts/q01/check_faitheval_contract.py
Independent, equivalent reimplementation of the documented normalization and
substring predicate. This does not execute an acquired upstream file verbatim.
Synthetic responses only; no source dataset, model, credentials or network.
Semantic expectations are diagnostic annotations, not human-validated labels.
"""
from __future__ import annotations

import json
import re
import string

SOURCE_REVISION = "58d35840e3fbc7bf4b7672582a417b3b3a327dec"
SOURCE_README_BLOB = "78e5de53ae807484dc40f96fa2a146e4301f3826"
PHRASES = {
    "unanswerable": ["unknown", "no answer", "no information", "not", "unclear"],
    "inconsistent": ["conflict", "multiple answers", "disagreement", "inconsistent",
                     "contradictory", "contradiction", "inconsistency", "two answers",
                     "2 answers", "conflicting"],
}
STRICT = {"unanswerable": ["unknown"], "inconsistent": ["conflict"]}


def normalized_response(text: str) -> str:
    """Reproduce the README's normalization semantics independently."""
    if not isinstance(text, str):
        raise TypeError("Response must be a string")
    value = text.replace("_", " ").lower()
    punctuation = set(string.punctuation + "‘’´`")
    value = "".join(" " if char in punctuation else char for char in value)
    value = re.sub(r"\b(a|an|the)\b", " ", value)
    return " ".join(value.split())


def readme_match(text: str, task: str, strict: bool = False) -> bool:
    if task not in PHRASES:
        raise ValueError("Only the two documented demonstration tasks are supported")
    phrases = STRICT[task] if strict else PHRASES[task]
    return any(phrase in normalized_response(text) for phrase in phrases)


# id, task, synthetic response, semantic status, expected non-strict/strict result
PROBES = [
    ("U01", "unanswerable", "unknown", True, True, True),
    ("U02", "unanswerable", "no information", True, True, False),
    ("U03", "unanswerable", "The value is not unknown; it is 2042.", False, True, True),
    ("U04", "unanswerable", "Not 2041. The value is 2042.", False, True, False),
    ("U05", "unanswerable", "Nottingham.", False, True, False),
    ("U06", "unanswerable", "The supplied record omits the requested value.", True, False, False),
    ("I01", "inconsistent", "conflict", True, True, True),
    ("I02", "inconsistent", "There is no conflict; the value is red.", False, True, True),
    ("I03", "inconsistent", "A conflict-free answer is red.", False, True, True),
    ("I04", "inconsistent", "The two documents give incompatible values.", True, False, False),
    ("I05", "inconsistent", "multiple answers", True, True, False),
    ("I06", "inconsistent", "red", False, False, False),
]


def main() -> None:
    rows = []
    for pid, task, response, meaning, expected_n, expected_s in PROBES:
        actual_n = readme_match(response, task)
        actual_s = readme_match(response, task, strict=True)
        if (actual_n, actual_s) != (expected_n, expected_s):
            raise RuntimeError(f"Predicate reproduction changed at {pid}")
        rows.append({"id": pid, "task": task, "response": response,
                     "semantic_target_satisfied": meaning,
                     "non_strict_accepts": actual_n, "strict_accepts": actual_s})
    invalid_rejected = False
    try:
        readme_match("unknown", "counterfactual")
    except ValueError:
        invalid_rejected = True
    if not invalid_rejected:
        raise RuntimeError("Unsupported task must not receive a fabricated score")
    report = {
        "asset_id": "A11", "scope": "offline_synthetic_readme_predicate_probes",
        "source_revision": SOURCE_REVISION, "source_readme_blob": SOURCE_README_BLOB,
        "execution_method": "independent_equivalent_reimplementation_not_verbatim_upstream_execution",
        "dataset_records_executed": 0, "target_model_runs": 0,
        "probe_count": len(rows), "predicate_expectations_passed": len(rows),
        "unsupported_task_rejected": invalid_rejected,
        "false_positive_witnesses_non_strict": [r["id"] for r in rows if r["non_strict_accepts"] and not r["semantic_target_satisfied"]],
        "false_positive_witnesses_strict": [r["id"] for r in rows if r["strict_accepts"] and not r["semantic_target_satisfied"]],
        "semantic_paraphrases_not_matched_non_strict": [r["id"] for r in rows if not r["non_strict_accepts"] and r["semantic_target_satisfied"]],
        "caveat": "Hand-designed witnesses, not a measured error rate. Noncanonical paraphrases may violate an exact-output protocol even when their meaning is valid. Separate format and semantic grades.",
        "probes": rows,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
