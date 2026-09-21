"""Reconcile A11 diagnostics against a pinned upstream README, offline.

Usage: python scripts/q01/check_faitheval_reconciliation.py UPSTREAM_README.md
No model, dataset or network is used. The old diagnostic remains unchanged.
Only hash-verified source is executed. The archive is evidence, never applied.
"""
from __future__ import annotations

import argparse
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import re
import string
import tempfile
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / "archives/a11_patch_5678684125fa"
PATCH_SHA256 = "5678684125fa97413c493d36c0adf57635eab7d773cc8eb2083777d9162f1f83"
README_BLOB = "78e5de53ae807484dc40f96fa2a146e4301f3826"
GIT_SCRIPT_BLOB = "978c9472c890ca2b8b6c914610270b9b67dbaa5f"
PACKAGE_SCRIPT_BLOB = "8c52ec0f5b135a6aea594940bdf7be97c45c73fe"
SCRIPT_PATH = "scripts/q01/check_faitheval_contract.py"
RESULT_PATH = "data/q01/A11_local_checks.json"


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def archived_files() -> dict[str, bytes]:
    raw = (ARCHIVE / "manifest.original.json").read_bytes()
    require(hashlib.sha256(raw).hexdigest() == "f271f3b59b449ccdc2c7ca8a2d59ff995c8b5230dde960efdce24b5b64bc63b2", "Archive manifest hash mismatch")
    manifest = json.loads(raw)
    result = {}
    require(len(manifest["files"]) == 6, "Expected six archived files")
    for item in manifest["files"]:
        path = ARCHIVE / "files" / item["path"]
        require(path.resolve().is_relative_to((ARCHIVE / "files").resolve()), "Unsafe archive path")
        data = path.read_bytes()
        require(len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item["sha256"]
                and blob_sha(data) == item["git_blob_sha"], f"Archived file mismatch: {item['path']}")
        result[item["path"]] = data
    return result


def checked_namespace(data: bytes, expected: str, name: str) -> dict[str, Any]:
    require(blob_sha(data) == expected, f"{name} source hash mismatch")
    env: dict[str, Any] = {"__name__": name}
    exec(compile(data, name, "exec"), env)
    return env


def upstream_matcher(data: bytes) -> Callable[[str, str, bool], bool]:
    require(blob_sha(data) == README_BLOB, "Upstream README hash mismatch")
    trees = [ast.parse(b) for b in re.findall(r"```python\n(.*?)\n```", data.decode(), re.S)]
    funcs = [n for t in trees for n in t.body
             if isinstance(n, ast.FunctionDef) and n.name == "normalize_answer"]
    require(len(funcs) == 1, "Expected one normalization function")
    env: dict[str, Any] = {"re": re, "string": string}
    exec(compile(ast.fix_missing_locations(ast.Module(body=funcs, type_ignores=[])), "pinned_normalizer", "exec"), env)
    sets: dict[str, dict[bool, list[str]]] = {}
    predicates = []
    for tree in trees:
        task = None
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "dataset_name" for t in node.targets):
                v = node.value
                name = "".join(x.value for x in v.values if isinstance(x, ast.Constant)) if isinstance(v, ast.JoinedStr) else ast.literal_eval(v)
                for candidate in ("unanswerable", "inconsistent"):
                    if f"FaithEval-{candidate}-" in name:
                        task = candidate
        if task:
            branches = [n for n in tree.body if isinstance(n, ast.If)]
            require(len(branches) == 1, "Unexpected phrase branches")
            sets[task] = {}
            for strict, nodes in ((False, branches[0].body), (True, branches[0].orelse)):
                values = [ast.literal_eval(n.value) for n in nodes if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == "valid_phrases" for t in n.targets)]
                require(len(values) == 1, "Unexpected phrase assignment")
                sets[task][strict] = values[0]
        predicates.extend(n.test for n in ast.walk(tree) if isinstance(n, ast.If)
                          and isinstance(n.test, ast.Call) and isinstance(n.test.func, ast.Name)
                          and n.test.func.id == "any")
    require(len(predicates) == 1 and len(sets) == 2, "Unexpected matching contract")
    code = compile(ast.fix_missing_locations(ast.Expression(body=predicates[0])), "pinned_predicate", "eval")

    def match(text: str, task: str, strict: bool = False) -> bool:
        if task not in sets:
            raise ValueError("Unsupported task")
        return bool(eval(code, dict(env, pred_answer=text, valid_phrases=sets[task][strict])))
    return match


