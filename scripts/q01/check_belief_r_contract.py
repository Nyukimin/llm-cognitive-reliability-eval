"""Offline A10 audit probes, not a benchmark or production scorer.

Usage: python scripts/q01/check_belief_r_contract.py UPSTREAM_PARSER.py
Provide src/prompts/utils.py from the pinned upstream commit. The upstream
source is not redistributed here. No models, credentials or network are used.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import itertools
import json
from pathlib import Path
import re

EXPECTED_BLOB = "c9fd905feb10c2d4a699013c2cf821251c18fcbf"
UPSTREAM_COMMIT = "e9cec77b14e7deea9d26b3b04c41fc08ab2094e3"


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def audit(parser_path: Path) -> dict:
    data = parser_path.read_bytes()
    observed = git_blob_id(data)
    if observed != EXPECTED_BLOB:
        raise ValueError(f"Unexpected upstream parser blob: {observed}")
    tree = ast.parse(data.decode("utf-8"))
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef)
             and n.name == "get_final_answer"]
    if len(funcs) != 1:
        raise ValueError("Expected exactly one get_final_answer function")
    namespace = {"re": re}
    # Execute only the exact-hash-pinned parser function, not module imports.
    exec(compile(ast.Module(body=funcs, type_ignores=[]),
                 "<pinned-upstream-parser>", "exec"), namespace)
    parser = namespace["get_final_answer"]
    probes = []
    for text, expected in [("Final Answer [a].", "a"),
                           ("Final Answer [c].", "c"),
                           ("Final Answer [z].", "z"),
                           ("12345678901a", "a")]:
        got = parser(text)
        if got != expected:
            raise AssertionError((text, expected, got))
        probes.append({"input": text, "observed_output": got})

    logical = []
    for mode in ("ponens", "tollens"):
        for semantics in ("material_implication", "explicit_rule_replacement"):
            worlds = []
            for p, q, r in itertools.product((False, True), repeat=3):
                # Replacement is a DIFFERENT premise set, not an inference
                # licensed by merely adding r -> q to the original set.
                rule = ((not p) or q) if semantics == "material_implication" else ((not (p and r)) or q)
                observed_fact = p if mode == "ponens" else not q
                extra = ((not r) or q) if semantics == "material_implication" else True
                if rule and observed_fact and extra:
                    worlds.append({"p": p, "q": q, "r": r})
            entailed = bool(worlds) and all(w["q"] if mode == "ponens" else not w["p"] for w in worlds)
            expected = semantics == "material_implication"
            if entailed != expected:
                raise AssertionError((mode, semantics, worlds))
            logical.append({"mode": mode, "semantics": semantics,
                            "satisfying_assignments": len(worlds),
                            "initial_conclusion_remains_entailed": entailed})
    return {
        "asset_id": "A10", "scope": "isolated_parser_and_formal_truth_tables",
        "upstream_revision": UPSTREAM_COMMIT,
        "parser_git_blob_sha": observed,
        "observations": {"parser": probes, "logic": logical},
        "assertions_passed": len(probes) + len(logical),
        "findings": ["parser_accepts_out_of_range_z", "parser_can_accept_missing_marker",
                     "adding_a_sufficient_condition_does_not_retract_literal_entailment"],
        "target_model_runs": 0, "full_dataset_parsed": False,
        "upstream_full_runner_executed": False,
        "limitations": "These are engineering/semantics checks, not validation of all natural-language labels or LLM performance."
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream_parser", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.upstream_parser), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
