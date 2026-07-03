#!/usr/bin/env python3
"""Split a transcript-like text file into numbered chunk files."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def split_units(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) > 1:
        return paragraphs
    return [line.strip() for line in text.splitlines() if line.strip()]


def chunk_text(text: str, max_chars: int) -> list[str]:
    units = split_units(text)
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for unit in units:
        separator_len = 2 if current else 0
        if current and current_len + separator_len + len(unit) > max_chars:
            chunks.append("\n\n".join(current).strip())
            current = [unit]
            current_len = len(unit)
        else:
            current.append(unit)
            current_len += separator_len + len(unit)
    if current:
        chunks.append("\n\n".join(current).strip())
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--max-chars", type=int, default=12000)
    args = parser.parse_args()

    source = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    text = source.read_text(encoding="utf-8", errors="replace").strip()
    chunks = chunk_text(text, args.max_chars)
    width = max(3, len(str(len(chunks))))
    for index, chunk in enumerate(chunks, 1):
        path = output_dir / f"{args.prefix}-{index:0{width}d}.txt"
        path.write_text(chunk.strip() + "\n", encoding="utf-8")
        print(path)


if __name__ == "__main__":
    main()

