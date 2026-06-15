#!/usr/bin/env python3
"""format_check.py - detect and auto-fix formatting-rules violations.

Part of the formatting-rules skill. Standard library only.

Usage:
  python3 format_check.py [options] PATH [PATH ...]

Options:
  --fix                 apply safe auto-fixes in place
  --json FILE           write a machine-readable JSON report
  --rules LIST          comma-separated rule IDs to enable (default: all)
  --exclude-rules LIST  comma-separated rule IDs to disable
  --max-line-length N   line length limit for U006 (default 100)
  --max-blank-lines N   blank-line run limit for U005 (default 2)
  --list-rules          print the rule catalog and exit

Exit codes: 0 clean, 1 violations found or remaining, 2 usage/internal error.

Design principle: a fix is automatic only when it cannot change program
behavior. Emojis in string literals, naming, and import order are therefore
reported but never auto-fixed.
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import sys
import tokenize
from collections import Counter
from dataclasses import dataclass

MAX_PASSES = 12
MAX_FILE_BYTES = 2_000_000

RULES = {
    "U001": ("no-emoji", "error",
             "No emojis; auto-removed from comments/docstrings/Markdown, reported in string literals"),
    "U002": ("no-midsentence-linebreak", "error",
             "Prose sentences must not be broken across lines; broken lines are joined"),
    "U003": ("trailing-whitespace", "error", "No whitespace at end of line"),
    "U004": ("eof-newline", "error", "File must end with exactly one newline"),
    "U005": ("max-blank-lines", "warning", "At most N consecutive blank lines (default 2)"),
    "U006": ("line-length", "warning",
             "Code lines must not exceed the limit (default 100); prose and URLs exempt"),
    "U007": ("smart-quotes", "warning", "No smart quotes or typographic dashes in code"),
    "U008": ("tabs-in-indent", "error", "No tabs in indentation"),
    "U009": ("line-endings", "warning", "LF line endings, not CRLF"),
    "P001": ("python-naming", "warning",
             "snake_case functions/variables/args, PascalCase classes, UPPER_SNAKE constants"),
    "P002": ("import-order", "warning", "Imports at top of file; stdlib group before third-party"),
    "P003": ("comma-spacing", "error", "Space required after comma"),
    "P004": ("blank-lines-before-def", "warning", "Two blank lines before top-level def/class"),
}

# Unicode emoji and pictograph blocks (incl. dingbats, misc symbols, ZWJ, VS16, keycap).
EMOJI_RE = re.compile(
    "[\u200d\u20e3\u2600-\u27bf\u2b00-\u2bff\ufe0f"
    "\U0001f000-\U0001faff]"
)

SMART_MAP = {
    "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    "\u2013": "-", "\u2014": "-", "\u2026": "...", "\u00a0": " ",
}

PY_EXTS = {".py"}
PROSE_EXTS = {".md", ".rst", ".txt"}
NB_EXTS = {".ipynb"}
# ext -> (line_comment, block_open, block_close)
GENERIC_SYNTAX = {
    ".js": ("//", "/*", "*/"), ".jsx": ("//", "/*", "*/"),
    ".ts": ("//", "/*", "*/"), ".tsx": ("//", "/*", "*/"),
    ".java": ("//", "/*", "*/"), ".c": ("//", "/*", "*/"),
    ".h": ("//", "/*", "*/"), ".cpp": ("//", "/*", "*/"),
    ".hpp": ("//", "/*", "*/"), ".cs": ("//", "/*", "*/"),
    ".go": ("//", "/*", "*/"), ".rs": ("//", "/*", "*/"),
    ".css": (None, "/*", "*/"), ".scss": ("//", "/*", "*/"),
    ".sql": ("--", "/*", "*/"),
    ".sh": ("#", None, None), ".bash": ("#", None, None), ".zsh": ("#", None, None),
    ".yaml": ("#", None, None), ".yml": ("#", None, None),
    ".toml": ("#", None, None), ".r": ("#", None, None), ".R": ("#", None, None),
    ".rb": ("#", None, None), ".jl": ("#", None, None),
    ".json": (None, None, None),
}
ALL_EXTS = PY_EXTS | PROSE_EXTS | NB_EXTS | set(GENERIC_SYNTAX)

SKIP_DIRS = {".git", ".hg", ".svn", "node_modules", "__pycache__", ".venv", "venv",
             "env", ".env", "dist", "build", ".ipynb_checkpoints", ".mypy_cache",
             ".pytest_cache", ".tox", "site-packages", ".idea", ".vscode", "outputs"}
SKIP_FILES = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
              "Pipfile.lock", "Cargo.lock"}

SENTENCE_END_RE = re.compile(r"[A-Za-z0-9,\)\]'\"%`]$")
CONT_START_RE = re.compile(r"[a-z0-9(`'\"]")
COMMENT_DIRECTIVE_RE = re.compile(r"^#\s*(!|-\*-|noqa|type:|pylint|ruff|flake8|fmt:|coding)")
LIST_ITEM_RE = re.compile(r"\s*([-*+]|\d{1,3}[.)])\s+")
HEADING_RE = re.compile(r"\s{0,3}#{1,6}\s")
FENCE_RE = re.compile(r"\s{0,3}(```|~~~)")
SNAKE_RE = re.compile(r"_{0,2}[a-z][a-z0-9_]*_{0,2}$")
PASCAL_RE = re.compile(r"_?[A-Z][A-Za-z0-9]*$")
CONST_RE = re.compile(r"_{0,2}[A-Z][A-Z0-9_]*$")
DUNDER_RE = re.compile(r"__\w+__$")


@dataclass
class V:
    """A single violation."""
    file: str
    line: int            # 1-based; 0 = file-level
    rule: str
    message: str
    fixable: bool
    severity: str = ""
    cell: int = 0        # 1-based notebook cell number, 0 = not a notebook

    def __post_init__(self):
        if not self.severity:
            self.severity = RULES[self.rule][1]

    def where(self):
        loc = f"{self.file}"
        if self.cell:
            loc += f":cell {self.cell}"
        if self.line:
            loc += f":{self.line}"
        return loc


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def split_lines(text):
    """Split into lines without a trailing-'' sentinel; report EOF state."""
    ends_nl = text.endswith("\n")
    lines = text.split("\n")
    if ends_nl:
        lines.pop()
    return lines, ends_nl


def rebuild(lines, ends_nl):
    return "\n".join(lines) + ("\n" if ends_nl and lines else "")


def clean_prose_segment(seg):
    """Remove emojis from a prose segment and tidy leftover spacing."""
    new = EMOJI_RE.sub("", seg)
    if new != seg:
        new = re.sub(r"  +", " ", new)
        new = re.sub(r" +([.,;:!?])", r"\1", new)
    return new


def eof_checks(lines, ends_nl, path, cfg, cell=0):
    """U004: file must end with exactly one newline."""
    viols, ops = [], []
    if cfg.in_cell or not lines:
        return viols, ops
    if not ends_nl:
        viols.append(V(path, len(lines), "U004", "missing newline at end of file", True, cell=cell))
        ops.append({"kind": "eof", "rule": "U004"})
    elif lines and lines[-1].strip() == "":
        viols.append(V(path, len(lines), "U004", "blank line(s) / extra newlines at end of file", True, cell=cell))
        ops.append({"kind": "eof", "rule": "U004"})
    return viols, ops


def blank_run_checks(lines, path, cfg, cell=0):
    """U005: at most N consecutive blank lines (interior)."""
    viols, ops = [], []
    run_start = None
    for i, line in enumerate(lines + ["sentinel"]):
        if i < len(lines) and line.strip() == "":
            if run_start is None:
                run_start = i
        else:
            if run_start is not None:
                run = i - run_start
                if run > cfg.max_blank_lines and i < len(lines):
                    viols.append(V(path, run_start + 1 + cfg.max_blank_lines, "U005",
                                   f"{run} consecutive blank lines (max {cfg.max_blank_lines})",
                                   True, cell=cell))
                    ops.append({"kind": "delete", "rule": "U005",
                                "start": run_start + cfg.max_blank_lines, "end": i})
                run_start = None
    return viols, ops


def pair_join_check(lines, idx_a, idx_b, text_a, text_b, indent_a, indent_b):
    """Decide whether line idx_b is a mid-sentence continuation of idx_a."""
    a = text_a.rstrip()
    b = text_b.strip()
    if not a or not b:
        return False
    if abs(indent_a - indent_b) > 3:
        return False
    if not SENTENCE_END_RE.search(a):
        return False
    if not CONT_START_RE.match(b):
        return False
    return True


def apply_ops(lines, ends_nl, ops):
    """Apply fix operations. Returns (lines, ends_nl, applied_ops)."""
    applied = []
    for op in ops:
        if op["kind"] == "replace":
            i = op["idx"]
            if i < len(lines) and lines[i] == op["old"]:
                lines[i] = op["new"]
                applied.append(op)
    consumed = set()
    structural = [o for o in ops if o["kind"] in ("join", "delete", "insert")]
    structural.sort(key=lambda o: o.get("idx", o.get("start", 0)), reverse=True)
    for op in structural:
        if op["kind"] == "join":
            i = op["idx"]
            if i in consumed or i + 1 in consumed or i + 1 >= len(lines):
                continue
            child = re.sub(op.get("strip_prefix", r"^\s*"), "", lines[i + 1], count=1)
            lines[i] = lines[i].rstrip() + " " + child.strip()
            del lines[i + 1]
            consumed.update({i, i + 1})
            applied.append(op)
        elif op["kind"] == "delete":
            rng = set(range(op["start"], op["end"]))
            if rng & consumed or op["end"] > len(lines):
                continue
            del lines[op["start"]:op["end"]]
            consumed.update(rng)
            applied.append(op)
        elif op["kind"] == "insert":
            i = op["idx"]
            if i in consumed:
                continue
            lines[i:i] = [""] * op["count"]
            applied.append(op)
    for op in ops:
        if op["kind"] == "eof":
            while lines and lines[-1].strip() == "":
                lines.pop()
            ends_nl = True
            applied.append(op)
    return lines, ends_nl, applied


def line_transform(line, prose_spans, code_mask, cfg, path, lineno, cell=0,
                   py_indent=False, fixable_emoji=True):
    """Detect per-line violations and build at most ONE replace op (first
    applicable category). The fix loop re-analyzes after every pass, so
    multiple issues on one line converge over a few passes without any
    column-offset bookkeeping."""
    viols, op = [], None

    def make_op(new, rule):
        nonlocal op
        if op is None and new != line:
            op = {"kind": "replace", "rule": rule, "idx": lineno - 1, "old": line, "new": new}

    # U008 tabs in indentation
    stripped = line.lstrip(" \t")
    indent = line[:len(line) - len(stripped)]
    if "\t" in indent:
        sev = "error" if py_indent else "warning"
        viols.append(V(path, lineno, "U008", "tab character in indentation", True,
                       severity=sev, cell=cell))
        make_op(indent.replace("\t", "    ") + stripped, "U008")

    # U007 smart quotes / dashes in code regions
    if code_mask is not None:
        cols = [i for i, ch in enumerate(code_mask) if ch in SMART_MAP]
        if cols:
            viols.append(V(path, lineno, "U007",
                           "smart quote/dash in code (likely paste artifact)", True, cell=cell))
            new = line
            for i in reversed(cols):
                new = new[:i] + SMART_MAP[new[i]] + new[i + 1:]
            make_op(new, "U007")

    # U001 emoji
    for (a, b) in prose_spans:
        seg = line[a:b]
        if EMOJI_RE.search(seg):
            if fixable_emoji:
                viols.append(V(path, lineno, "U001", "emoji in comment/prose", True, cell=cell))
                make_op(line[:a] + clean_prose_segment(seg) + line[b:], "U001")
            else:
                viols.append(V(path, lineno, "U001",
                               "emoji in code block content - review manually", False, cell=cell))
    if code_mask is not None and EMOJI_RE.search(code_mask):
        viols.append(V(path, lineno, "U001",
                       "emoji in code - review manually", False, cell=cell))

    # P003 comma spacing (only when a python/code mask is supplied)
    if code_mask is not None and cfg.commas:
        if re.search(r",(?=[^\s)\]\}])", code_mask):
            viols.append(V(path, lineno, "P003", "missing space after comma", True, cell=cell))
            new = line
            for m in reversed(list(re.finditer(r",(?=[^\s)\]\}])", code_mask))):
                new = new[:m.start() + 1] + " " + new[m.start() + 1:]
            make_op(new, "P003")

    # U006 line length (code lines only, URLs exempt)
    if (code_mask is not None and len(line) > cfg.max_line_length
            and code_mask.strip() and "http" not in line.lower()):
        viols.append(V(path, lineno, "U006",
                       f"line is {len(line)} chars (max {cfg.max_line_length})", False, cell=cell))

    # U003 trailing whitespace
    if line != line.rstrip():
        viols.append(V(path, lineno, "U003", "trailing whitespace", True, cell=cell))
        make_op(line.rstrip(), "U003")

    return viols, op


# ---------------------------------------------------------------------------
# Python analyzer
# ---------------------------------------------------------------------------

def py_token_layout(text, lines):
    """Use tokenize to find comments and string spans; build a code mask
    (strings and comments blanked) per line."""
    masked = [list(l) for l in lines]
    comments = {}   # lineno -> (col, text)
    strings = []    # (start_line, token_text)

    def blank(sl, sc, el, ec):
        for r in range(sl, el + 1):
            if r - 1 >= len(masked):
                continue
            row = masked[r - 1]
            a = sc if r == sl else 0
            b = ec if r == el else len(row)
            for c in range(a, min(b, len(row))):
                row[c] = " "

    src = text if text.endswith("\n") else text + "\n"
    fstring_types = {getattr(tokenize, n, -1) for n in
                     ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END")}
    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            comments[tok.start[0]] = (tok.start[1], tok.string)
            blank(tok.start[0], tok.start[1], tok.end[0], tok.end[1])
        elif tok.type == tokenize.STRING or tok.type in fstring_types:
            strings.append((tok.start[0], tok.end[0], tok.string))
            blank(tok.start[0], tok.start[1], tok.end[0], tok.end[1])
    return ["".join(r) for r in masked], comments, strings


def py_ast_checks(tree, lines, path, cfg, cell=0):
    """P001 naming, P002 import order, P004 blank lines before defs."""
    viols, ops = [], []

    def check_name(name, kind, lineno):
        ok = True
        if kind == "function":
            ok = bool(SNAKE_RE.fullmatch(name) or DUNDER_RE.fullmatch(name))
        elif kind == "class":
            ok = bool(PASCAL_RE.fullmatch(name))
        elif kind == "variable":
            ok = bool(SNAKE_RE.fullmatch(name) or CONST_RE.fullmatch(name)
                      or DUNDER_RE.fullmatch(name))
        elif kind == "argument":
            ok = bool(SNAKE_RE.fullmatch(name)) or name in ("self", "cls")
        if not ok:
            expect = {"function": "snake_case", "class": "PascalCase",
                      "variable": "snake_case or UPPER_SNAKE", "argument": "snake_case"}[kind]
            viols.append(V(path, lineno, "P001",
                           f"{kind} '{name}' should be {expect}", False, cell=cell))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            check_name(node.name, "function", node.lineno)
            a = node.args
            for arg in (a.posonlyargs + a.args + a.kwonlyargs
                        + ([a.vararg] if a.vararg else [])
                        + ([a.kwarg] if a.kwarg else [])):
                check_name(arg.arg, "argument", arg.lineno)
        elif isinstance(node, ast.ClassDef):
            check_name(node.name, "class", node.lineno)

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                for n in ast.walk(t):
                    if isinstance(n, ast.Name):
                        check_name(n.id, "variable", node.lineno)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            check_name(node.target.id, "variable", node.lineno)

    # P002: stdlib group first, imports at top
    stdlib = getattr(sys, "stdlib_module_names", frozenset())
    seen_third_party = False
    seen_code = False
    for i, node in enumerate(tree.body):
        is_docstring = (i == 0 and isinstance(node, ast.Expr)
                        and isinstance(node.value, ast.Constant)
                        and isinstance(node.value.value, str))
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                local = node.level > 0
            else:
                root = node.names[0].name.split(".")[0]
                local = False
            if seen_code:
                viols.append(V(path, node.lineno, "P002",
                               f"import '{root or '.'}' not at top of file", False, cell=cell))
            if root == "__future__":
                continue
            if local or root not in stdlib:
                seen_third_party = True
            elif seen_third_party:
                viols.append(V(path, node.lineno, "P002",
                               f"stdlib import '{root}' after third-party imports "
                               "- group stdlib first", False, cell=cell))
        elif not is_docstring:
            seen_code = True

    # P004: two blank lines before top-level def/class
    if not cfg.in_cell:
        for pos, node in enumerate(tree.body):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if pos == 0:
                continue
            start = min([d.lineno for d in node.decorator_list] + [node.lineno])
            i = start - 2
            while i >= 0 and lines[i].lstrip().startswith("#"):
                i -= 1
            blanks, j = 0, i
            while j >= 0 and lines[j].strip() == "":
                blanks += 1
                j -= 1
            if j >= 0 and blanks < 2:
                viols.append(V(path, node.lineno, "P004",
                               f"expected 2 blank lines before top-level "
                               f"'{node.name}', found {blanks}", True, cell=cell))
                ops.append({"kind": "insert", "rule": "P004",
                            "idx": j + 1, "count": 2 - blanks})
    return viols, ops


def analyze_python(text, path, cfg, cell=0):
    lines, ends_nl = split_lines(text)
    viols, ops = [], []
    if any(l.lstrip().startswith(("%", "!")) for l in lines):
        return analyze_generic(text, path, cfg, ("#", None, None), cell=cell)
    try:
        tree = ast.parse(text if text.endswith("\n") else text + "\n")
        masked, comments, strings = py_token_layout(text, lines)
    except (SyntaxError, tokenize.TokenError, IndentationError, ValueError):
        return analyze_generic(text, path, cfg, ("#", None, None), cell=cell)

    # Docstring spans (treated as prose, emoji fixable)
    doc_spans = []
    nodes = [tree] + [n for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    for n in nodes:
        body = getattr(n, "body", [])
        if (body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)):
            doc_spans.append((body[0].value.lineno, body[0].value.end_lineno))
    doc_lines = set()
    for (a, b) in doc_spans:
        doc_lines.update(range(a, b + 1))
    doc_starts = {a for (a, _) in doc_spans}

    # Emoji in non-docstring string literals: manual only
    for (sl, el, tokstr) in strings:
        if sl in doc_starts:
            continue
        if EMOJI_RE.search(tokstr):
            viols.append(V(path, sl, "U001",
                           "emoji in string literal - removing would change "
                           "program behavior, review manually", False, cell=cell))

    # Per-line transforms
    for i, line in enumerate(lines, 1):
        prose_spans = []
        if i in comments:
            col, _ = comments[i]
            prose_spans.append((col, len(line)))
        if i in doc_lines:
            prose_spans.append((0, len(line)))
        if i == 1 and line.startswith("#!"):
            prose_spans = []
        mask = masked[i - 1] if i - 1 < len(masked) else line
        vs, op = line_transform(line, prose_spans, mask, cfg, path, i, cell=cell,
                                py_indent=True, fixable_emoji=True)
        viols.extend(vs)
        if op:
            ops.append(op)

    # U002 in consecutive full-line comments
    groups, cur = [], []
    for i in range(1, len(lines) + 1):
        c = comments.get(i)
        full = c is not None and lines[i - 1][:c[0]].strip() == ""
        if full and not COMMENT_DIRECTIVE_RE.match(c[1]):
            if cur and (i - 1 != cur[-1][0] or comments[cur[-1][0]][0] != c[0]):
                groups.append(cur)
                cur = []
            cur.append((i, c))
        else:
            if cur:
                groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    for g in groups:
        for (ln_a, ca), (ln_b, cb) in zip(g, g[1:]):
            ta = re.sub(r"^#+\s?", "", ca[1])
            tb = re.sub(r"^#+\s?", "", cb[1])
            if pair_join_check(lines, ln_a, ln_b, ta, tb, ca[0], cb[0]):
                viols.append(V(path, ln_a, "U002",
                               "comment sentence broken across lines", True, cell=cell))
                ops.append({"kind": "join", "rule": "U002", "idx": ln_a - 1,
                            "strip_prefix": r"^\s*#+\s?"})

    # U002 inside docstrings (equal indent only; bare quote lines exempt)
    quote_only = {'"""', "'''", 'r"""', "r'''"}
    for (a, b) in doc_spans:
        for ln in range(a, b):
            la, lb = lines[ln - 1], lines[ln]
            if la.strip().lower() in quote_only or lb.strip().lower() in quote_only:
                continue
            ia = len(la) - len(la.lstrip())
            ib = len(lb) - len(lb.lstrip())
            if la.strip() and lb.strip() and ia == ib and \
                    pair_join_check(lines, ln, ln + 1, la, lb, ia, ib):
                viols.append(V(path, ln, "U002",
                               "docstring sentence broken across lines", True, cell=cell))
                ops.append({"kind": "join", "rule": "U002", "idx": ln - 1})

    v2, o2 = py_ast_checks(tree, lines, path, cfg, cell=cell)
    viols.extend(v2)
    ops.extend(o2)
    v3, o3 = blank_run_checks(lines, path, cfg, cell=cell)
    viols.extend(v3)
    ops.extend(o3)
    v4, o4 = eof_checks(lines, ends_nl, path, cfg, cell=cell)
    viols.extend(v4)
    ops.extend(o4)
    return viols, ops


