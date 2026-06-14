#!/usr/bin/env bash
# collect_branch_data.sh - gather everything needed to draft a PR description.
#
# Usage: bash collect_branch_data.sh [base-branch]
#
# Auto-detects the base branch when not given. Prints clearly delimited
# sections: BASE, BRANCH, COMMITS, DIFFSTAT, STATUS, DIFF. When the diff is
# very large it prints only the diffstat and instructs the caller to read
# files selectively, so the output stays usable as model context.

set -euo pipefail

MAX_DIFF_LINES=4000

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: not inside a git repository" >&2
    exit 1
fi

BASE="${1:-}"
if [ -z "$BASE" ]; then
    for candidate in origin/main origin/master origin/develop main master develop; do
        if git rev-parse --verify --quiet "$candidate" >/dev/null; then
            # Skip candidates that point at HEAD itself (same branch).
            if [ "$(git rev-parse "$candidate")" != "$(git rev-parse HEAD)" ] || \
               [ "$(git rev-parse --abbrev-ref HEAD)" != "${candidate#origin/}" ]; then
                BASE="$candidate"
                break
            fi
        fi
    done
fi

if [ -z "$BASE" ]; then
    echo "ERROR: could not auto-detect a base branch; pass one explicitly," >&2
    echo "e.g. bash collect_branch_data.sh origin/main" >&2
    exit 1
fi

MERGE_BASE="$(git merge-base "$BASE" HEAD)" || {
    echo "ERROR: no merge base between $BASE and HEAD" >&2
    exit 1
}

echo "=== BASE ==="
echo "$BASE (merge-base $MERGE_BASE)"

echo "=== BRANCH ==="
git rev-parse --abbrev-ref HEAD

if [ "$MERGE_BASE" = "$(git rev-parse HEAD)" ]; then
    echo "=== RESULT ==="
    echo "Branch contains no commits beyond $BASE - nothing to describe."
    exit 0
fi

echo "=== COMMITS (newest first, merges excluded) ==="
git log --no-merges --format='--- %h %s%n%b' "$MERGE_BASE"..HEAD

echo "=== DIFFSTAT ==="
git diff --stat "$MERGE_BASE"..HEAD

echo "=== STATUS (uncommitted changes - these will NOT be in the PR) ==="
git status --short || true

DIFF_LINES="$(git diff "$MERGE_BASE"..HEAD | wc -l)"
echo "=== DIFF ($DIFF_LINES lines) ==="
if [ "$DIFF_LINES" -gt "$MAX_DIFF_LINES" ]; then
    echo "(diff exceeds $MAX_DIFF_LINES lines - omitted; use the diffstat above and"
    echo "read significant files with: git diff $MERGE_BASE..HEAD -- <path>)"
else
    git diff "$MERGE_BASE"..HEAD
fi
