# Q01 Asset Inspection: A06 LongMemEval

Status: **case-source candidate accepted with label-audit requirement; whole benchmark not adopted into Full**  
Inspection date: 2026-09-21  
Stage: Q01 existing-asset case inspection

## 1. Decision

Use **`xiaowu0162/longmemeval-cleaned`** as the preferred LongMemEval v1 source for case inspection.

Do not use the deprecated original Hugging Face dataset as the current source. Do not treat LongMemEval-V2 as a drop-in replacement; V2 is a separate agent-memory benchmark and remains A07.

LongMemEval is useful for four parts of this project:
- B04 evidence-sensitive updating, especially `knowledge-update`
- B08 answerability / abstention, through `*_abs`
- B10 use of available historical information
- a **narrow subtype of B06** through `single-session-assistant`, which can test recall of information previously stated by the assistant

However, LongMemEval does **not** directly close the central B06 gap that motivated this project: after the model's current conclusion changes, accurately reporting its own earlier belief, ranking, or stated rationale. Its official knowledge-update scorer explicitly permits mentioning older information as long as the current updated answer is present. That makes it a current-state update test, not a historical-fidelity test.

A second constraint is label quality. The cleaned release is the official current v1 data, but public issues in the official repository document multiple apparent annotation / timestamp / gold-answer errors in the cleaned data. Therefore, **no LongMemEval case enters Full solely because it is present in the official 500-question dataset**. Selected cases must pass our case-level evidence and label audit first.

## 2. Pinned sources

### Current cleaned v1 dataset

- Provider: `xiaowu0162`
- Dataset: `longmemeval-cleaned`
- Hugging Face revision: `98d7416c24c778c2fee6e6f3006e7a073259d48f`
- Dataset language: English
- Dataset license metadata: MIT
- Questions: 500 per split
- Files:
  - `longmemeval_oracle.json`
    - SHA256: `821a2034d219ab45846873dd14c14f12cfe7776e73527a483f9dac095d38620c`
    - evidence sessions only
  - `longmemeval_s_cleaned.json`
    - SHA256: `d6f21ea9d60a0d56f34a05b609c79c88a451d2ae03597821ea3d5a9678c3a442`
    - roughly 115k-token history target in the original design
  - `longmemeval_m_cleaned.json`
    - SHA256: `9d79e5524794a2e6900a3aa9cb7d9152c5a3e8319c9a87c25494ba1eacee495f`
    - roughly 500 history sessions per question

The cleaned dataset replaces the original v1 release and removes noisy history sessions that interfered with answer correctness.

### Official code repository

- Repository: `xiaowu0162/LongMemEval`
- Inspected repository head: `9e0b455f4ef0e2ab8f2e582289761153549043fc`
- Repository license: MIT
- Official evaluation code inspected:
  - `src/evaluation/evaluate_qa.py`
  - `src/evaluation/print_qa_metrics.py`

### Paper

- LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory
- arXiv:2410.10813
- ICLR 2025
- last paper revision observed: v2, 2025-03-04

## 3. Official task structure

The official README defines 500 questions across these question types:

- `single-session-user`
- `single-session-assistant`
- `single-session-preference`
- `temporal-reasoning`
- `knowledge-update`
- `multi-session`

Questions whose IDs end with `_abs` are abstention questions.

The paper describes five core abilities:
- information extraction
- multi-session reasoning
- knowledge updates
- temporal reasoning
- abstention

Each record contains the question, expected answer, question date, session IDs, session timestamps, actual user/assistant history, evidence-turn markers, and answer-session IDs.

## 4. Official scoring behavior that matters for this project

The official QA evaluator uses a judge model and task-specific prompts.

At the inspected code revision:
- default official metric model alias `gpt-4o` maps to `gpt-4o-2024-08-06`
- temperature: 0
- output is judged yes/no
- `single-session-user`, `single-session-assistant`, and `multi-session` require the response to contain the correct answer
- `temporal-reasoning` explicitly tolerates off-by-one errors in time-unit counts
- `knowledge-update` explicitly says that a response may include prior information and still be correct **as long as the updated answer is the required answer**
- `single-session-preference` uses a rubric and does not require every rubric point
- abstention asks whether the response correctly identifies the question as unanswerable

This scoring contract is important: a `knowledge-update` success is evidence that the model can produce the current answer under the provided history. It is **not** evidence that the model can accurately reconstruct what it believed or said earlier.

## 5. Mapping to our behavior definitions

| Our behavior | LongMemEval relation | Q01 disposition |
| --- | --- | --- |
| B04 Evidence-sensitive revision | **Direct, narrow.** `knowledge-update` directly tests choosing the updated current answer from older/newer information. | Candidate cases accepted for case-level inspection. |
| B08 Evidence / abstention calibration | **Direct, narrow.** `*_abs` cases test recognizing that the available history does not contain the requested answer. | Candidate cases accepted, but label evidence must be rechecked. |
| B10 Use of available information | **Direct under fixed/history-provided conditions.** All main types require using historical information; the benchmark also exposes retrieval evaluation. | Candidate for R-lane and memory-system evaluation. Does not by itself prove native product Memory retrieval. |
| B06 Historical fidelity | **Partial only.** `single-session-assistant` can test remembering information previously said by an assistant. This is useful for speaker-grounded past-statement recall. It does not directly test an updated model accurately reporting its own former belief/ranking/rationale. | Keep B06 central gap open. Inspect assistant-side cases only as a narrow subtype. |
| B02 Problem framing | No direct coverage established. | Do not count as covered. |
| B03 Search / stopping | No direct coverage established. | Do not count as covered. |
| B07 Retrospective rationale | No direct coverage established. | Do not count as covered. |
| B11 Self-correction with dependent repair | No direct coverage established from v1 task definitions. | Do not count as covered. |