# ---------------------------------------------------------------------------
# Generic code analyzer (js, sh, yaml, ... and python fallback)
# ---------------------------------------------------------------------------

def analyze_generic(text, path, cfg, syntax, cell=0):
    line_c, block_o, block_c = syntax
    lines, ends_nl = split_lines(text)
    viols, ops = [], []
    in_block = False
    comment_info = {}   # idx -> (col, text, full_line)

    for idx, line in enumerate(lines):
        mask = list(line)
        i, n = 0, len(line)
        quote = None
        com_col = None
        while i < n:
            ch = line[i]
            if in_block:
                end = line.find(block_c, i) if block_c else -1
                if end == -1:
                    for k in range(i, n):
                        mask[k] = " "
                    com_col = 0 if com_col is None else com_col
                    i = n
                else:
                    for k in range(i, end + len(block_c)):
                        mask[k] = " "
                    in_block = False
                    i = end + len(block_c)
                continue
            if quote:
                if ch == "\\":
                    if i < n:
                        mask[i] = " "
                    if i + 1 < n:
                        mask[i + 1] = " "
                    i += 2
                    continue
                if ch == quote:
                    quote = None
                mask[i] = " "
                i += 1
                continue
            if ch in "\"'`":
                quote = ch
                mask[i] = " "
                i += 1
                continue
            if line_c and line.startswith(line_c, i):
                com_col = i
                for k in range(i, n):
                    mask[k] = " "
                break
            if block_o and line.startswith(block_o, i):
                in_block = True
                continue
            i += 1
        if com_col is not None:
            comment_info[idx] = (com_col, line[com_col:],
                                 line[:com_col].strip() == "")
        # Emoji inside string literals (blanked in mask, outside any comment)
        if EMOJI_RE.search(line):
            com_start = com_col if com_col is not None else len(line)
            for m in EMOJI_RE.finditer(line):
                if m.start() < com_start and m.start() < len(mask) and mask[m.start()] == " ":
                    viols.append(V(path, idx + 1, "U001",
                                   "emoji in string literal - removing would change "
                                   "behavior, review manually", False, cell=cell))
                    break
        prose_spans = [(com_col, len(line))] if com_col is not None else []
        if idx == 0 and line.startswith("#!"):
            prose_spans = []
        vs, op = line_transform(line, prose_spans, "".join(mask), cfg, path,
                                idx + 1, cell=cell, py_indent=False, fixable_emoji=True)
        viols.extend(vs)
        if op:
            ops.append(op)

    # U002 across consecutive full-line comments
    prefix_re = re.compile(r"^(//+|#+|--+)\s?")
    prev = None
    for idx in sorted(comment_info):
        col, ctext, full = comment_info[idx]
        if not full or COMMENT_DIRECTIVE_RE.match(ctext):
            prev = None
            continue
        if prev is not None and idx == prev[0] + 1 and col == prev[1]:
            ta = prefix_re.sub("", prev[2])
            tb = prefix_re.sub("", ctext)
            if pair_join_check(lines, prev[0], idx, ta, tb, prev[1], col):
                viols.append(V(path, prev[0] + 1, "U002",
                               "comment sentence broken across lines", True, cell=cell))
                ops.append({"kind": "join", "rule": "U002", "idx": prev[0],
                            "strip_prefix": r"^\s*(//+|#+|--+)\s?"})
        prev = (idx, col, ctext)

    v3, o3 = blank_run_checks(lines, path, cfg, cell=cell)
    viols.extend(v3)
    ops.extend(o3)
    v4, o4 = eof_checks(lines, ends_nl, path, cfg, cell=cell)
    viols.extend(v4)
    ops.extend(o4)
    return viols, ops


