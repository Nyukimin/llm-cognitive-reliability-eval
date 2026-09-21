# llm-cognitive-reliability-eval

A cross-model evaluation project for **cognitive reliability in long-horizon, multi-turn LLM interactions**.

The project started from two observed failure patterns:

- retrospective distortion of prior statements, beliefs, or decision history
- fixation on a local solution without returning to the higher-level objective or problem definition

The evaluation scope is intentionally broader than those two examples. It covers reliability of goal retention, problem framing, evidence-sensitive revision, historical fidelity, provenance of claims, self-correction, completion integrity, ambiguity handling, and related failure modes.

## Current baseline

- Requirements: `v0.5`
- Stage 1 design: `v0.3`
- Status: case inspection and pilot implementation
- Formal Full / Short benchmark: not yet adopted
- Target-model performance tests: not yet run

## Current asset inspection

See the [Q01 inspection index](research/q01/README.md) for the current source/protocol decisions and pending case-acceptance work. Asset review completion is not completion of every case audit. A10 Belief-R is conditionally retained as an update/maintain protocol reference; original cases require semantic and label checks before adoption. A11 FaithEval is next.

## Repository structure

- `docs/requirements/` — baseline requirements
- `docs/design/` — evaluation scope and Stage 1 design
- `docs/reviews/` — review disposition and integration records
- `docs/pilot/` — pilot execution contracts
- `research/` — existing evaluation assets and source mapping
- `data/` — machine-readable registries and contracts
- `scripts/` — validation utilities
- `evals/` — future benchmark cases, scorers, and configs

## Important distinction

This repository evaluates **observable behavior and evidence**. It does not infer hidden chain-of-thought or internal causes from fluent explanations alone.

The Full benchmark is designed first; any public Short test must be a documented subset of the Full benchmark.

## Public-repository note

Raw personal conversation logs and unpublished private evidence are not part of this public repository. Public benchmark cases must be anonymized, self-contained, and reviewable from the evidence included with the case.

## License

No license has been selected yet.
