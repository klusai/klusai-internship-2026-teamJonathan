# Exercise 5 — Prompt engineering

**Topic:** few-shot examples for ambiguous inputs, explicit review criteria, and
multi-pass architectures for large code reviews.

## Goal

Three short studies that each show a prompt technique moving the needle:
few-shot examples improve classification on ambiguous tickets; explicit criteria
make reviews consistent and complete; a split→review→synthesize pipeline improves
coverage on a long diff.

## What's here

```
ex5_prompt_engineering/
  tickets.json             20 tickets to classify (bug | feature | question); no labels here
  big_diff.txt             a long diff with 3 planted issues: SQL injection, bare except, MD5
  task1_fewshot.py         zero-shot classifier with an empty FEWSHOT slot to fill   (has TODO)
  task2_review_criteria.py vague vs. explicit-criteria review, 3 runs each           (has TODO)
  task3_multipass.py       split -> review -> synthesize pipeline + single-pass baseline (has TODO)
```

Gold labels for the tickets live in `../instructor/gold_labels.json` (tickets 8, 13,
and 19 are marked debatable). `task1_fewshot.py` reads them to score itself,
excluding the debatable ones.

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

## Tasks

1. **Few-shot lift (task1).** Run zero-shot first and record accuracy on the
   non-debatable tickets. Then fill the `FEWSHOT` slot with a few labeled examples
   (cover at least one bug, one feature, one question) and re-run. Did accuracy
   improve? Did the debatable tickets (8, 13, 19) flip?

2. **Explicit criteria (task2).** Complete the `CRITERIA` checklist so it names the
   exception-handling and password-hashing issues (not just SQL). Run vague ×3 and
   explicit ×3. Confirm the explicit prompt finds all three planted issues every
   run, and note how much the vague runs vary.

3. **Multi-pass (task3).** Implement `split_into_chunks` (per file) and the synthesis
   step. Compare single-pass vs. multi-pass: does multi-pass catch all three planted
   issues, and does it surface anything single-pass missed?

## Acceptance criteria

- [ ] task1: zero-shot and few-shot accuracies both recorded; few-shot ≥ zero-shot
      on the non-debatable set, with a note on the debatable tickets.
- [ ] task2: `CRITERIA` covers SQL injection, bare `except`/`except: pass`, and weak
      hashing; explicit runs find all three consistently; you noted vague-run variance.
- [ ] task3: chunk split + synthesis implemented; a written single-pass vs.
      multi-pass comparison (coverage, cost, latency).
- [ ] You can name all three planted issues in `big_diff.txt` and their file/line.

## Stretch goals

- Add a 4th, subtle issue to `big_diff.txt` and see which technique catches it.
- In task1, force structured output (an enum label) instead of parsing free text.
- In task3, run the chunk reviews concurrently and measure the latency change.

## Self-check

- Why are tickets 8, 13, and 19 ambiguous? What's the defensible label for each, and
  what extra info would disambiguate them?
- When is multi-pass *not* worth it? (small diffs, latency-sensitive paths)
