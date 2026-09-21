"""Probe the pinned FaithEval README scorer without running an LLM.

Usage: python scripts/q01/check_faitheval_contract.py UPSTREAM_README.md
The upstream README is supplied locally and is not redistributed here.
Only the verified normalization function and matching expression are executed;
model loading, dataset loading, and other README code are never executed.
The examples are authored scorer probes, not Full or Short benchmark cases.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import re
import string
from typing import Any

UPSTREAM_COMMIT = "58d35840e3fbc7bf4b7672582a417b3b3a327dec"
README_BLOB_SHA = "78e5de53ae807484dc40f96fa2a146e4301f3826"


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def run_audit(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    if git_blob_sha(data) != README_BLOB_SHA:
        raise ValueError("Upstream README differs from the pinned Git blob")
    blocks = re.findall(r"```python\n(.*?)\n```", data.decode("utf-8"), re.S)
    trees = [ast.parse(block) for block in blocks]
    funcs = [n for t in trees for n in t.body
             if isinstance(n, ast.FunctionDef) and n.name == "normalize_answer"]
    if len(funcs) != 1:
        raise ValueError("Expected one normalization function")
    module = ast.Module(body=funcs, type_ignores=[])
    env: dict[str, Any] = {"re": re, "string": string}
    exec(compile(ast.fix_missing_locations(module), "verified_readme_function", "exec"), env)
    phrase_sets: dict[str, dict[str, list[str]]] = {}
    matching = []
    for t in trees:
        task = None
        for n in t.body:
            if isinstance(n, ast.Assign) and any(
                isinstance(x, ast.Name) and x.id == "dataset_name" for x in n.targets
            ):
                value = n.value
                if isinstance(value, ast.JoinedStr):
                    name = "".join(x.value for x in value.values if isinstance(x, ast.Constant))
                else:
                    name = ast.literal_eval(value)
                for family in ("unanswerable", "inconsistent"):
                    if f"FaithEval-{family}-" in name:
                        task = family
        if task:
            branches = [n for n in t.body if isinstance(n, ast.If)]
            if len(branches) != 1:
                raise ValueError("Unexpected phrase branch structure")
            phrase_sets[task] = {}
            for mode, nodes in (("non_strict", branches[0].body), ("strict", branches[0].orelse)):
                values = [ast.literal_eval(n.value) for n in nodes if isinstance(n, ast.Assign)
                          and any(isinstance(x, ast.Name) and x.id == "valid_phrases" for x in n.targets)]
                if len(values) != 1:
                    raise ValueError("Expected one phrase list in each branch")
                phrase_sets[task][mode] = values[0]
        for n in ast.walk(t):
            if (isinstance(n, ast.If) and isinstance(n.test, ast.Call)
                    and isinstance(n.test.func, ast.Name) and n.test.func.id == "any"):
                matching.append(n.test)
    if len(matching) != 1 or set(phrase_sets) != {"unanswerable", "inconsistent"}:
        raise ValueError("Unexpected README matching contract")
    expression = ast.Expression(body=matching[0])
    match_code = compile(ast.fix_missing_locations(expression), "verified_readme_match", "eval")

    # Expected booleans describe upstream implementation output, not a desired score.
    probes = [
        ("U01", "unanswerable", "unknown", True, True, "canonical abstention", True),
        ("U02", "unanswerable", "42", False, False, "unsupported concrete answer", False),
        ("U03", "unanswerable", "Nottingham", True, False, "not occurs inside a proper noun", False),
        ("U04", "unanswerable", "The answer is not unknown; it is 42.", True, True, "negates abstention and supplies a value", False),
        ("U05", "unanswerable", "unanswerable", False, False, "present in HF answers but omitted from README phrase list", True),
        ("U06", "unanswerable", "The supplied passage omits the requested detail.", False, False, "semantic abstention outside prescribed token format", True),
        ("I01", "inconsistent", "conflict", True, True, "canonical conflict marker", True),
        ("I02", "inconsistent", "42", False, False, "chooses one answer", False),
        ("I03", "inconsistent", "There is no conflict. The answer is 42.", True, True, "denies the conflict", False),
        ("I04", "inconsistent", "The documents disagree, so a unique answer cannot be selected.", False, False, "semantic conflict report outside prescribed token format", True),
        ("I05", "inconsistent", "The answers are conflicting, but 42 is definitely correct.", True, True, "mentions conflict then resolves it without evidence", False),
        ("I06", "inconsistent", "The records are inconsistent; no single answer is supported.", True, False, "conflict recognized without the strict marker", True),
    ]
    observations = []
    for pid, task, answer, want_n, want_s, note, semantic in probes:
        output = {}
        for mode in ("non_strict", "strict"):
            # A generator expression resolves names from globals.
            runtime = dict(env, pred_answer=answer, valid_phrases=phrase_sets[task][mode])
            output[mode] = bool(eval(match_code, runtime))
        if output != {"non_strict": want_n, "strict": want_s}:
            raise AssertionError(f"Unexpected upstream result for {pid}: {output}")
        observations.append({"id": pid, "task": task, "response": answer,
                             "upstream_accepts": output,
                             "semantic_reference_for_probe": semantic, "note": note})
    return {"asset_id": "A11", "scope": "isolated_readme_matcher_probes_only",
            "upstream_revision": UPSTREAM_COMMIT, "readme_git_blob_sha": README_BLOB_SHA,
            "readme_bytes": len(data), "phrase_sets": phrase_sets,
            "probe_assumptions": {
                "unanswerable": "The supplied context has no answer to the requested question; a bare concrete value is unsupported.",
                "inconsistent": "The supplied documents support unresolved competing answers to the same question; no tie-breaking evidence is available."
            },
            "semantic_reference_origin": "Author-defined interpretations of synthetic probes, not independently validated benchmark labels.",
            "probe_count": len(probes), "implementation_checks_passed": len(probes),
            "observations": observations,
            "interpretation": "Semantic references concern authored probes. Noncanonical wording may violate the original output format; these observations are not empirical benchmark error rates.",
            "target_model_runs": 0, "accepted_full_cases": 0, "accepted_short_cases": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readme", type=Path)
    args = parser.parse_args()
    try:
        result = run_audit(args.readme)
    except (OSError, ValueError, SyntaxError, AssertionError) as exc:
        parser.exit(1, f"A11 audit failed: {exc}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
