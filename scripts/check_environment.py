#!/usr/bin/env python3
"""Preflight checks for the class-note processing workflow."""

from __future__ import annotations

import importlib.metadata
import shutil
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "AGENTS.md",
    "PROCESS.md",
    "prompts/revise-transcript.md",
    "prompts/summarize-lecture.md",
    "scripts/init_task.py",
    "scripts/get_youtube_transcript.py",
    "scripts/split_text.py",
    "scripts/build_site_index.py",
]
REQUIRED_PACKAGES = {
    "youtube-transcript-api": "1.2.4",
    "yt-dlp": "2026.6.9",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def check_python() -> None:
    version = sys.version_info
    if version < (3, 11):
        fail(f"Python 3.11+ is required; found {version.major}.{version.minor}.{version.micro}")
    print(f"OK: Python {version.major}.{version.minor}.{version.micro}")


def check_files() -> None:
    missing = [name for name in REQUIRED_FILES if not (PROJECT_ROOT / name).exists()]
    if missing:
        fail("Missing required repo files: " + ", ".join(missing))
    print("OK: required workflow files exist")


def check_packages() -> None:
    for package, expected in REQUIRED_PACKAGES.items():
        try:
            actual = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            fail(f"Package {package} is not installed. Run: python -m pip install -r requirements.txt")
        if actual != expected:
            fail(
                f"Package {package} must be {expected}; found {actual}. "
                "Run: python -m pip install -r requirements.txt"
            )
        print(f"OK: {package}=={actual}")


def check_git() -> None:
    if not shutil.which("git"):
        fail("git is required to clone, commit, and push processed notes")
    print("OK: git available")


def main() -> None:
    check_python()
    check_git()
    check_files()
    check_packages()
    print("OK: environment is ready for this repo workflow")


if __name__ == "__main__":
    main()