# ---------------------------------------------------------------------------
# Markdown / prose analyzer
# ---------------------------------------------------------------------------

def md_classify(lines):
    kinds = []
    in_fence = False
    in_front = False
    for idx, line in enumerate(lines):
        s = line.strip()
        if idx == 0 and s == "---":
            in_front = True
            kinds.append("code")
            continue
        if in_front:
            kinds.append("code")
            if s == "---":
                in_front = False
            continue
        if FENCE_RE.match(line):
            kinds.append("fence")
            in_fence = not in_fence
            continue
        if in_fence:
            kinds.append("code")
            continue
        if not s:
            kinds.append("blank")
        elif HEADING_RE.match(line) or s.startswith("#"):
            kinds.append("heading")
        elif s.startswith("|"):
            kinds.append("table")
        elif len(line) - len(line.lstrip()) >= 4:
            kinds.append("code")
        else:
            kinds.append("prose")
    return kinds


def analyze_markdown(text, path, cfg, cell=0):
    lines, ends_nl = split_lines(text)
    viols, ops = [], []
    kinds = md_classify(lines)
    bq_re = re.compile(r"^\s*((?:>\s*)+)")

    for idx, line in enumerate(lines):
        kind = kinds[idx]
        fixable = kind in ("prose", "heading", "table", "blank")
        prose_spans = [(0, len(line))] if kind != "code" or not line.strip() else []
        if kind == "code" and line.strip():
            if EMOJI_RE.search(line):
                viols.append(V(path, idx + 1, "U001",
                               "emoji in code block content - review manually",
                               False, cell=cell))
        vs, op = line_transform(line, prose_spans, None, cfg, path, idx + 1,
                                cell=cell, py_indent=False, fixable_emoji=fixable)
        viols.extend(vs)
        if op:
            ops.append(op)

    for idx in range(len(lines) - 1):
        if kinds[idx] != "prose" or kinds[idx + 1] != "prose":
            continue
        a, b = lines[idx], lines[idx + 1]
        if LIST_ITEM_RE.match(b):
            continue
        ma, mb = bq_re.match(a), bq_re.match(b)
        depth_a = ma.group(1).count(">") if ma else 0
        depth_b = mb.group(1).count(">") if mb else 0
        if depth_a != depth_b:
            continue
        ta = a[ma.end():] if ma else a
        tb = b[mb.end():] if mb else b
        if LIST_ITEM_RE.match(a):
            ta = a[LIST_ITEM_RE.match(a).end():]
        ia = len(ta) - len(ta.lstrip())
        ib = len(tb) - len(tb.lstrip())
        if pair_join_check(lines, idx, idx + 1, ta, tb, ia, ib):
            viols.append(V(path, idx + 1, "U002",
                           "sentence broken across lines", True, cell=cell))
            ops.append({"kind": "join", "rule": "U002", "idx": idx,
                        "strip_prefix": r"^\s*(>\s*)*"})

    v3, o3 = blank_run_checks(lines, path, cfg, cell=cell)
    viols.extend(v3)
    ops.extend(o3)
    v4, o4 = eof_checks(lines, ends_nl, path, cfg, cell=cell)
    viols.extend(v4)
    ops.extend(o4)
    return viols, ops


