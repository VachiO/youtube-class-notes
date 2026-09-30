# Scheduled processing and public status

Effective 30 September 2026, first processing run at 16:00 Asia/Bangkok.
Run hourly at 16:00, 17:00, 18:00, 19:00, 20:00, 21:00, 22:00 and 23:00
Thai time. Each run is a separate chat and may process at most ONE video.
This allows up to eight videos per day without violating the one-video-per-chat rule.
Use gpt-5.6-sol with high reasoning. The local machine and Codex must be running.

## Source of truth and coverage

Run `python scripts/processing_status.py scan` at the start of EVERY run.
This reads the live archive navigation, every linked date page, and YouTube titles
for every distinct embedded video. Only the seven allowed courses count. Match
the class date in the title to the archive page, then compare against the LIVE
published site index and nonempty published summary files, by YouTube video ID.
Never claim up-to-date from local files, Git, the generated site index alone,
or lifecycle state. A failed page/title request invalidates the fresh check:
retain the last complete snapshot, publish the scan error, and report the blocker.
Never replace an incomplete scan with a zero backlog or guess course identities.

`data/processing-status.json` is the public complete-scan snapshot and attempt
journal. Preserve its existing attempts; never overwrite it from a stale checkout.
Before editing, fetch origin/main and reconcile this file with the newest pushed
version. If both have new attempts, merge by immutable attempt ID, keeping final
outcomes over running entries; stop on conflicting final outcomes.

## Each scheduled run

1. Follow AGENTS.md and PROCESS.md; run the environment check. Read this file,
   automation memory, local lifecycle state and the public journal.
2. Resolve any previous running attempt before starting another. Check its worker
   and outputs. A genuinely active worker prevents a new attempt. A confirmed
   interrupted/abandoned attempt is finalized failed, including download failure,
   inaccessible captions or a model interruption. Do not silently erase it.
   If completed outputs were already pushed, verify their publication and finish
   that attempt succeeded. A deployment delay remains running and is retried on
   the next run; never process the lecture again just because Pages is delayed.
3. Perform the live scan. Reconcile ALL already-complete local lifecycle entries
   against verified published outputs before selecting work. This reconciliation
   does not consume the processing slot or create an attempt. Never let an old
   discovered/failed state for an already-published video consume today's slot.
4. Choose the oldest class date in scan.remaining, then subject/video ID, excluding
   permanently blocked transcripts and non-transient failures. Retry transient
   failures at most three attempts per video, using journal and lifecycle history.
   If all are blocked, publish the backlog and report why; do not claim zero.
5. Upsert the selected video through scripts/automation_state.py with the exact
   live-validated identity and acquire its per-video lock. Immediately BEFORE
   transcript retrieval or lecture processing, run:
   `python scripts/processing_status.py start --video VIDEO_ID`
   Save the returned attempt ID. Publish data/processing-status.json in a scoped
   commit and push so an interruption still leaves the attempt visible.
   If that push fails, finalize failed locally and stop; retain it for publication
   recovery on the next run. Do not start another clip in this chat.
6. Process this one video end-to-end, preserving detail and auditing completeness.
   Update course notes, exam/events, site index and project memory as AGENTS.md
   requires. Commit/push only this task's changes, preserving unrelated dirty work.
   Use a temporary Git index based on origin/main if the dirty local branch is
   behind; never force-push, reset, discard, or include unrelated user edits.
7. After verification and publication of the lecture, run:
   `python scripts/processing_status.py finish --attempt ATTEMPT_ID --status succeeded`
   This rechecks the live archive and published output. If publication is delayed,
   retain running and report the delay; retry finalization without processing again.
   On actual processing failure/blocked captions, run the same finish command with
   `--status failed`, update lifecycle status and processing notes with the reason.
8. Release the lock in final cleanup. Publish data/processing-status.json after
   success, failure, scan failure, and no-work runs. Verify the LIVE status JSON
   and report any deployment delay. Persist the attempt even on unexpected errors.

## Counting

- Counts start with this journal; do not invent historical counts from git commits,
  existing output folders, completed lifecycle entries or old attempt counters.
- A new start records one actual attempt. Repeated finalization is idempotent.
- A retry of the same video is another attempt because it consumes processing again.
- Assign attempts to their START date in Asia/Bangkok, including cross-midnight work.
- Total = succeeded + failed + running. When none is running: total = succeeded + failed.
- Scanning, reconciliation, idle runs and waiting for publication do not count as clips.
- The page reports attempt counts, NOT token quantities, costs, or total scanner usage.
- Show snapshot timestamps and warnings on incomplete/stale scans or load failures.
  Never show yesterday's counts as today's counts; use the browser's current Thai date.

## Verification

`python tests/test_processing_status.py`

`node tests/test_processing_status_ui.js`
