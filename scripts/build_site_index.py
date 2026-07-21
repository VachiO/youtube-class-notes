#!/usr/bin/env python3
"""Build the static site index from processed class folders."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLASSES_DIR = PROJECT_ROOT / "classes"
DATA_DIR = PROJECT_ROOT / "data"
COURSE_META_PATH = DATA_DIR / "course-meta.json"
SITE_INDEX_PATH = DATA_DIR / "site-index.json"

DEFAULT_META: dict[str, dict[str, Any]] = {
    "POL1101": {
        "title": "การเมืองและการปกครองของไทย",
        "order": 1101,
    },
    "POL2100": {"title": "POL2100", "order": 2100},
    "POL2102": {
        "title": "หลักรัฐธรรมนูญและสถาบันทางการเมือง",
        "order": 2102,
    },
    "POL2107": {"title": "การเมืองเปรียบเทียบ", "order": 2107},
    "POL2129": {
        "title": "รัฐและประชาสังคมในระบบการเมือง",
        "order": 2129,
    },
    "POL3179": {"title": "การเมืองในอเมริกา", "order": 3179},
}

IMPORTANT_TERMS = [
    "⚠️",
    "ข้อสอบ",
    "สอบ",
    "คะแนน",
    "quiz",
    "ควิส",
    "ส่ง",
    "กำหนด",
    "deadline",
    "อ่าน",
    "จำ",
    "สอบซ่อม",
    "final",
    "midterm",
]

THAI_WEEKDAYS = [
    "วันจันทร์",
    "วันอังคาร",
    "วันพุธ",
    "วันพฤหัสบดี",
    "วันศุกร์",
    "วันเสาร์",
    "วันอาทิตย์",
]

THAI_MONTHS = [
    "",
    "มกราคม",
    "กุมภาพันธ์",
    "มีนาคม",
    "เมษายน",
    "พฤษภาคม",
    "มิถุนายน",
    "กรกฎาคม",
    "สิงหาคม",
    "กันยายน",
    "ตุลาคม",
    "พฤศจิกายน",
    "ธันวาคม",
]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def rel(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def read_source(source_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not source_path.exists():
        return values
    for line in source_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip().lower()] = value.strip()
    return values


def parse_video_name(name: str) -> tuple[int, int]:
    match = re.fullmatch(r"video-(\d{2})(?:-v(\d+))?", name)
    if not match:
        return (999, 1)
    return (int(match.group(1)), int(match.group(2) or "1"))


def thai_date_label(value: str) -> str:
    date = dt.date.fromisoformat(value)
    return f"{THAI_WEEKDAYS[date.weekday()]}ที่ {date.day} {THAI_MONTHS[date.month]} {date.year + 543}"


def first_paragraph(text: str) -> str:
    text = text.lstrip("\ufeff")
    paragraphs = [part.strip() for part in re.split(r"\r?\n\s*\r?\n", text) if part.strip()]
    if not paragraphs:
        return ""
    paragraph = re.sub(r"\s+", " ", paragraphs[0])
    return paragraph[:220] + ("..." if len(paragraph) > 220 else "")


def count_important(paragraphs: list[str]) -> int:
    return sum(
        1
        for paragraph in paragraphs
        if any(term.lower() in paragraph.lower() for term in IMPORTANT_TERMS)
    )


def ensure_course_meta(subjects: set[str]) -> dict[str, dict[str, Any]]:
    raw_meta = read_json(COURSE_META_PATH)
    meta: dict[str, dict[str, Any]] = {}

    for subject in sorted(subjects):
        base = DEFAULT_META.get(subject, {"title": subject, "order": 9999})
        custom = raw_meta.get(subject, {})
        meta[subject] = {**base, **custom}

    if raw_meta != meta:
        write_json(COURSE_META_PATH, meta)

    return meta


def collect_lectures(meta: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    lectures: list[dict[str, Any]] = []
    if not CLASSES_DIR.exists():
        return lectures

    for subject_dir in sorted(path for path in CLASSES_DIR.iterdir() if path.is_dir()):
        subject = subject_dir.name
        subject_meta = meta.get(subject, {"title": subject, "order": 9999})

        for date_dir in sorted(path for path in subject_dir.iterdir() if path.is_dir()):
            try:
                dt.date.fromisoformat(date_dir.name)
            except ValueError:
                continue

            for video_dir in sorted((p for p in date_dir.iterdir() if p.is_dir()), key=lambda p: parse_video_name(p.name)):
                if not re.fullmatch(r"video-\d{2}(?:-v\d+)?", video_dir.name):
                    continue
                summary_path = video_dir / "lecture-summary.txt"
                if not summary_path.exists() or summary_path.stat().st_size == 0:
                    continue

                text = summary_path.read_text(encoding="utf-8", errors="replace").strip()
                paragraphs = [part.strip() for part in re.split(r"\r?\n\s*\r?\n", text) if part.strip()]
                video_number, version = parse_video_name(video_dir.name)
                source_values = read_source(video_dir / "source.txt")
                date_value = date_dir.name

                lectures.append(
                    {
                        "id": f"{subject}-{date_value}-{video_dir.name}",
                        "subject": subject,
                        "courseTitle": subject_meta["title"],
                        "noExam": bool(subject_meta.get("noExam", False)),
                        "date": date_value,
                        "dateLabelTh": thai_date_label(date_value),
                        "buddhistYear": int(date_value[:4]) + 543,
                        "video": video_dir.name,
                        "videoNumber": video_number,
                        "version": version,
                        "summaryPath": rel(summary_path),
                        "sourcePath": rel(video_dir / "source.txt"),
                        "transcriptPath": rel(video_dir / "transcript-revised.txt"),
                        "readmePath": f"readme-{subject}.md",
                        "hintPath": f"hint-{subject}.md",
                        "sourceUrl": source_values.get("url", ""),
                        "paragraphCount": len(paragraphs),
                        "wordCount": len(re.findall(r"\S+", text)),
                        "importantCount": count_important(paragraphs),
                        "excerpt": first_paragraph(text),
                    }
                )

    return sorted(lectures, key=lambda item: (item["date"], item["subject"], item["video"]), reverse=True)


def build_subjects(lectures: list[dict[str, Any]], meta: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    subjects: list[dict[str, Any]] = []
    for subject in sorted({lecture["subject"] for lecture in lectures}):
        subject_lectures = [lecture for lecture in lectures if lecture["subject"] == subject]
        subject_meta = meta.get(subject, {"title": subject, "order": 9999})
        subjects.append(
            {
                "code": subject,
                "title": subject_meta["title"],
                "order": subject_meta.get("order", 9999),
                "noExam": bool(subject_meta.get("noExam", False)),
                "lectureCount": len(subject_lectures),
                "dates": sorted({lecture["date"] for lecture in subject_lectures}, reverse=True),
                "readmePath": f"readme-{subject}.md",
                "hintPath": f"hint-{subject}.md",
            }
        )
    return sorted(subjects, key=lambda item: (item["order"], item["code"]))


def main() -> None:
    subjects = {path.name for path in CLASSES_DIR.iterdir() if path.is_dir()} if CLASSES_DIR.exists() else set()
    meta = ensure_course_meta(subjects)
    lectures = collect_lectures(meta)
    site_index = {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "totalLectures": len(lectures),
        "subjects": build_subjects(lectures, meta),
        "lectures": lectures,
    }
    write_json(SITE_INDEX_PATH, site_index)
    print(f"Wrote {rel(SITE_INDEX_PATH)} with {len(lectures)} lectures")


if __name__ == "__main__":
    main()