# ---------------------------------------------------------------------------
# Fix engine and file handling
# ---------------------------------------------------------------------------

def enabled_only(viols, ops, cfg):
    viols = [v for v in viols if v.rule in cfg.enabled]
    ops = [o for o in ops if o["rule"] in cfg.enabled]
    return viols, ops


def fix_loop(text, analyzer, path, cfg, cell=0):
    """Re-analyze and apply fixes until stable."""
    fixed = Counter()
    for _ in range(MAX_PASSES):
        viols, ops = analyzer(text, path, cfg, cell=cell)
        viols, ops = enabled_only(viols, ops, cfg)
        if not ops:
            break
        lines, ends_nl = split_lines(text)
        lines, ends_nl, applied = apply_ops(lines, ends_nl, ops)
        if not applied:
            break
        for op in applied:
            fixed[op["rule"]] += 1
        new_text = rebuild(lines, ends_nl)
        if new_text == text:
            break
        text = new_text
    final_viols, _ = analyzer(text, path, cfg, cell=cell)
    final_viols, _ = enabled_only(final_viols, [], cfg)
    return text, fixed, final_viols


def pick_analyzer(ext):
    if ext in PY_EXTS:
        return analyze_python
    if ext in PROSE_EXTS:
        return analyze_markdown
    if ext in GENERIC_SYNTAX:
        syntax = GENERIC_SYNTAX[ext]
        return lambda t, p, c, cell=0: analyze_generic(t, p, c, syntax, cell=cell)
    return None