def run(readme: Path) -> dict[str, Any]:
    raw = readme.read_bytes()
    upstream = upstream_matcher(raw)
    additions = archived_files()
    current = checked_namespace((ROOT / SCRIPT_PATH).read_bytes(), GIT_SCRIPT_BLOB, "git_diagnostic")
    supplied = checked_namespace(additions[SCRIPT_PATH], PACKAGE_SCRIPT_BLOB, "package_diagnostic")
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        current["main"]()
    git_result = json.loads(buf.getvalue())
    require(git_result == json.loads((ROOT / RESULT_PATH).read_text()), "Git diagnostic differs from saved result")
    package_result = supplied["run_audit"](readme)
    require(package_result == json.loads(additions[RESULT_PATH]), "Package diagnostic differs from saved result")
    rows = []
    inputs = [("git", r["id"], r["task"], r["response"], r["semantic_target_satisfied"], r["non_strict_accepts"], r["strict_accepts"]) for r in git_result["probes"]]
    inputs += [("package", r["id"], r["task"], r["response"], r["semantic_reference_for_probe"], r["upstream_accepts"]["non_strict"], r["upstream_accepts"]["strict"]) for r in package_result["observations"]]
    for source, pid, task, response, meaning, want_n, want_s in inputs:
        a = [upstream(response, task, strict) for strict in (False, True)]
        b = [current["readme_match"](response, task, strict) for strict in (False, True)]
        require(a == b == [want_n, want_s], f"Matcher disagreement: {source}:{pid}")
        rows.append({"id": f"{source}:{pid}", "task": task, "response": response,
                     "semantic_annotation": meaning, "non_strict": a[0], "strict": a[1]})
    negative = []
    def reject(label: str, action: Callable[[], Any]) -> None:
        try:
            action()
        except ValueError:
            negative.append(label)
        else:
            raise ValueError(f"Negative control accepted: {label}")
    reject("modified_readme", lambda: upstream_matcher(raw + b"\n"))
    reject("modified_package_checker", lambda: checked_namespace(additions[SCRIPT_PATH] + b"\n", PACKAGE_SCRIPT_BLOB, "bad_package"))
    reject("modified_git_checker", lambda: checked_namespace((ROOT / SCRIPT_PATH).read_bytes() + b"\n", GIT_SCRIPT_BLOB, "bad"))
    reject("unsupported_task", lambda: upstream("unknown", "counterfactual"))
    with tempfile.TemporaryDirectory() as tmp:
        bad = Path(tmp) / "README.md"; bad.write_bytes(raw + b"\n")
        reject("package_rejects_modified_readme", lambda: supplied["run_audit"](bad))
    return {
        "asset_id": "A11", "scope": "artifact_reconciliation_not_benchmark",
        "source_commit": "f7e5c3b7337059f587e9d54cb4e1d0f09c65d450",
        "upstream_readme_blob": README_BLOB, "upstream_readme_bytes": len(raw),
        "patch_sha256": PATCH_SHA256,
        "original_reports_reproduced": {"git": 12, "package": 12},
        "namespaced_probe_entries": len(rows),
        "unique_task_response_pairs": len({(r["task"], r["response"]) for r in rows}),
        "matcher_mode_comparisons": 2 * len(rows), "matcher_disagreements": 0,
        "negative_controls_rejected": negative,
        "target_model_runs": 0, "accepted_full_cases": 0, "accepted_short_cases": 0,
        "caveat": "Probe annotations are author-defined, not independent human labels. Overlapping input entries and two modes are not independent benchmark trials. No universal equivalence, dataset accuracy, or historical actor is inferred.",
        "probes": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("readme", type=Path)
    args = parser.parse_args()
    try:
        report = run(args.readme)
    except (OSError, ValueError, SyntaxError, AssertionError) as exc:
        parser.exit(1, f"A11 reconciliation failed: {exc}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