## 6. Oracle, S, and M must not be treated as equivalent tests

### Oracle

Only evidence sessions are provided.

Use:
- reader / reasoning ceiling
- case-label inspection
- cheap initial pilot of answer scoring

Do not interpret oracle success as evidence that a system retrieved the correct memory from a large history.

### S

Long history, roughly 115k tokens in the benchmark design.

Use:
- long-context/history use
- retrieval + reading when the full system is tested

For a public manual Web test, S may be impractical or unsupported depending on the product/context limit. It must not be silently shortened and still called the same official case.

### M

Roughly 500 sessions per question and too long for the original long-context baseline.

Use:
- memory retrieval systems / large-scale memory pipelines

It is not a realistic common manual Web path for the public Short unless a separately accepted derived case is created.

## 7. Label-quality audit requirement

The cleaned dataset is the correct upstream source to start from, but its labels are not assumed infallible.

Open issues in the official LongMemEval repository include examples such as:
- #19 / #26 / #41: `370a8ff4`, temporal gold answer reported as 15 weeks while the cited session dates yield 81 days (~11.6 weeks)
- #37: `eac54add`, reported ground-truth evidence-session mapping error
- #39: `37f165cf`, reported timestamps inconsistent with the question's January/March wording
- #21: `dd2973ad`, reported cross-session date mismatch

These are issue reports, not a maintainer-certified corrected release. They are sufficient to show that **case-level label verification is necessary before Full adoption**, not sufficient to declare the entire benchmark invalid.

For every selected LongMemEval case:
1. recompute or re-read the expected answer from the pinned evidence;
2. verify the relevant timestamps and speaker;
3. verify the evidence session IDs;
4. verify the intended answerability condition;
5. record known upstream issues affecting the case;
6. reject or hold the case if the reference answer cannot be independently supported.

Temporal and multi-session cases receive explicit arithmetic/timeline verification. Knowledge-update cases receive explicit ordering/supersession verification.

## 8. Redistribution and adaptation

The official GitHub repository contains an MIT license, and the current cleaned Hugging Face dataset declares MIT.

This makes the asset eligible in principle for public case reuse and derived cases under the stated license, subject to:
- preserving required MIT notices where applicable;
- keeping source attribution/provenance;
- recording modifications such as translation, shortening, or history transformation;
- re-accepting a modified case as its own case/version under this project.

A transformed oracle case, translated case, or shortened S case is not reported as an unmodified official LongMemEval result.

## 9. Public-Short feasibility

Preliminary result: **useful for selected R-lane cases, not suitable as a whole public Short without derivation.**

Promising:
- text-based;
- MIT metadata;
- answer and evidence structure is explicit;
- oracle cases can isolate reading/reasoning from retrieval.

Constraints:
- S/M histories are too large for a universal manual Web path;
- product-native cross-session Memory is not the same as injecting LongMemEval history;
- selected gold labels need independent verification;
- Japanese translation creates derived cases;
- official scoring currently depends on an older GPT-4o judge contract and must be separately validated for this project.

## 10. Q01 outcome

`A06 LongMemEval`:
- asset status: **accepted as a source for case inspection**
- preferred v1 data: **longmemeval-cleaned @ 98d7416c24c778c2fee6e6f3006e7a073259d48f**
- deprecated original v1 dataset: **do not use for new case selection**
- LongMemEval-V2: **separate asset A07**
- whole 500-question benchmark imported into Full: **no**
- accepted Full cases: **0**
- accepted Short cases: **0**
- B04 direct candidate: **yes, knowledge-update**
- B08 direct candidate: **yes, abstention**
- B10 direct candidate: **yes, fixed/history-provided conditions**
- B06 central gap closed: **no**
- label audit required before any case adoption: **yes**

## 11. Next action for A06

Before any LongMemEval case enters Full:
- inspect a small representative set from `knowledge-update`, `single-session-assistant`, `*_abs`, and `temporal-reasoning`;
- recompute their labels from source evidence;
- mark each as direct / derived / reject / hold;
- use oracle first to validate our scorer semantics, then decide whether S or M is needed for the intended measurement.

This Q01 pass does not reproduce LongMemEval scores and does not run a target LLM.

## 12. Sources checked

Primary / upstream:
- <https://github.com/xiaowu0162/LongMemEval>
- <https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned>
- <https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/commit/98d7416c24c778c2fee6e6f3006e7a073259d48f>
- <https://arxiv.org/abs/2410.10813>

Upstream issue reports used only as label-risk evidence:
- <https://github.com/xiaowu0162/LongMemEval/issues/19>
- <https://github.com/xiaowu0162/LongMemEval/issues/21>
- <https://github.com/xiaowu0162/LongMemEval/issues/26>
- <https://github.com/xiaowu0162/LongMemEval/issues/37>
- <https://github.com/xiaowu0162/LongMemEval/issues/39>
- <https://github.com/xiaowu0162/LongMemEval/issues/41>
