#!/usr/bin/env python3
"""Detect the test framework, runner command, and existing test layout.

Prints a JSON object so the TDD skill can orient itself before writing
any tests, without needing to ask the user to describe their setup.

Usage:
    python detect_test_env.py [--path ROOT]

Output keys:
    framework       "pytest" | "unittest" | "unknown"
    run_command     shell command to run the full suite
    run_single      template for running one file: replace {file} and {test}
    test_dirs       list of discovered test directories
    test_files      list of discovered test files (up to 20)
    src_dirs        list of likely source directories
    config_files    config files that mention test settings
    notes           list of human-readable observations
"""

import json
import os
import sys
import argparse
import subprocess
from pathlib import Path


CONFIG_MARKERS = {
    "pytest": ["pytest.ini", "conftest.py"],
    "pyproject_pytest": [],   # detected by content
    "setupcfg_pytest": [],    # detected by content
}

IGNORE_DIRS = {".git", "__pycache__", ".venv", "venv", "env", ".env",
               "node_modules", ".tox", "dist", "build", ".mypy_cache",
               ".ruff_cache", ".pytest_cache"}


def find_files(root: Path, pattern: str, max_results=50):
    results = []
    for p in root.rglob(pattern):
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        results.append(str(p.relative_to(root)))
        if len(results) >= max_results:
            break
    return results


def file_contains(path: Path, substring: str) -> bool:
    try:
        return substring in path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return False


def detect_framework(root: Path) -> tuple[str, list[str]]:
    notes = []
    # Explicit config files
    if (root / "pytest.ini").exists():
        notes.append("Found pytest.ini")
        return "pytest", notes
    if (root / "conftest.py").exists():
        notes.append("Found conftest.py at root")
        return "pytest", notes

    pyproject = root / "pyproject.toml"
    if pyproject.exists() and file_contains(pyproject, "[tool.pytest"):
        notes.append("pyproject.toml has [tool.pytest.ini_options]")
        return "pytest", notes

    setup_cfg = root / "setup.cfg"
    if setup_cfg.exists() and file_contains(setup_cfg, "[tool:pytest]"):
        notes.append("setup.cfg has [tool:pytest] section")
        return "pytest", notes

    tox = root / "tox.ini"
    if tox.exists() and file_contains(tox, "pytest"):
        notes.append("tox.ini references pytest")
        return "pytest", notes

    # Check if pytest is importable
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--version"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        notes.append(f"pytest available: {result.stdout.strip()}")
        return "pytest", notes

    # Fallback: check for unittest usage in existing test files
    test_files = find_files(root, "test_*.py", 10) + find_files(root, "*_test.py", 10)
    for tf in test_files:
        if file_contains(root / tf, "import unittest"):
            notes.append(f"unittest import found in {tf}")
            return "unittest", notes

    notes.append("No test framework detected; defaulting to pytest conventions")
    return "unknown", notes


def find_test_dirs(root: Path) -> list[str]:
    candidates = ["tests", "test", "spec"]
    found = []
    for c in candidates:
        p = root / c
        if p.is_dir():
            found.append(c)
    # Also look one level deep
    for child in root.iterdir():
        if child.is_dir() and child.name not in IGNORE_DIRS and child.name not in candidates:
            for c in candidates:
                nested = child / c
                if nested.is_dir():
                    found.append(str(nested.relative_to(root)))
    return found


def find_src_dirs(root: Path) -> list[str]:
    candidates = ["src", "app", "lib"]
    found = []
    for c in candidates:
        p = root / c
        if p.is_dir() and any(p.rglob("*.py")):
            found.append(c)
    # Top-level Python packages (dirs with __init__.py, not test dirs)
    test_dir_names = {"tests", "test", "spec"}
    for child in root.iterdir():
        if (child.is_dir()
                and child.name not in IGNORE_DIRS
                and child.name not in test_dir_names
                and child.name not in candidates
                and (child / "__init__.py").exists()):
            found.append(child.name)
    return found


def build_commands(framework: str, root: Path) -> tuple[str, str]:
    if framework == "pytest":
        run_all = "pytest"
        run_single = "pytest {file}::{test} -v"
    elif framework == "unittest":
        run_all = "python -m unittest discover"
        run_single = "python -m unittest {module}.{test}"
    else:
        run_all = "pytest"   # sane default even if unconfirmed
        run_single = "pytest {file}::{test} -v"

    # Detect if they use a Makefile or scripts
    if (root / "Makefile").exists():
        content = (root / "Makefile").read_text(errors="ignore")
        if "test" in content:
            run_all = "make test   # or: " + run_all

    return run_all, run_single


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", default=".", help="Project root (default: cwd)")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    framework, notes = detect_framework(root)
    test_dirs = find_test_dirs(root)
    src_dirs = find_src_dirs(root)
    test_files = (find_files(root, "test_*.py", 20)
                  + find_files(root, "*_test.py", 20))
    run_all, run_single = build_commands(framework, root)

    config_files = []
    for name in ["pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini",
                 "conftest.py", ".pytest.ini"]:
        if (root / name).exists():
            config_files.append(name)

    output = {
        "framework":    framework,
        "run_command":  run_all,
        "run_single":   run_single,
        "test_dirs":    test_dirs,
        "test_files":   test_files[:20],
        "src_dirs":     src_dirs,
        "config_files": config_files,
        "notes":        notes,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