def process_text_file(path, disp, cfg, do_fix):
    try:
        raw = open(path, "rb").read()
    except OSError as e:
        return [], Counter(), f"read error: {e}"
    if b"\0" in raw[:8192] or len(raw) > MAX_FILE_BYTES:
        return [], Counter(), "skipped (binary or too large)"
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return [], Counter(), "skipped (not valid UTF-8)"

    viols, fixed = [], Counter()
    had_crlf = "\r" in text
    if had_crlf and "U009" in cfg.enabled:
        viols.append(V(disp, 0, "U009", "CRLF line endings", True))
    norm = text.replace("\r\n", "\n").replace("\r", "\n")

    analyzer = pick_analyzer(os.path.splitext(path)[1])
    if do_fix:
        new_text, fixed, remaining = fix_loop(norm, analyzer, disp, cfg)
        if had_crlf and "U009" in cfg.enabled:
            fixed["U009"] += 1
        out = new_text
        if had_crlf and "U009" not in cfg.enabled:
            out = out.replace("\n", "\r\n")
        if out != text:
            with open(path, "w", encoding="utf-8", newline="") as f:
                f.write(out)
        return remaining, fixed, None
    else:
        av, _ = analyzer(norm, disp, cfg)
        av, _ = enabled_only(av, [], cfg)
        return viols + av, fixed, None


