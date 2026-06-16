---
name: secret-scanner
description: Scan a codebase for leaked credentials — API keys, tokens, passwords, private keys, connection strings — using pattern matching plus entropy analysis, followed by a Claude verification pass that triages false positives and hunts for secrets the patterns miss, then produce a readable, redacted report with file and line locations and confidence labels. Use this whenever the user wants to check for hardcoded secrets, audit a repo before making it public, find leaked or committed credentials, verify nothing sensitive is exposed, or asks "are there any secrets/keys in this code". After reporting, offers to help remediate findings and (for public repos) to scan git history.
---

# Secret Scanner

Find credentials that shouldn't be in source control and present them so the user can act. The pipeline is: **scan → verify → report → offer to remediate → optionally scan git history**. A bundled scanner does the deterministic detection; you then apply judgment the regexes can't — confirming what's real, dismissing false positives, and catching what the patterns miss — before turning it all into a clear report and guiding remediation safely.

The guiding principle throughout: **the report and your messages must never become a second leak.** Always work with the scanner's redacted output. Never paste a full secret back to the user, never write secrets to a file, and never echo a matched value in full.

## Step 1 — Run the scanner

The detector lives at `scripts/scan_secrets.py` (relative to this skill). It walks the working tree (respecting `.gitignore` when in a git repo), applies provider-specific regexes, checks Shannon entropy on generic `key = value` assignments and standalone high-entropy strings, and prints **redacted** JSON.

```bash
python3 <skill-dir>/scripts/scan_secrets.py <target-path> --summary
```

- `<target-path>` defaults to `.` — use the repo root the user means.
- `--summary` prints a one-line count to stderr; the JSON report goes to stdout.
- `--min-entropy <float>` (default 3.5) tunes sensitivity. Raise it if the user complains about noise; lower it for a paranoid sweep.

Parse the JSON. Each finding has: `file`, `line`, `type`, `severity` (`critical`/`high`/`medium`/`low`), `match_redacted`, and `entropy`. If the scanner errors or isn't found, fall back to grepping for the patterns yourself — but the script is the source of truth, so prefer fixing the invocation over abandoning it.

## Step 2 — Verify (your own pass)

The scanner is fast and deterministic but pattern-bound: it over-reports things that *look* like secrets and misses anything that doesn't match a known shape. This is where you add the judgment regexes can't. Do three things, reading the actual files (never edit them here — this is read-only analysis). Reading the files means you'll see real secret values in full — that's for your judgment only; never carry a raw value or source line into the report (step 3 covers how to present them).

**1. Triage each finding.** Open the file around each hit and decide whether it's genuinely a live secret. A finding is weaker than it looks when it sits in an obvious test fixture or `*.example`/`*.sample` file, in a comment illustrating format, in documentation, or is plainly a sample/dummy value the scanner's filters didn't catch. It's stronger when it's a real assignment in application or config code, especially something committed. Don't just trust the scanner's severity — a `critical`-typed key in `examples/` may be a non-issue, and a `medium` password in `config/prod.py` may be the worst thing in the repo.

