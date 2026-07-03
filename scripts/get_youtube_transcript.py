#!/usr/bin/env python3
"""Fetch a YouTube transcript and write raw/readable transcript files."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path


LANGUAGES = ("th", "th-TH", "th-Hans", "th-Hant", "en")


def video_id_from_url(url: str) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.netloc.endswith("youtu.be"):
        video_id = parsed.path.strip("/").split("/", 1)[0]
    else:
        video_id = urllib.parse.parse_qs(parsed.query).get("v", [""])[0]
    if not re.fullmatch(r"[\w-]{11}", video_id):
        raise SystemExit(f"Cannot find YouTube video id in URL: {url}")
    return video_id


def clean_text(text: str) -> str:
    text = html.unescape(text)
    text = fix_thai_mojibake(text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("\ufeff", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def thai_score(text: str) -> int:
    return sum(1 for char in text if "\u0e00" <= char <= "\u0e7f")


def mojibake_score(text: str) -> int:
    return text.count("เธ") + text.count("เน€") + text.count("เน") + text.count("เน")


def fix_thai_mojibake(text: str) -> str:
    """Repair Thai UTF-8 text that was accidentally decoded as CP874."""
    if mojibake_score(text) < 2:
        return text
    try:
        fixed = text.encode("cp874").decode("utf-8")
    except UnicodeError:
        return text
    return fixed if mojibake_score(fixed) < mojibake_score(text) else text

def vtt_to_text(vtt: str) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    for raw_line in vtt.splitlines():
        line = raw_line.strip()
        if not line or line == "WEBVTT" or line.startswith("Kind:") or line.startswith("Language:"):
            continue
        if "-->" in line:
            continue
        if re.fullmatch(r"\d+", line):
            continue
        line = re.sub(r"<\d{2}:\d{2}:\d{2}\.\d{3}>", "", line)
        line = clean_text(line)
        if line and line not in seen:
            lines.append(line)
            seen.add(line)
    return "\n".join(lines).strip()


def append_note(task_dir: Path, text: str) -> None:
    notes = task_dir / "processing-notes.txt"
    with notes.open("a", encoding="utf-8") as fh:
        fh.write(text.rstrip() + "\n")


def fetch_with_ytdlp(url: str, task_dir: Path) -> tuple[str, str] | None:
    exe = shutil.which("yt-dlp")
    if exe:
        runner = [exe]
    else:
        try:
            import yt_dlp  # type: ignore  # noqa: F401
        except Exception:
            append_note(task_dir, "yt-dlp: not installed")
            return None
        runner = [sys.executable, "-m", "yt_dlp"]

    with tempfile.TemporaryDirectory() as temp_name:
        temp_dir = Path(temp_name)
        output_template = str(temp_dir / "%(id)s.%(ext)s")
        cmd = [
            *runner,
            "--skip-download",
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            ",".join(LANGUAGES),
            "--sub-format",
            "vtt",
            "--output",
            output_template,
            url,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        append_note(task_dir, f"yt-dlp exit code: {result.returncode}")
        if result.stderr.strip():
            append_note(task_dir, "yt-dlp stderr:\n" + result.stderr.strip())
        files = sorted(temp_dir.glob("*.vtt"))
        if not files:
            return None
        preferred = sorted(files, key=lambda p: (not any(lang in p.name for lang in LANGUAGES), p.name))[0]
        raw = preferred.read_text(encoding="utf-8", errors="replace")
        text = vtt_to_text(raw)
        if text:
            append_note(task_dir, f"Transcript method: yt-dlp ({preferred.name})")
            return raw, text
    return None


def fetch_with_python_api(video_id: str, task_dir: Path) -> tuple[str, str] | None:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
    except Exception as exc:
        append_note(task_dir, f"youtube-transcript-api: not available ({exc})")
        return None

    attempts = []
    api = YouTubeTranscriptApi
    if hasattr(api, "get_transcript"):
        attempts.append(lambda: api.get_transcript(video_id, languages=list(LANGUAGES)))
    attempts.append(lambda: api().fetch(video_id, languages=list(LANGUAGES)))

    for attempt in attempts:
        try:
            transcript = attempt()
            rows = []
            for item in transcript:
                text = item["text"] if isinstance(item, dict) else getattr(item, "text", "")
                rows.append(clean_text(str(text)))
            rows = [row for row in rows if row]
            if rows:
                raw = json.dumps(transcript, ensure_ascii=False, default=lambda obj: getattr(obj, "__dict__", str(obj)), indent=2)
                append_note(task_dir, "Transcript method: youtube-transcript-api")
                return raw, "\n".join(rows)
        except Exception as exc:
            append_note(task_dir, f"youtube-transcript-api attempt failed: {exc}")
    return None


def extract_player_response(page: str) -> dict | None:
    marker = "ytInitialPlayerResponse"
    start = page.find(marker)
    if start == -1:
        return None
    brace_start = page.find("{", start)
    if brace_start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(brace_start, len(page)):
        char = page[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return json.loads(page[brace_start : index + 1])
    return None


def fetch_url(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "th,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def fetch_with_timedtext(video_id: str, task_dir: Path) -> tuple[str, str] | None:
    try:
        page = fetch_url(f"https://www.youtube.com/watch?v={video_id}")
        data = extract_player_response(page)
        tracks = (
            data.get("captions", {})
            .get("playerCaptionsTracklistRenderer", {})
            .get("captionTracks", [])
            if data
            else []
        )
        if not tracks:
            append_note(task_dir, "timedtext: no caption tracks found")
            return None

        def score(track: dict) -> tuple[int, str]:
            language = track.get("languageCode", "")
            return (0 if language.startswith("th") else 1, language)

        track = sorted(tracks, key=score)[0]
        base_url = track["baseUrl"]
        separator = "&" if "?" in base_url else "?"
        raw = fetch_url(base_url + separator + "fmt=json3")
        payload = json.loads(raw)
        rows = []
        for event in payload.get("events", []):
            parts = event.get("segs", [])
            text = "".join(part.get("utf8", "") for part in parts)
            text = clean_text(text)
            if text:
                rows.append(text)
        if rows:
            append_note(task_dir, f"Transcript method: YouTube timedtext ({track.get('languageCode', 'unknown')})")
            return raw, "\n".join(rows)
    except Exception as exc:
        append_note(task_dir, f"timedtext failed: {exc}")
    return None


def write_outputs(task_dir: Path, raw: str, text: str) -> None:
    (task_dir / "transcript-raw.txt").write_text(raw.strip() + "\n", encoding="utf-8")
    (task_dir / "transcript-original.txt").write_text(clean_text(text) + "\n", encoding="utf-8")
    append_note(task_dir, f"Raw transcript characters: {len(raw)}")
    append_note(task_dir, f"Original transcript characters: {len(text)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True)
    parser.add_argument("--task-dir", required=True)
    args = parser.parse_args()

    task_dir = Path(args.task_dir).resolve()
    task_dir.mkdir(parents=True, exist_ok=True)
    video_id = video_id_from_url(args.url)
    append_note(task_dir, f"Video id: {video_id}")

    for fetcher in (
        lambda: fetch_with_ytdlp(args.url, task_dir),
        lambda: fetch_with_python_api(video_id, task_dir),
        lambda: fetch_with_timedtext(video_id, task_dir),
    ):
        result = fetcher()
        if result:
            raw, text = result
            write_outputs(task_dir, raw, text)
            print(task_dir / "transcript-original.txt")
            return

    append_note(task_dir, "Status: failed to fetch transcript")
    print("Failed to fetch transcript", file=sys.stderr)
    raise SystemExit(1)


if __name__ == "__main__":
    main()