def process_notebook(path, disp, cfg, do_fix):
    try:
        with open(path, encoding="utf-8") as f:
            nb = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        return [], Counter(), f"skipped (cannot parse notebook: {e})"
    viols, fixed = [], Counter()
    changed = False
    import types
    cell_cfg = types.SimpleNamespace(**{**vars(cfg), "in_cell": True})
    for ci, cell in enumerate(nb.get("cells", []), 1):
        src = cell.get("source", [])
        was_list = isinstance(src, list)
        text = "".join(src) if was_list else src
        ctype = cell.get("cell_type")
        if ctype == "code":
            analyzer = analyze_python
            cell_cfg.commas = True
        elif ctype == "markdown":
            analyzer = analyze_markdown
        else:
            continue
        if do_fix:
            new_text, f_counts, remaining = fix_loop(text, analyzer, disp, cell_cfg, cell=ci)
            fixed.update(f_counts)
            viols.extend(remaining)
            if new_text != text:
                changed = True
                if was_list:
                    parts = new_text.split("\n")
                    rebuilt = [p + "\n" for p in parts[:-1]]
                    if parts[-1] != "":
                        rebuilt.append(parts[-1])
                    cell["source"] = rebuilt
                else:
                    cell["source"] = new_text
        else:
            av, _ = analyzer(text, disp, cell_cfg, cell=ci)
            av, _ = enabled_only(av, [], cell_cfg)
            viols.extend(av)
    if do_fix and changed:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(nb, f, indent=1, ensure_ascii=False)
            f.write("\n")
    return viols, fixed, None


