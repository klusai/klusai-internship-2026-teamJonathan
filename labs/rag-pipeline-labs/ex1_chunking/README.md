# Exercise 1 — Chunking strategies

**Topic:** splitting a document for retrieval — size-based windows, the overlap trick,
and structure-based (section) chunking — and measuring what each strategy preserves.

## Goal

Chunking is the first decision in a RAG pipeline and it caps everything downstream: if
a boundary slices through an answer, no retriever can find it whole. Implement
size-based chunking with overlap, then compare three strategies on the shared corpus
by counting how many of the 9 evaluation answers survive intact in some chunk.

## What's here

```
ex1_chunking/
  chunk.py        chunk_by_size (TODO: overlap) + chunk_by_section (reference) + the measurement
  ../corpus/      corpus.md (the shared report) and queries.json (the eval answers)
```

## Setup

```bash
python chunk.py     # no API key — pure text processing
```

## Tasks

1. **Implement `chunk_by_size`.** Slide a `size`-character window across the text,
   stepping `size - overlap` each time so neighbours share `overlap` characters.
   `overlap=0` must give non-overlapping windows; a positive overlap heals boundary
   cuts. Guard against `overlap >= size`.

2. **Run and record the three numbers.** `python chunk.py` prints "answers intact"
   for size/no-overlap, size/overlap, and section-based. Record all three and the
   chunk counts.

3. **Explain the trade-off.** Section-based keeps every answer intact but produces
   uneven, sometimes large chunks; size-based is uniform but cuts context. Write one
   or two sentences on when you'd pick each (hint: does your source have reliable
   structure?).

## Acceptance criteria

- [ ] `chunk_by_size` produces overlapping windows; `overlap=0` is non-overlapping;
      `overlap >= size` is handled (no infinite loop).
- [ ] All three "answers intact" numbers recorded; overlap ≥ no-overlap and
      section-based = 9/9.
- [ ] A written note on when to prefer size-based vs structure-based chunking.

## Stretch goals

- Add a `chunk_by_sentence` strategy (split on `. ` / newlines) and see where it lands
  between size-based and section-based.
- Report the duplication overhead of overlap: total characters across chunks with
  overlap vs without — that's the cost you pay to heal the cuts.
- Vary `SIZE` down to 80 and back up to 240; watch where the no-overlap intact rate
  dips and recovers.

## Self-check

- Why does a positive overlap raise the "answers intact" count?
- Section-based chunking scored 9/9 here — what property of *this* document made that
  easy, and when would it fail badly?
