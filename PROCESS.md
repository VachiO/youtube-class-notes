# Processing Workflow

This file is the canonical workflow for every machine that clones this repo.

## One-time setup on a new machine

Use Python 3.11 or newer.

```powershell
git clone https://github.com/VachiO/youtube-class-notes.git
cd youtube-class-notes
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts\check_environment.py
```

On macOS or Linux, activate the virtual environment with:

```bash
source .venv/bin/activate
```

The check command must pass before processing a video.

## Normal process command

When the user says:

```text
process <youtube-url> as "<subject>" from <dd.mm.yyyy>
```

For เทอม 1/2569, process only these `รายวิชาในเทอม 1/2569` by default:

```text
POL3128
POL1101
POL2129
POL2107
POL3179
POL2100
POL2102
```

If the requested subject is not in this list, ask the user to confirm whether the subject is correct before continuing.

Process the video end to end using the same repo scripts and prompts:

```powershell
python scripts\init_task.py --url "<youtube-url>" --subject "<subject>" --date "<dd.mm.yyyy>"
python scripts\get_youtube_transcript.py --url "<youtube-url>" --task-dir "<task-dir>"
python scripts\split_text.py --input "<task-dir>\transcript-original.txt" --output-dir "<task-dir>\chunks" --prefix original-chunk --max-chars 9000
```

Then revise every `chunks/original-chunk-*.txt` with `prompts/revise-transcript.md`, write matching `chunks/revised-chunk-*.txt`, and combine them into `transcript-revised.txt`.

Then summarize from `transcript-revised.txt` with `prompts/summarize-lecture.md`, write `chunks/summary-chunk-*.txt`, and combine them into `lecture-summary.txt`.

Audit the combined `lecture-summary.txt` against `transcript-revised.txt` using `prompts/audit-summary-completeness.md`. Merge all recovered details into their appropriate positions and repeat the audit until no substantial omissions remain. Give special attention to side knowledge, stories, personal experiences, and meaningful teacher digressions; these are valuable class content and must not be discarded merely because they are outside the main topic.

Finally update:

- `readme-<SUBJECT>.md` with course logistics only.
- `hint-<SUBJECT>.md` with exam hints only.
- `processing-notes.txt` with tools, blockers, assumptions, and quality checks.
- `data/site-index.json` by running `python scripts\build_site_index.py`.

## Rules that must stay identical

- Keep the output folder format: `classes/<SUBJECT>/<YYYY-MM-DD>/video-XX/`.
- Never overwrite an existing processed video folder. If the same URL is processed again, create `video-XX-v2`, `video-XX-v3`, and so on.
- Always split `transcript-original.txt` before transcript revision.
- `transcript-revised.txt` is corrected transcript, not summary.
- `lecture-summary.txt` is Thai lecture-note prose, not a short abstract.
- Keep summaries as natural Thai prose. Do not run Thai tokenizers, local word segmentation, or artificial spacing to inflate word counts.
- Keep highlight markers such as `⚠️` for exam, score, quiz, deadline, required action, and teacher emphasis.
- Do not copy ordinary lecture content into `readme-<SUBJECT>.md`; keep it for logistics.
- Do not copy general lecture content into `hint-<SUBJECT>.md`; keep it for exam hints and preparation.

## Before final response

Run:

```powershell
python scripts\check_environment.py
python scripts\build_site_index.py
git status --short
```

Then check that the processed task folder contains:

- `source.txt`
- `transcript-raw.txt`
- `transcript-original.txt`
- `transcript-revised.txt`
- `lecture-summary.txt`
- `processing-notes.txt`
- `chunks/`