**2. Hunt for what the patterns missed.** The scanner only knows the formats it was taught. Read the high-signal files yourself and look for secrets that wouldn't match a regex:
- Custom or internal token formats (a company-specific prefix, an unusual length) that no public pattern covers.
- Secrets that are **base64- or hex-encoded** to hide them — decode suspicious blobs and check what's inside.
- Credentials **split or concatenated** across lines/variables so no single line matches.
- Secrets under **non-obvious keys** (`auth`, `cookie`, `signature`, `salt`, a vendor's odd field name) or buried in CI/CD YAML, Dockerfiles, k8s manifests, `.ipynb` outputs, or shell scripts.
Focus this sweep on the files most likely to hold secrets so it stays bounded: anything matching `*.env*`, config/settings files, auth/login/payment code, CI configs (`.github/`, `.gitlab-ci.yml`), infra files, and anything the scanner already flagged (a file with one leak often has more).

**3. Don't take "zero findings" at face value.** A clean scanner result means "nothing matched the patterns," not "no secrets." When the scan comes back empty, still spot-read the highest-risk files (the same set above) before you tell the user they're clean. If they genuinely look clean, say so with confidence — you've earned it. If something's off, surface it.

Keep this proportionate: a handful of findings in a small repo is a quick read; a huge monorepo means prioritizing the high-risk files, and you should say what you did and didn't cover rather than implying you eyeballed everything.

## Step 3 — Write the report

Present findings **inline in the conversation** — do not write a report file (a findings file is itself sensitive and easily committed by accident). Merge the scanner output and your verification into one report, grouped by severity, most dangerous first.

Each finding carries a **confidence** (from your step-2 triage) and a **source**, so the user knows what's machine-matched versus what your review concluded:
- Confidence: **confirmed** (you verified it's a real secret), **likely**, or **possible FP** (matched a pattern but probably benign).
- Source: **scanner** (regex/entropy hit) or **Claude** (something you found in verification that the patterns missed).

Use this structure:

```
# Secret scan — <N> findings in <path>

## 🔴 Critical (<count>)
- `path/to/file.ts:42` — **AWS Access Key ID** — `AKIA…CDEF` — confirmed (scanner) — live key in app config
- `config/key.pem:1` — **Private key (PEM)** — `----…----` — confirmed (scanner)

## 🟠 High (<count>)
- `src/db.ts:18` — **DB connection string with password** — `S3c…ss` — confirmed (scanner)
- `.github/workflows/ci.yml:20` — **Inline deploy token** — `glpt…9k2` — likely (Claude) — under a custom `deploy_key:` field the regexes don't cover

## 🟡 Medium (<count>)
...

## ⚪ Low / possible (<count>)
- `lib/data.js:90` — **High-entropy string** — `Xk9…Tv5` — possible FP (scanner) — looks like a content hash, not a credential
```

Guidance on presentation:
- Keep the `match_redacted` value exactly as the scanner gives it; for anything **you** found, redact it the same way (first/last few chars only) — the report must never contain a full secret.
- **The redacted token is the only place a secret may appear.** Do not quote the raw source line, the surrounding code, or the full connection string in your context note — when you read files during verification you'll see the real values, but a note like `password = "hunter2pass"` or `postgres://admin:S3cr3tDbPass@host/db` re-leaks exactly what the redaction protects. Describe the context in words instead ("embedded in the DB connection URL in committed config"). The `file:line` pointer already tells the user where to look.
- **Severity is about blast radius.** Live provider keys (AWS, GitHub, Stripe live, OpenAI/Anthropic, private keys) are critical — they grant direct access. Test keys, JWTs, and bare high-entropy strings are lower because they're often non-sensitive or already scoped. Let your verification override the scanner's default severity when context warrants — and say why in the one-line note.
- Lead with the confirmed findings; don't let possible-FPs dilute the signal. It's fine to collapse a long tail of low-confidence hits into a count with a one-line summary.
- If, after your verification, there are **no real findings**, say so plainly and state what you actually checked ("scanner matched nothing; I also read `.env*`, `config/`, and the auth code — all clean"). That's more trustworthy than a bare "nothing found," and it's honest about coverage without manufacturing concern.

## Step 4 — Offer to remediate

After the report, ask whether the user wants help removing the leaks. **Remediation edits files, so confirm each change before applying it** — never silently rewrite a secret, because the right fix depends on context only the user has (is this key still live? is it already rotated? is the file even meant to hold config?).

For each finding the user wants to address, propose the fix that fits, then apply it only on their go-ahead:

- **Move it to an environment variable.** Replace the literal with a reference (`process.env.X`, `os.environ["X"]`, etc.), add the key to `.env.example` with a placeholder, and ensure `.env` is in `.gitignore`. This is the usual right answer for config.
- **Add to `.gitignore`** when the secret lives in a file that should never be tracked (`.env`, `*.pem`, credentials JSON). Removing it from the working tree isn't enough if it's already committed — point that out.
- **Redact / remove** when it's genuinely dead (a test fixture, an expired key) — just delete or stub it.

Two things to always flag, because they're easy to miss and have real consequences:
1. **A committed secret must be rotated, not just deleted.** Once it's been pushed, treat it as compromised — editing the file doesn't un-leak it. Tell the user to revoke/regenerate the credential at its provider.
2. **Deleting from the working tree leaves it in git history.** That's the bridge to step 5.

## Step 5 — Offer a git-history scan (public repos)

Working-tree-clean ≠ history-clean. A secret removed in a later commit still sits in every earlier one, and on a **public** repo that's fully exposed. So after remediation, offer to scan history — but gate it on exposure, since on a private repo it's lower urgency.

Determine whether the repo is public before pushing this:
```bash
git remote get-url origin                          # is there a remote at all?
gh repo view --json visibility -q .visibility 2>/dev/null   # PUBLIC / PRIVATE, if gh is available
```
If `gh` isn't available or there's no clear answer, just ask the user whether the repo is public. If it is public (or the user wants it regardless), run:

```bash
python3 <skill-dir>/scripts/scan_secrets.py <target-path> --history --summary
```

This scans every blob reachable in history (deduplicated), reporting `file`, `line`, the redacted match, and a short `blob` SHA. Present it like the step-3 report, adding the blob SHA. For locating which commits a leaked blob lives in, point the user at:

```bash
git log --all --oneline --find-object=<blob-sha>
```

History findings are more serious to clean up: removing them means rewriting history (`git filter-repo` or BFG) and force-pushing, which coordinates with everyone who has a clone. Don't run that automatically — explain the cost and let the user decide. And reiterate: **rotate the exposed credentials regardless**, because anyone who cloned already has them.

## Notes on the scanner's coverage

So you can set expectations honestly: the script detects PEM private keys; AWS, GitHub (classic + fine-grained PAT), Stripe, Google, Slack, SendGrid, Twilio, Mailgun, npm, OpenAI, and Anthropic keys; JWTs; credentials embedded in URLs and DB connection strings; keyword-assigned secrets (`api_key`, `password`, `token`, …) confirmed by entropy; and bare high-entropy base64/hex strings. It skips binaries, files over ~2 MB, lockfiles and `.git`/`node_modules`/build dirs (for the standalone-entropy pass), and known placeholder text. It is good, not exhaustive — a custom or obfuscated secret can slip through, so frame results as "what the scanner found," not "proof the repo is clean."
