#!/usr/bin/env python3
"""Local lifecycle state and locks for scheduled lecture processing.

The state file is deliberately local to one Codex workspace. It records what
the automation has observed without creating unrelated commits when no lecture
needs processing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATE_PATH = PROJECT_ROOT / "data" / "automation-state.json"
LOCK_DIR = PROJECT_ROOT / "data" / "automation-locks"
VALID_STATUSES = {"discovered", "queued", "running", "completed", "blocked", "failed"}
ACTIVE_STATUSES = {"queued", "running"}
REQUIRED_OUTPUTS = (
    "source.txt",
    "transcript-raw.txt",
    "transcript-original.txt",
    "transcript-revised.txt",
    "lecture-summary.txt",
    "processing-notes.txt",
)


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def video_id(value: str) -> str:
    value = value.strip()
    if re.fullmatch(r"[\w-]{11}", value):
        return value
    parsed = urlparse(value)
    if parsed.netloc.endswith("youtu.be"):
        candidate = parsed.path.strip("/").split("/", 1)[0]
    else:
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    if not re.fullmatch(r"[\w-]{11}", candidate):
        raise ValueError(f"Invalid YouTube URL or video id: {value}")
    return candidate


def load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {"version": 1, "videos": {}}
    try:
        state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid automation state: {exc}")
    if not isinstance(state, dict) or not isinstance(state.get("videos", {}), dict):
        raise SystemExit("Invalid automation state structure")
    state.setdefault("version", 1)
    return state


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(STATE_PATH)


def print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def source_video_id(source: Path) -> str | None:
    if not source.exists():
        return None
    for line in source.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.lower().startswith("url:"):
            try:
                return video_id(line.split(":", 1)[1].strip())
            except ValueError:
                return None
    return None


def completed_folder(item: dict[str, Any]) -> Path | None:
    subject = item.get("subject", "")
    class_date = item.get("classDate", "")
    target_id = item.get("videoId", "")
    day = PROJECT_ROOT / "classes" / subject / class_date
    if not day.exists():
        return None
    for folder in sorted(day.glob("video-*")):
        if folder.is_dir() and source_video_id(folder / "source.txt") == target_id:
            if all((folder / name).is_file() and (folder / name).stat().st_size for name in REQUIRED_OUTPUTS):
                if (folder / "chunks").is_dir():
                    return folder
    return None


def index_contains(item: dict[str, Any]) -> bool:
    path = PROJECT_ROOT / "data" / "site-index.json"
    if not path.exists():
        return False
    try:
        entries = json.loads(path.read_text(encoding="utf-8")).get("lectures", [])
    except json.JSONDecodeError:
        return False
    return any(video_id(entry.get("sourceUrl", "")) == item["videoId"] for entry in entries if entry.get("sourceUrl"))


def command_upsert(args: argparse.Namespace) -> None:
    state = load_state()
    key = video_id(args.url)
    item = state["videos"].get(key, {"videoId": key, "discoveredAt": now(), "attempts": 0})
    item.update({
        "subject": args.subject,
        "classDate": args.class_date,
        "archiveDateRaw": args.archive_date_raw,
        "url": args.url,
        "archiveUrl": args.archive_url,
        "lastSeenAt": now(),
    })
    if item.get("status") not in ACTIVE_STATUSES and item.get("status") != "completed":
        item["status"] = "discovered"
    state["videos"][key] = item
    save_state(state)
    print_json(item)


def command_set(args: argparse.Namespace) -> None:
    if args.status not in VALID_STATUSES:
        raise SystemExit(f"Invalid status: {args.status}")
    state = load_state()
    key = video_id(args.video)
    item = state["videos"].get(key)
    if not item:
        raise SystemExit(f"Unknown video: {key}; run upsert first")
    old_status = item.get("status")
    item["status"] = args.status
    item["updatedAt"] = now()
    if args.status == "queued" and old_status != "queued":
        item["attempts"] = int(item.get("attempts", 0)) + 1
        item["queuedAt"] = now()
    if args.status == "running":
        item.setdefault("startedAt", now())
    if args.status in {"completed", "blocked", "failed"}:
        item["finishedAt"] = now()
    for key_name, value in (("workerTaskId", args.worker_task_id), ("taskDir", args.task_dir), ("commit", args.commit), ("message", args.message)):
        if value is not None:
            item[key_name] = value
    state["videos"][key] = item
    save_state(state)
    print_json(item)


def command_status(args: argparse.Namespace) -> None:
    state = load_state()
    if args.video:
        item = state["videos"].get(video_id(args.video))
        print_json(item or {})
        raise SystemExit(0 if item else 1)
    items = list(state["videos"].values())
    if args.active:
        items = [item for item in items if item.get("status") in ACTIVE_STATUSES]
    print_json(sorted(items, key=lambda item: item.get("lastSeenAt", ""), reverse=True))


def command_verify(args: argparse.Namespace) -> None:
    state = load_state()
    item = state["videos"].get(video_id(args.video))
    if not item:
        raise SystemExit("Unknown video")
    folder = completed_folder(item)
    result = {
        "videoId": item["videoId"],
        "outputComplete": bool(folder),
        "taskDir": str(folder) if folder else None,
        "indexContainsVideo": index_contains(item),
    }
    result["complete"] = result["outputComplete"] and result["indexContainsVideo"]
    print_json(result)
    raise SystemExit(0 if result["complete"] else 1)


def command_lock(args: argparse.Namespace) -> None:
    key = video_id(args.video)
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    path = LOCK_DIR / f"{key}.lock"
    if path.exists():
        try:
            created = dt.datetime.fromisoformat(path.read_text(encoding="utf-8").strip())
            age = (dt.datetime.now(dt.timezone.utc) - created).total_seconds() / 60
        except (ValueError, OSError):
            age = 0
        if age < args.stale_minutes:
            print(f"Lock already held: {path}", file=sys.stderr)
            raise SystemExit(1)
    path.write_text(now() + "\n", encoding="utf-8")
    print(path)


def command_unlock(args: argparse.Namespace) -> None:
    path = LOCK_DIR / f"{video_id(args.video)}.lock"
    if path.exists():
        path.unlink()
    print(path)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(required=True)
    upsert = sub.add_parser("upsert")
    upsert.add_argument("--url", required=True)
    upsert.add_argument("--subject", required=True)
    upsert.add_argument("--class-date", required=True)
    upsert.add_argument("--archive-date-raw", required=True)
    upsert.add_argument("--archive-url", required=True)
    upsert.set_defaults(func=command_upsert)
    set_status = sub.add_parser("set")
    set_status.add_argument("--video", required=True)
    set_status.add_argument("--status", required=True)
    set_status.add_argument("--worker-task-id")
    set_status.add_argument("--task-dir")
    set_status.add_argument("--commit")
    set_status.add_argument("--message")
    set_status.set_defaults(func=command_set)
    status = sub.add_parser("status")
    status.add_argument("--video")
    status.add_argument("--active", action="store_true")
    status.set_defaults(func=command_status)
    verify = sub.add_parser("verify")
    verify.add_argument("--video", required=True)
    verify.set_defaults(func=command_verify)
    lock = sub.add_parser("lock")
    lock.add_argument("--video", required=True)
    lock.add_argument("--stale-minutes", type=int, default=360)
    lock.set_defaults(func=command_lock)
    unlock = sub.add_parser("unlock")
    unlock.add_argument("--video", required=True)
    unlock.set_defaults(func=command_unlock)
    return root


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
