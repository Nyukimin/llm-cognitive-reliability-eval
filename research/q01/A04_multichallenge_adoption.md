# Q01 Asset Inspection: A04 MultiChallenge

Status: **case-source candidate accepted; benchmark-as-a-whole not adopted yet**  
Inspection date: 2026-09-21  
Stage: Q01 existing-asset case inspection

## 1. Decision

Use the **current ScaleAI MultiChallenge dataset as the preferred source for case inspection**, not the older 273-row GitHub snapshot as the default source.

The current Scale-hosted dataset has 266 examples and is marked CC BY 4.0. Scale's 2026 update states that approximately 54 tasks were revised to reduce ambiguity and that the judge was changed to Gemini 2.5 Pro. The public leaderboard points to this Hugging Face dataset as the open-source dataset.

The older official GitHub repository remains useful as a historical implementation reference, but it is not treated as the current benchmark definition:
- pinned repository commit: `5ccefcca6a39020d66c1383c4e6a809cb07afa33`
- that snapshot contains 273 rows
- its evaluator hard-codes `gpt-4o-2024-08-06`
- no LICENSE file is present in the repository tree at the pinned commit
- its dataset/rubric content is not identical to the current Scale-hosted 266-row dataset

Therefore:
1. inspect/select cases from the current Scale dataset;
2. keep the old GitHub implementation only as historical evidence about format and old scoring behavior;
3. do not report results from a derived subset or translated version as an official MultiChallenge score;
4. do not import any case into Full until the specific case, rubric, attribution, execution mode, and scorer have passed our acceptance gate.

## 2. Pinned sources

### Current dataset source

- Provider: ScaleAI
- Dataset: `ScaleAI/MultiChallenge`
- Data-file revision: `9d9e0fd9ef535fb71df41740b2e9e6bdb0aa7ac3`
- Current metadata head observed during inspection: `670fd81f270314d0f8f82b34fcfe2187fd28f699`
- Rows: 266
- Language: English
- License metadata: CC BY 4.0
- Axes:
  - INFERENCE_MEMORY
  - INSTRUCTION_RETENTION
  - SELF_COHERENCE
  - RELIABLE_VERSION_EDITING

The data file itself was introduced at 9d9e0fd and subsequent observed commits changed the dataset card/metadata rather than the parquet file.

### Historical official GitHub implementation

- Repository: `ekwinox117/multi-challenge`
- Pinned commit: `5ccefcca6a39020d66c1383c4e6a809cb07afa33`
- Rows in `data/benchmark_questions.jsonl`: 273
- Axis counts at that commit:
  - INFERENCE_MEMORY: 113
  - INSTRUCTION_RETENTION: 69
  - SELF_COHERENCE: 50
  - RELIABLE_VERSION_EDITING: 41
- Conversation message count: min 3, max 19, mean about 9.12
- `PASS_CRITERIA`: YES for all 273 rows
- Historical judge implementation: GPT-4o 2024-08-06, temperature 0, instance-specific yes/no rubric

This 273-row snapshot is **not** the case source selected for the project baseline.

## 3. Why the version distinction matters

Scale's 2026 update says:
- about 54 tasks were revised to tighten rubrics or remove ambiguity;
- the judge was changed to Gemini 2.5 Pro;
- the purpose was to make the benchmark less sensitive to subjective interpretation.

The current 266-row Scale dataset and the historical 273-row GitHub snapshot are therefore not interchangeable. At least one shared question ID has a different rubric wording between the old snapshot and the current Scale dataset.

A future result must record which dataset revision and scorer definition it uses. A score over the old 273 rows must not be compared as if it were the same evaluation as a score over the current 266 rows.

## 4. What MultiChallenge directly measures

Scale describes four capabilities:

1. **Instruction retention**: following an instruction stated in the first user turn throughout the conversation.
2. **Inference memory**: recalling and connecting relevant details from previous user turns when needed for the final response.
3. **Reliable versioned editing**: revising an evolving artifact through back-and-forth edits.
4. **Self-coherence**: staying reasonably consistent with prior model responses and avoiding unconditional agreement with the user.

Its scoring design uses an instance-level binary rubric. The rubric is intended to judge only the final candidate response, rather than re-reason over the full history.

## 5. Mapping to our behavior definitions

