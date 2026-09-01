#!/usr/bin/env python3
"""Validate that a YouTube title matches the requested class identity."""

from __future__ import annotations

import datetime as dt
import json
import re
import urllib.parse
import urllib.request


def fetch_youtube_title(url: str) -> str:
    endpoint = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"url": url, "format": "json"}
    )
    request = urllib.request.Request(endpoint, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            title = json.load(response).get("title", "").strip()
    except Exception as exc:
        raise ValueError(f"Could not read YouTube title: {exc}") from exc
    if not title:
        raise ValueError("YouTube returned an empty title")
    return title


def title_class_date(title: str) -> str | None:
    match = re.search(r"(?<!\d)(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{2,4})(?!\d)", title)
    if not match:
        return None
    day, month, year = map(int, match.groups())
    if year < 100:
        year += 2500
    if year >= 2400:
        year -= 543
    try:
        return dt.date(year, month, day).isoformat()
    except ValueError:
        return None


def validate_title_identity(title: str, subject: str, class_date: str) -> None:
    expected_subject = re.sub(r"\s+", "", subject).upper()
    title_subject = re.search(r"\bPOL\s*(\d{4})\b", title, re.IGNORECASE)
    actual_subject = f"POL{title_subject.group(1)}" if title_subject else None
    actual_date = title_class_date(title)
    errors = []
    if actual_subject != expected_subject:
        errors.append(f"subject is {actual_subject or 'not stated'}, expected {expected_subject}")
    if actual_date != class_date:
        errors.append(f"date is {actual_date or 'not stated'}, expected {class_date}")
    if errors:
        raise ValueError(f"YouTube title mismatch: {title!r}; " + "; ".join(errors))


def validate_video_identity(url: str, subject: str, class_date: str) -> str:
    title = fetch_youtube_title(url)
    validate_title_identity(title, subject, class_date)
    return title
