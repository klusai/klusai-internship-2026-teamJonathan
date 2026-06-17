#!/usr/bin/env python3
"""Collect commit data for changelog generation.

Outputs JSON with commits grouped by conventional-commit type,
plus raw git log for non-conventional repos.

Usage:
    python collect_commits.py [options]

Options:
    --since TAG       Start from this tag/ref (exclusive). Defaults to the
                      most recent tag; falls back to the initial commit.
    --until REF       End at this ref (inclusive). Defaults to HEAD.
    --max-count N     Cap the number of commits fetched (default: 500).
    --prs             Attempt to enrich commits with merged PR titles via
                      the gh CLI (requires gh auth).
"""

import json
import subprocess
import sys
import re
import argparse


CONVENTIONAL_TYPE_MAP = {
    "feat":     "added",
    "feature":  "added",
    "add":      "added",
    "fix":      "fixed",
    "bugfix":   "fixed",
    "hotfix":   "fixed",
    "perf":     "changed",
    "refactor": "changed",
    "revert":   "changed",
    "change":   "changed",
    "chore":    "changed",
    "build":    "changed",
    "ci":       "changed",
    "style":    "changed",
    "remove":   "removed",
    "removed":  "removed",
    "drop":     "removed",
    "deprecate": "deprecated",
    "deprecated": "deprecated",
    "security": "security",
    "sec":      "security",
}

CHANGELOG_SECTIONS = ["security", "added", "changed", "deprecated", "fixed", "removed", "uncategorized"]


def run(cmd, check=True):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"ERROR: {' '.join(cmd)}\n{result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def get_tags():
    out = run(["git", "tag", "--sort=-version:refname"], check=False)
    return [t for t in out.splitlines() if t] if out else []


def detect_base(since_arg):
    if since_arg:
        return since_arg
    tags = get_tags()
    if tags:
        return tags[0]
    # No tags — use the root commit so we get everything.
    return run(["git", "rev-list", "--max-parents=0", "HEAD"])


def get_commits(base, until, max_count):
    """Return list of dicts with hash, short_hash, author, date, subject, body."""
    sep = "|||"
    fmt = f"%H{sep}%h{sep}%an{sep}%as{sep}%s{sep}%b{sep}---END---"
    range_spec = f"{base}..{until}" if base else until
    out = run([
        "git", "log",
        "--no-merges",
        f"--max-count={max_count}",
        f"--pretty=format:{fmt}",
        range_spec,
    ], check=False)

    commits = []
    if not out:
        return commits

    for block in out.split("---END---\n"):
        block = block.strip()
        if not block:
            continue
        parts = block.split(sep, 5)
        if len(parts) < 5:
            continue
        commits.append({
            "hash":       parts[0],
            "short_hash": parts[1],
            "author":     parts[2],
            "date":       parts[3],
            "subject":    parts[4],
            "body":       parts[5].strip() if len(parts) > 5 else "",
        })
    return commits


def parse_conventional(subject):
    """Return (type_key, scope, breaking, description) or None if not conventional."""
    # type(scope)!: description  OR  type!: description
    m = re.match(r"^(\w+)(?:\(([^)]*)\))?(!)?\s*:\s*(.+)$", subject)
    if not m:
        return None
    type_key = m.group(1).lower()
    scope    = m.group(2) or ""
    breaking = bool(m.group(3))
    desc     = m.group(4).strip()
    return type_key, scope, breaking, desc


def classify(commit):
    """Add 'section', 'scope', 'breaking', 'description' keys to commit dict."""
    parsed = parse_conventional(commit["subject"])
    if parsed:
        type_key, scope, breaking, desc = parsed
        section = CONVENTIONAL_TYPE_MAP.get(type_key, "uncategorized")
        if breaking:
            section = "changed"   # breaking changes surface in Changed + flag
        commit["section"]     = section
        commit["scope"]       = scope
        commit["breaking"]    = breaking
        commit["description"] = desc
    else:
        commit["section"]     = "uncategorized"
        commit["scope"]       = ""
        commit["breaking"]    = False
        commit["description"] = commit["subject"]
    return commit


def enrich_with_prs(commits):
    """Try to map commit hashes to PR numbers/titles via gh CLI."""
    try:
        # gh is optional — skip silently if missing
        result = subprocess.run(
            ["gh", "--version"], capture_output=True
        )
        if result.returncode != 0:
            return commits
    except FileNotFoundError:
        return commits

    for c in commits:
        result = subprocess.run(
            ["gh", "pr", "list", "--search", c["hash"], "--state", "merged",
             "--json", "number,title,url", "--limit", "1"],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            prs = json.loads(result.stdout)
            if prs:
                c["pr_number"] = prs[0]["number"]
                c["pr_title"]  = prs[0]["title"]
                c["pr_url"]    = prs[0]["url"]
    return commits


def main():
    parser = argparse.ArgumentParser(description="Collect commits for changelog generation.")
    parser.add_argument("--since",     default="",    help="Base tag/ref (exclusive). Auto-detected from latest tag if omitted.")
    parser.add_argument("--until",     default="HEAD", help="End ref (default: HEAD).")
    parser.add_argument("--max-count", default=500,   type=int, help="Max commits to fetch.")
    parser.add_argument("--prs",       action="store_true",     help="Enrich with merged PR data via gh CLI.")
    args = parser.parse_args()

    base = detect_base(args.since)
    commits = get_commits(base, args.until, args.max_count)
    commits = [classify(c) for c in commits]

    if args.prs:
        commits = enrich_with_prs(commits)

    tags = get_tags()
    try:
        latest_tag = run(["git", "describe", "--tags", "--abbrev=0"], check=False) or None
    except Exception:
        latest_tag = None

    try:
        repo_url = run(["git", "remote", "get-url", "origin"], check=False) or None
        if repo_url and repo_url.endswith(".git"):
            repo_url = repo_url[:-4]
        # Normalise SSH remote to HTTPS for link building
        if repo_url and repo_url.startswith("git@github.com:"):
            repo_url = repo_url.replace("git@github.com:", "https://github.com/")
    except Exception:
        repo_url = None

    grouped = {s: [] for s in CHANGELOG_SECTIONS}
    breaking = []
    for c in commits:
        grouped[c["section"]].append(c)
        if c.get("breaking"):
            breaking.append(c)

    output = {
        "base_ref":   base,
        "until_ref":  args.until,
        "total":      len(commits),
        "latest_tag": latest_tag,
        "all_tags":   tags[:10],
        "repo_url":   repo_url,
        "grouped":    grouped,
        "breaking":   breaking,
        "raw":        commits,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