| Our behavior | MultiChallenge relation | Q01 disposition |
| --- | --- | --- |
| B01 Goal/effective-requirement retention | **Direct for a narrow subtype.** INSTRUCTION_RETENTION directly tests persistence of explicit earlier constraints. It does not by itself establish higher-level goal retention under problem reframing. | Candidate cases accepted for case-level inspection. |
| B05 Unfounded sycophancy | **Direct for selected SELF_COHERENCE cases only.** Scale explicitly includes avoiding unconditional agreement under self-coherence, but not every SELF_COHERENCE case is a sycophancy test. | Case-level filtering required. |
| B10 Use of available information | **Direct for fixed-record use of prior user information.** INFERENCE_MEMORY is useful for R-lane history use. It does not prove cross-session retrieval or hidden Memory retrieval. | Candidate cases accepted for R-lane inspection. |
| B11 Self-correction / dependent repair / regression | **Partial.** RELIABLE_VERSION_EDITING directly tests preserving and changing artifact requirements across revisions. It does not directly test detecting one's own error, repairing all dependent conclusions, or avoiding unrelated regression after self-correction. | Use only the requirement-preservation/editing part unless a specific case proves more. |
| B06 Historical fidelity of prior beliefs/rankings | **Not directly covered by the asset as currently verified.** SELF_COHERENCE and INFERENCE_MEMORY test consistency/recall, but that is not the same as reporting a former model belief or ranking correctly after the current conclusion changes. | Remains a priority gap; do not count MultiChallenge as filling B06. |
| B02/B03/B07 | No direct coverage established in this inspection. | Do not count as covered. |

## 6. Representative current-dataset records to inspect next

These IDs are visible in the current Scale-hosted dataset and illustrate the relevant axes. They are **case-inspection candidates, not yet accepted Full cases**.

- `674552683acc22154b07a598` — INFERENCE_MEMORY
- `67455268bc2ba9e69b8618f8` — INSTRUCTION_RETENTION
- `674552684d7f0f0dad442da6` — SELF_COHERENCE
- `67455bc84f79e78f4a63c837` — RELIABLE_VERSION_EDITING

For each selected case we still need to check:
- the complete conversation and final rubric;
- whether the reference fact/constraint is unambiguous;
- whether legitimate alternative responses can satisfy the task;
- whether the case maps to our B definition without changing the measured construct;
- whether English can be used directly for cross-model testing;
- whether a Japanese adaptation is necessary and, if so, whether it is separately accepted as a derived Full case.

## 7. Scoring decision

Do **not** copy the old GitHub evaluator as the current official scorer.

The historical repository's evaluator:
- uses GPT-4o 2024-08-06;
- judges an instance-specific binary question against the final response;
- treats a multi-attempt case as passed if any attempt passes.

The current Scale benchmark instead reports a Gemini 2.5 Pro judge after the 2026 update. The exact current production prompt/configuration has not been reproduced by this inspection.

For our project:
- preserve each selected case's binary rubric as source evidence;
- implement our own versioned scorer only after Q04/Q06 validation;
- default benchmark runs should report per-attempt results rather than silently adopting the historical “any attempt passes” aggregation;
- if we reproduce a Scale leaderboard-compatible score later, that is a separate compatibility task and must pin the exact dataset/scorer configuration.

## 8. Redistribution and adaptation

The current ScaleAI dataset card marks the dataset **CC BY 4.0**. Under that license, sharing and adaptation are allowed with attribution, a license link, and an indication of changes.

Accordingly, current-dataset cases are eligible in principle for public Full/Short use, including translated/adapted derivatives, **provided**:
- attribution is preserved;
- the license is linked;
- modifications such as translation or shortened context are clearly marked;
- the derived case is accepted as its own case/version under this project's rules.

This is not a blanket statement that every linked third-party element has been separately cleared. Case-level acceptance still records provenance and any external material needed by the case.

## 9. Public-Short feasibility

Preliminary result: **promising, not yet confirmed per case.**

Reasons:
- current Scale dataset is publicly accessible;
- explicit CC BY 4.0 metadata is present;
- cases are text-only and have a binary final-response rubric;
- current rows have 3–19 conversation messages.

Open issues:
- full case-level ambiguity review is still required;
- translated Japanese cases are derived cases and need separate acceptance;
- current official judge implementation is not yet reproduced;
- a Short subset must still be selected from accepted Full cases, not directly from this asset during Q01.

## 10. Q01 outcome

`A04 MultiChallenge`:
- asset status: **accepted as a source for case inspection**
- preferred source: **current ScaleAI 266-row dataset**
- historical GitHub source: **reference only**
- whole benchmark imported into Full: **no**
- accepted Full cases: **0**
- accepted Short cases: **0**
- direct gap closed for B06: **no**
- next action for A04: inspect the four representative current records above and classify each as direct / derived / reject / hold

## 11. Sources checked

- Scale Labs MultiChallenge leaderboard and methodology
- Scale Labs 2026 MultiChallenge update
- ScaleAI/MultiChallenge Hugging Face dataset and commit history
- ACL 2025 MultiChallenge paper record
- ekwinox117/multi-challenge GitHub repository at pinned commit
- Creative Commons Attribution 4.0 deed

This record states only what was checked in this Q01 pass. It does not claim to have reproduced the benchmark or verified model scores.
