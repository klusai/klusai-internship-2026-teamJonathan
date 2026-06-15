#!/usr/bin/env python3
"""
secret-scanner — find leaked credentials in code/config via regex + entropy.

Outputs JSON to stdout so the calling skill can format a report. Secrets are
ALWAYS redacted in output (first/last few chars only) so the report itself
never becomes a new leak.

Usage:
    python scan_secrets.py [PATH]                 # scan working tree (default: .)
    python scan_secrets.py [PATH] --history       # scan all blobs in git history
    python scan_secrets.py [PATH] --min-entropy 4.0
    python scan_secrets.py [PATH] --summary       # also print a human summary to stderr

JSON shape:
  {"mode": "...", "scanned_files": N, "findings": [
     {"file","line","type","severity","match_redacted","entropy","blob"}], ...}
"""
import argparse
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------- entropy
def shannon(s: str) -> float:
    if not s:
        return 0.0
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in Counter(s).values())

# ---------------------------------------------------------------- patterns
# Each: (type, severity, compiled regex, capture group holding the secret)
# severity: critical > high > medium > low
PROVIDER_PATTERNS = [
    ("Private key (PEM)", "critical", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----"), 0),
    ("AWS Access Key ID", "critical", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"), 0),
    ("GitHub token", "critical", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[0-9A-Za-z]{36}\b"), 0),
    ("GitHub fine-grained PAT", "critical", re.compile(r"\bgithub_pat_[0-9A-Za-z_]{82}\b"), 0),
    ("Stripe live secret key", "critical", re.compile(r"\b(?:sk|rk)_live_[0-9A-Za-z]{24,}\b"), 0),
    ("Stripe test secret key", "medium", re.compile(r"\b(?:sk|rk)_test_[0-9A-Za-z]{24,}\b"), 0),
    ("Google API key", "high", re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"), 0),
    ("Slack token", "high", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"), 0),
    ("Slack webhook URL", "high", re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/]+"), 0),
    ("SendGrid API key", "high", re.compile(r"\bSG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}\b"), 0),
    ("Twilio API key", "high", re.compile(r"\bSK[0-9a-fA-F]{32}\b"), 0),
    ("Mailgun API key", "high", re.compile(r"\bkey-[0-9a-f]{32}\b"), 0),
    ("npm token", "high", re.compile(r"\bnpm_[0-9A-Za-z]{36}\b"), 0),
    ("OpenAI API key", "critical", re.compile(r"\bsk-(?:proj-)?[0-9A-Za-z\-_]{20,}\b"), 0),
    ("Anthropic API key", "critical", re.compile(r"\bsk-ant-[0-9A-Za-z\-_]{20,}\b"), 0),
    ("JSON Web Token", "medium", re.compile(r"\beyJ[0-9A-Za-z_-]{10,}\.eyJ[0-9A-Za-z_-]{10,}\.[0-9A-Za-z_-]{10,}\b"), 0),
    ("DB connection string with password", "high",
     re.compile(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|amqp)://[^\s:/@]+:([^\s:/@]{3,})@"), 1),
    ("Credentials in URL", "high", re.compile(r"\b(?:https?|ftp)://[^\s:/@]+:([^\s:/@]{3,})@[^\s/]+"), 1),
]

# Generic "keyword = value" assignments. Value checked for entropy / placeholder.
KEYWORD_ASSIGN = re.compile(
    r"""(?ix)
    \b(?P<key>(?:api[_-]?key|secret(?:[_-]?key)?|access[_-]?token|auth[_-]?token|
        client[_-]?secret|private[_-]?key|passwd|password|pwd|token|bearer))
    \b \s* [:=] \s*
    (?P<q>["'`]?) (?P<val>[^\s"'`]{6,}) (?P=q)
    """,
)

# Standalone high-entropy blobs (base64/hex) with no keyword — noisy, kept low.
STANDALONE = re.compile(r"\b(?P<val>[A-Za-z0-9+/]{32,}={0,2}|[A-Fa-f0-9]{40,})\b")

PLACEHOLDER = re.compile(
    r"(?i)(example|sample|dummy|placeholder|changeme|your[_-]?|xxxx|<[^>]+>|"
    r"redacted|fake|test[_-]?(key|token|secret)|foo|bar|baz|\bnull\b|\bnone\b|\.\.\.|\*\*\*)"
)
# Exact dummy values common in .env.example / templates — not real secrets.
DUMMY_VALUES = {
    "password", "passwd", "pass", "secret", "secretkey", "secret_key", "token",
    "apikey", "api_key", "apitoken", "user", "username", "admin", "administrator",
    "root", "host", "hostname", "localhost", "changeme", "change_me", "example",
    "test", "demo", "mypassword", "yourpassword", "string", "value", "xxx",
}
# Lines/files where standalone-entropy hits are almost always false positives.
NOISE_HINT = re.compile(r"(?i)integrity|sha512-|sha256-|sha1-|\bhash\b|checksum|etag")
# Values that are code references to a secret, not the secret itself.
CODE_REF = re.compile(
    r"(?i)(process\.env|os\.environ|import\.meta|getenv|System\.getenv|"
    r"\$\{|\$\(|<%|\benv\[|config\.|settings\.|\bvault\b|secretmanager|\bprompt\()"
)

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "env", "dist", "build",
             "__pycache__", ".next", ".nuxt", "target", "vendor", "coverage",
             ".transformers-cache", ".cache", ".idea", ".pytest_cache"}
LOCKFILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
             "Cargo.lock", "composer.lock", "Gemfile.lock", "go.sum"}
MAX_BYTES = 2_000_000  # secrets are small; skip huge files

SEV_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}

# ---------------------------------------------------------------- redaction
def redact(secret: str) -> str:
    s = secret.strip()
    if len(s) <= 8:
        return s[0] + "…" if s else "…"
    return f"{s[:4]}…{s[-4:]}"

def is_placeholder(val: str) -> bool:
    if val.lower() in DUMMY_VALUES:
        return True
    if PLACEHOLDER.search(val):
        return True
    if len(set(val)) <= 2:           # "aaaaaaaa", "00000000"
        return True
    return False

# ---------------------------------------------------------------- scanning
def scan_text(text: str, location: str, min_entropy: float, is_lock: bool, blob=None):
    findings = []
    seen = set()       # (line, redacted, type) dedupe within a unit
    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        if len(line) > 4000:          # minified / data line — skip standalone, keep providers
            minified = True
        else:
            minified = False

        recorded_spans = []  # char spans already claimed on this line
        def overlaps(span):
            return any(span[0] < e and s < span[1] for s, e in recorded_spans)

        # 1) strong provider patterns
        for typ, sev, rx, grp in PROVIDER_PATTERNS:
            for m in rx.finditer(line):
                secret = m.group(grp) if grp else m.group(0)
                if grp and is_placeholder(secret):
                    continue
                span = m.span(grp) if grp else m.span()
                if overlaps(span):           # same secret already matched by an earlier pattern
                    continue
                key = (i, redact(secret), typ)
                if key in seen:
                    continue
                seen.add(key)
                recorded_spans.append(span)
                findings.append(_mk(location, i, typ, sev, secret, blob))

        # 2) keyword = value assignments
        for m in KEYWORD_ASSIGN.finditer(line):
            val = m.group("val").rstrip(";,)")
            if is_placeholder(val) or CODE_REF.search(val):
                continue
            ent = shannon(val)
            keyname = m.group("key").lower()
            is_pwd = "pass" in keyname or "pwd" in keyname
            # passwords count even at low entropy; other keys need entropy or length
            if not (is_pwd or ent >= min_entropy or len(val) >= 20):
                continue
            sev = "high" if ent >= min_entropy or len(val) >= 32 else "medium"
            typ = f"Hardcoded {keyname} value"
            key = (i, redact(val), typ)
            if key in seen:
                continue
            seen.add(key)
            recorded_spans.append(m.span("val"))
            findings.append(_mk(location, i, typ, sev, val, blob, ent))

        # 3) standalone high-entropy (conservative)
        if not minified and not is_lock and not NOISE_HINT.search(line):
            for m in STANDALONE.finditer(line):
                val = m.group("val")
                if is_placeholder(val):
                    continue
                # 40-char hex is usually a git sha / digest; require higher bar
                ent = shannon(val)
                if re.fullmatch(r"[A-Fa-f0-9]{40}", val):
                    continue
                if ent < max(min_entropy, 4.3):
                    continue
                if overlaps(m.span("val")):   # already caught by a stronger rule
                    continue
                typ = "High-entropy string"
                key = (i, redact(val), typ)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(_mk(location, i, typ, "low", val, blob, ent))
    return findings

def _mk(loc, line, typ, sev, secret, blob, ent=None):
    return {
        "file": loc, "line": line, "type": typ, "severity": sev,
        "match_redacted": redact(secret),
        "entropy": round(ent if ent is not None else shannon(secret), 2),
        "blob": blob,
    }

# ---------------------------------------------------------------- file discovery
def git(*args, cwd):
    return subprocess.run(["git", "-C", str(cwd), *args],
                          capture_output=True, text=True)

def is_git_repo(path: Path) -> bool:
    return git("rev-parse", "--is-inside-work-tree", cwd=path).returncode == 0

def list_worktree_files(root: Path):
    if is_git_repo(root):
        r = git("ls-files", "--cached", "--others", "--exclude-standard", cwd=root)
        if r.returncode == 0:
            return [root / p for p in r.stdout.splitlines() if p]
    out = []
    for p in root.rglob("*"):
        if p.is_dir():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        out.append(p)
    return out

def read_text(path: Path):
    try:
        if path.stat().st_size > MAX_BYTES:
            return None
        data = path.read_bytes()
        if b"\x00" in data[:8000]:   # binary
            return None
        return data.decode("utf-8", errors="replace")
    except (OSError, ValueError):
        return None

# ---------------------------------------------------------------- modes
def scan_worktree(root: Path, min_entropy: float):
    files = list_worktree_files(root)
    findings, scanned = [], 0
    for f in files:
        if f.name in LOCKFILES:
            is_lock = True
        else:
            is_lock = False
        text = read_text(f)
        if text is None:
            continue
        scanned += 1
        rel = str(f.relative_to(root)) if root in f.parents or f == root else str(f)
        findings.extend(scan_text(text, rel, min_entropy, is_lock))
    return scanned, findings

def scan_history(root: Path, min_entropy: float):
    if not is_git_repo(root):
        print("Not a git repository — cannot scan history.", file=sys.stderr)
        return 0, []
    r = git("rev-list", "--all", "--objects", cwd=root)
    if r.returncode != 0:
        return 0, []
    # map blob sha -> a representative path
    blob_path = {}
    for line in r.stdout.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2 and parts[1]:
            blob_path.setdefault(parts[0], parts[1])
    # filter to blobs (skip trees/commits) via batch-check
    shas = list(blob_path)
    check = subprocess.run(["git", "-C", str(root), "cat-file", "--batch-check"],
                           input="\n".join(shas), capture_output=True, text=True)
    blobs = []
    for line in check.stdout.splitlines():
        p = line.split()
        if len(p) >= 3 and p[1] == "blob" and p[2].isdigit() and int(p[2]) <= MAX_BYTES:
            blobs.append(p[0])
    findings, scanned = [], 0
    for sha in blobs:
        path = blob_path.get(sha, sha)
        if Path(path).name in LOCKFILES or any(d in path.split("/") for d in SKIP_DIRS):
            continue
        content = subprocess.run(["git", "-C", str(root), "cat-file", "-p", sha],
                                 capture_output=True, text=True, errors="replace")
        if content.returncode != 0:
            continue
        if "\x00" in content.stdout[:8000]:
            continue
        scanned += 1
        is_lock = Path(path).name in LOCKFILES
        findings.extend(scan_text(content.stdout, path, min_entropy, is_lock, blob=sha[:10]))
    return scanned, findings

# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--history", action="store_true", help="scan all git-history blobs")
    ap.add_argument("--min-entropy", type=float, default=3.5)
    ap.add_argument("--summary", action="store_true", help="print human summary to stderr")
    args = ap.parse_args()
    root = Path(args.path).resolve()

    if args.history:
        scanned, findings = scan_history(root, args.min_entropy)
        mode = "history"
    else:
        scanned, findings = scan_worktree(root, args.min_entropy)
        mode = "worktree"

    findings.sort(key=lambda f: (SEV_RANK.get(f["severity"], 9), f["file"], f["line"]))
    out = {"mode": mode, "root": str(root), "scanned_files": scanned,
           "finding_count": len(findings), "findings": findings}
    print(json.dumps(out, indent=2))

    if args.summary:
        by_sev = Counter(f["severity"] for f in findings)
        print(f"\n[secret-scanner] {mode}: scanned {scanned} units, "
              f"{len(findings)} findings "
              f"(critical={by_sev['critical']} high={by_sev['high']} "
              f"medium={by_sev['medium']} low={by_sev['low']})", file=sys.stderr)

if __name__ == "__main__":
    main()
