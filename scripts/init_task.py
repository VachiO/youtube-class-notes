#!/usr/bin/env python3
"""Create the next video task folder for a class transcript workflow."""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path


def parse_class_date(value: str) -> str:
    match = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", value.strip())
    if not match:
        raise SystemExit("Date must use dd.mm.yyyy, for example 01.06.2026")
    day, month, year = map(int, match.groups())
    return dt.date(year, month, day).isoformat()


def normalize_subject(value: str) -> str:
    value = value.strip().strip('"').strip("'")
    if not value:
        raise SystemExit("Subject is required")
    value = re.sub(r"[\\/:*?\"<>|]+", "-", value)
    value = re.sub(r"\s+", "-", value)
    return value


def read_source_url(video_dir: Path) -> str | None:
    source = video_dir / "source.txt"
    if not source.exists():
        return None
    for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("url:"):
            return line.split(":", 1)[1].strip()
    return None


def existing_video_dirs(day_dir: Path) -> list[Path]:
    if not day_dir.exists():
        return []
    return sorted(
        [p for p in day_dir.iterdir() if p.is_dir() and re.fullmatch(r"video-\d{2}(?:-v\d+)?", p.name)],
        key=lambda p: p.name,
    )


def next_video_number(day_dir: Path) -> int:
    max_number = 0
    for path in existing_video_dirs(day_dir):
        match = re.fullmatch(r"video-(\d{2})(?:-v\d+)?", path.name)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number + 1


def next_version_dir(base_dir: Path) -> Path:
    if not base_dir.exists():
        return base_dir
    version = 2
    while True:
        candidate = base_dir.with_name(f"{base_dir.name}-v{version}")
        if not candidate.exists():
            return candidate
        version += 1


def target_dir_for(day_dir: Path, url: str) -> Path:
    for path in existing_video_dirs(day_dir):
        if read_source_url(path) == url:
            base_name = re.sub(r"-v\d+$", "", path.name)
            return next_version_dir(day_dir / base_name)
    return day_dir / f"video-{next_video_number(day_dir):02d}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--subject", required=True)
    parser.add_argument("--date", required=True, help="dd.mm.yyyy")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    subject = normalize_subject(args.subject)
    class_date = parse_class_date(args.date)
    day_dir = project_root / "classes" / subject / class_date
    video_dir = target_dir_for(day_dir, args.url.strip())
    chunks_dir = video_dir / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=False)

    created_at = dt.datetime.now().isoformat(timespec="seconds")
    (video_dir / "source.txt").write_text(
        "\n".join(
            [
                f"URL: {args.url.strip()}",
                f"Subject: {subject}",
                f"Class date: {class_date}",
                f"Created at: {created_at}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (video_dir / "processing-notes.txt").write_text(
        "\n".join(
            [
                f"URL: {args.url.strip()}",
                f"Subject: {subject}",
                f"Class date: {class_date}",
                f"Task folder: {video_dir}",
                f"Created at: {created_at}",
                "Status: task folder created",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(video_dir)


if __name__ == "__main__":
    main()

