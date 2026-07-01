# Single-pass vs. multi-pass review — task 3

Reviewing `big_diff.txt` (5 files, ~150 diff lines) two ways with
`claude-opus-4-8`:

- **Single-pass** — the whole diff in one prompt, `max_tokens=1500`.
- **Multi-pass** — `split_into_chunks` splits on `diff --git` into one chunk
  per file (**5 chunks**), each reviewed independently (`max_tokens=800`), then
  the 5 reviews are merged/deduped/ranked in a synthesis call (`max_tokens=2000`).

## The three planted issues (and where they actually live)

Each planted issue type recurs in a second file — that duplication is the whole
point of the long-diff exercise.

| Planted issue | File / line | Single-pass | Multi-pass |
| --- | --- | :---: | :---: |
| SQL injection (string concat) | `api/auth.py:26` (`verify_login`) | ✅ | ✅ |
| SQL injection (column **and** value) | `api/orders.py:62–64` (`search_orders`) | ✅ | ✅ |
| Bare `except: pass` | `api/orders.py:74–75` (`cancel_order`) | ✅ | ✅ |
| Bare `except: pass` | `api/utils.py:103–104` (`parse_int`) | ✅ | ✅ |
| Unsalted MD5 password hash | `api/auth.py:18` (`hash_password`) | ✅ | ✅ |
| MD5 key fingerprint | `api/utils.py:110` (`api_key_fingerprint`) | ✅ | ✅ |

Both passes caught all three planted issue **types**, in **both** files each
appears in. On pure planted-issue coverage it's a tie.

## Coverage — where multi-pass pulled ahead

The difference shows up on everything *past* the first two files:

- **`web/dashboard.js` was reviewed only by multi-pass.** It flagged a listener
  leak (the `#refresh` `addEventListener` is re-bound on every `renderDashboard`
  call → one click fires N fetches), a missing null guard on
  `getElementById("refresh")`, and an unchecked `fetch` response. The
  single-pass output **never reached `dashboard.js`** — it hit its 1500-token
  cap partway through the `api/` issues (cut off mid-item at an "Unboun…"
  finding about `total_for_customer`) and stopped.
- Multi-pass also surfaced **unverified token expiry** in `auth.py` that the
  single-pass list didn't include.

Both independently found bugs *beyond* the planted three — predictable/forgeable
session token, non-constant-time hash comparison, and the latent `NameError`
from `api/utils.py` using `hashlib` without importing it. Multi-pass just
reported them more completely because no single response had to hold the entire
review.

**Why:** per-file isolation gives every file its own token budget and its own
focused prompt. The single long pass shares one budget across the whole diff, so
later files compete for room with earlier ones — and here the later file
(`dashboard.js`) lost and was dropped entirely.

## Cost

Structural, from the call shape (the task-3 script prints reports only, not
`usage` — exact token counts weren't instrumented this run):

- **Single-pass:** 1 call. Input ≈ the whole diff once; output ≤ 1500 tokens.
- **Multi-pass:** 7 calls (5 chunk + 1 synthesis... 6 model calls; the diff
  content is read once *across* the chunks, but the synthesis call then
  re-ingests all 5 chunk reviews as input and re-emits a merged report). More
  total output tokens (5 chunk reports + 1 merged report vs. one report), so
  multi-pass costs meaningfully more per review.

## Latency

- **Single-pass:** one round-trip.
- **Multi-pass (as written):** 6 sequential round-trips — visibly slower
  wall-clock (the run logged `reviewing chunk 1/5 … 5/5` one after another, then
  the synthesis call). The stretch goal — running the chunk reviews
  concurrently — would collapse the 5 chunk calls to ~1 chunk-call of latency,
  leaving multi-pass at roughly two sequential steps (parallel chunks → synth).

## When multi-pass is worth it (and when it isn't)

| Reach for **multi-pass** when… | Stick with **single-pass** when… |
| --- | --- |
| The diff is long enough that one response can't cover it (this run: a 5-file diff already truncated single-pass before the last file) | The diff is small and fits one response comfortably |
| Coverage/completeness matters more than latency or cost | You're on a latency-sensitive path (PR gate, editor inline) |
| You can parallelize the chunk reviews to hide the extra round-trips | Budget is tight and the extra calls aren't justified |

**Takeaway:** on planted-issue recall the two tied, but multi-pass won on
*overall* coverage purely because per-file budgeting kept the last file from
being truncated away. The cost is more calls and (sequentially) more latency —
worth it on long diffs, overkill on short ones.

> Caveat: both reports were themselves truncated by their `max_tokens` caps
> (single-pass at 1500, the synthesis at 2000), so neither final list is
> exhaustive. To get hard cost/latency numbers, instrument the script to print
> `resp.usage` per call and wall-clock each pass, then re-run.
