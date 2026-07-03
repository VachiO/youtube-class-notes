# YouTube Class Notes Workflow

Use this project from Codex CLI.

Normal command:

```text
process <youtube-url> as "<subject>" from <dd.mm.yyyy>
```

Example:

```text
process https://www.youtube.com/watch?v=fzGMIZ-5XuU as "POL3179" from 01.06.2026
```

Codex will create:

```text
classes/<SUBJECT>/<YYYY-MM-DD>/video-XX/
```

Each video folder contains:

```text
source.txt
transcript-raw.txt
transcript-original.txt
transcript-revised.txt
lecture-summary.txt
processing-notes.txt
chunks/
```

The workflow is intentionally file-based so every run can be debugged and fine-tuned.