def discover(paths):
    files = []
    for p in paths:
        if os.path.isfile(p):
            files.append(p)
        elif os.path.isdir(p):
            for root, dirs, names in os.walk(p):
                dirs[:] = [d for d in sorted(dirs) if d not in SKIP_DIRS]
                for name in sorted(names):
                    ext = os.path.splitext(name)[1]
                    if ext in ALL_EXTS and name not in SKIP_FILES:
                        files.append(os.path.join(root, name))
        else:
            print(f"warning: path not found: {p}", file=sys.stderr)
    return files


def main(argv=None):
    ap = argparse.ArgumentParser(description="formatting-rules checker/fixer")
    ap.add_argument("paths", nargs="*", help="files or directories")
    ap.add_argument("--fix", action="store_true")
    ap.add_argument("--json", dest="json_out")
    ap.add_argument("--rules")
    ap.add_argument("--exclude-rules")
    ap.add_argument("--max-line-length", type=int, default=100)
    ap.add_argument("--max-blank-lines", type=int, default=2)
    ap.add_argument("--list-rules", action="store_true")
    args = ap.parse_args(argv)

    if args.list_rules:
        for rid, (name, sev, desc) in RULES.items():
            print(f"{rid}  {name:28s} {sev:8s} {desc}")
        return 0
    if not args.paths:
        ap.error("no paths given")

    import types
    enabled = set(RULES)
    if args.rules:
        enabled = {r.strip().upper() for r in args.rules.split(",")} & set(RULES)
    if args.exclude_rules:
        enabled -= {r.strip().upper() for r in args.exclude_rules.split(",")}
    cfg = types.SimpleNamespace(enabled=enabled, max_line_length=args.max_line_length,
                                max_blank_lines=args.max_blank_lines,
                                in_cell=False, commas=True)

    files = discover(args.paths)
    if not files:
        print("no supported files found")
        return 0

    all_viols = []
    all_fixed = Counter()
    notes = []
    for path in files:
        disp = os.path.relpath(path) if not os.path.isabs(path) else path
        ext = os.path.splitext(path)[1]
        if ext in NB_EXTS:
            viols, fixed, note = process_notebook(path, disp, cfg, args.fix)
        else:
            viols, fixed, note = process_text_file(path, disp, cfg, args.fix)
        if note:
            notes.append(f"{disp}: {note}")
        all_viols.extend(viols)
        all_fixed.update(fixed)

    all_viols.sort(key=lambda v: (v.file, v.cell, v.line, v.rule))
    by_file = {}
    for v in all_viols:
        by_file.setdefault(v.file, []).append(v)
    for fname, vs in by_file.items():
        print(fname)
        for v in vs:
            loc = f"cell {v.cell}, line {v.line}" if v.cell else f"line {v.line}"
            fx = "auto-fixable" if v.fixable else "manual"
            print(f"  {loc:18s} {v.rule} {v.severity:7s} {v.message} [{fx}]")
        print()

    rule_counts = Counter(v.rule for v in all_viols)
    summary_bits = ", ".join(f"{r} x{c}" for r, c in sorted(rule_counts.items()))
    n_fixable = sum(1 for v in all_viols if v.fixable)
    if args.fix:
        fixed_bits = ", ".join(f"{r} x{c}" for r, c in sorted(all_fixed.items()))
        print(f"Fixed {sum(all_fixed.values())} violation(s)"
              + (f": {fixed_bits}" if fixed_bits else ""))
        print(f"Remaining {len(all_viols)} violation(s)"
              + (f" ({summary_bits}) - these need manual attention" if all_viols else ""))
    else:
        print(f"Found {len(all_viols)} violation(s) in {len(by_file)} file(s) "
              f"out of {len(files)} scanned ({n_fixable} auto-fixable)"
              + (f": {summary_bits}" if summary_bits else ""))
    for note in notes:
        print(f"note: {note}")

    if args.json_out:
        payload = {
            "mode": "fix" if args.fix else "check",
            "files_scanned": len(files),
            "summary": {"total": len(all_viols), "fixable": n_fixable,
                        "by_rule": dict(rule_counts)},
            "fixed": dict(all_fixed),
            "violations": [
                {"file": v.file, "cell": v.cell or None, "line": v.line,
                 "rule": v.rule, "name": RULES[v.rule][0], "severity": v.severity,
                 "message": v.message, "fixable": v.fixable}
                for v in all_viols
            ],
        }
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"JSON report written to {args.json_out}")

    return 1 if all_viols else 0


if __name__ == "__main__":
    sys.exit(main())
