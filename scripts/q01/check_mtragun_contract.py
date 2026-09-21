"""Offline A17 prompt-projection probes, not model or benchmark scores.

Usage: python scripts/q01/check_mtragun_contract.py UPSTREAM_UNDERSPECIFIED_EVAL_PY
Requires jinja2. Loads only the pinned prompt constant and formatting function
through AST; never imports upstream judge clients. No network or credentials.
"""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
from pathlib import Path
import jinja2
from jinja2 import Template, meta

UPSTREAM_COMMIT = "2c618bb98db3c8526433e22d8a2f7320f10a7470"
EXPECTED_BLOB = "bb5975cfbaf2b3bfabe4028fdc009ac38ebe256d"


def load_formatter(raw: bytes):
    blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    if blob != EXPECTED_BLOB:
        raise ValueError("Upstream source differs from the inspected Git blob")
    tree = ast.parse(raw.decode("utf-8"))
    nodes = [n for n in tree.body if
             isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and
             t.id == "UNDERSPECIFIED_PROMPT" for t in n.targets) or
             isinstance(n, ast.FunctionDef) and n.name == "format_underspecified_judge"]
    if len(nodes) != 2:
        raise ValueError("Expected exactly the prompt constant and formatter")
    namespace = {"Template": Template}
    module = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(module, "pinned_A17_formatter", "exec"), namespace)
    return namespace["UNDERSPECIFIED_PROMPT"], namespace["format_underspecified_judge"]


class Rows:
    """Minimal iterrows interface for this isolated upstream function."""
    def __init__(self, rows):
        self.rows = rows

    def iterrows(self):
        return iter(enumerate(self.rows))


def inspect(raw: bytes) -> dict:
    template, formatter = load_formatter(raw)
    variables = sorted(meta.find_undeclared_variables(jinja2.Environment().parse(template)))
    if variables != ["response"]:
        raise AssertionError("Reinspect changed judge-input contract")
    pairs = [
        ("P01", "A_PLAN: How much does it cost? Two plans are in context.",
         "B_PLAN: Give the price of Plan Blue only. Its price is provided.",
         "Which plan are you asking about?"),
        ("P02", "A_CITY: Find the schedule for my city. No city is specified.",
         "B_CITY: The city is Sampletown. Give its supplied schedule.",
         "Please specify the city."),
        ("P03", "A_REF: What does that mean? Two prior terms are plausible.",
         "B_REF: Explain the term latency, not throughput, from the supplied glossary.",
         "Which term would you like explained?"),
    ]
    results = []
    for pid, a, b, response in pairs:
        prompts = formatter(Rows([
            {"inquiry": a, "response": response, "document": ["DOC_A"]},
            {"inquiry": b, "response": response, "document": ["DOC_B"]},
        ]))
        equal = prompts[0] == prompts[1]
        absent = all(x not in prompts[0] for x in (a, b, "DOC_A", "DOC_B"))
        if not equal or not absent:
            raise AssertionError(f"Projection observation changed: {pid}")
        results.append({"id": pid, "same_response_different_inquiry_and_documents": True,
                        "judge_prompts_identical": equal, "inquiry_and_document_omitted": absent,
                        "prompt_sha256": hashlib.sha256(prompts[0].encode()).hexdigest()})
    changed = formatter(Rows([{"inquiry": "same", "response": "Please name the plan."},
                              {"inquiry": "same", "response": "The price is eight units."}]))
    if changed[0] == changed[1]:
        raise AssertionError("Response changes must reach the judge input")
    altered_rejected = False
    try:
        load_formatter(raw + b"\n")
    except ValueError:
        altered_rejected = True
    missing_rejected = False
    try:
        formatter(Rows([{"inquiry": "present"}]))
    except KeyError:
        missing_rejected = True
    if not altered_rejected or not missing_rejected:
        raise AssertionError("Negative controls did not reject invalid inputs")
    return {
        "asset_id": "A17", "scope": "offline_pinned_formatter_projection",
        "upstream_revision": UPSTREAM_COMMIT, "source_git_blob": EXPECTED_BLOB,
        "source_bytes": len(raw), "jinja2_version": jinja2.__version__,
        "execution_method": "isolated_upstream_AST_constant_and_function",
        "template_variables": variables, "synthetic_pairs": results,
        "response_change_reaches_prompt": True,
        "modified_source_rejected": altered_rejected,
        "missing_response_rejected": missing_rejected,
        "target_model_runs": 0, "judge_model_runs": 0, "dataset_records_executed": 0,
        "accepted_full_cases": 0, "accepted_short_cases": 0,
        "limitations": ["No empirical judge accuracy or error frequency measured.",
                         "Synthetic semantic contrasts are design examples, not human-validated labels.",
                         "Identical prompts prove missing distinguishing inputs, not the judge verdict.",
                         "No complete upstream pipeline or published scores reproduced."],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("upstream_file", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.upstream_file.read_bytes()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
