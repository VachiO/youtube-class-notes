# AGENTS.md

## Project Purpose

This project turns one YouTube class recording into Thai study files.

Before processing on any machine, follow `PROCESS.md` and run:

```text
python scripts/check_environment.py
```

If the environment check fails, fix the setup before processing.

The normal user command is:

```text
process <youtube-url> as "<subject>" from <dd.mm.yyyy>
```

Example:

```text
process https://www.youtube.com/watch?v=fzGMIZ-5XuU as "POL3179" from 01.06.2026
```

When this command is used, do the work end to end unless blocked by YouTube access, missing dependencies, or a transcript that cannot be obtained.

## Output Layout

Create outputs under:

```text
classes/<SUBJECT>/<YYYY-MM-DD>/video-XX/
```

If the same URL is processed again for the same subject and date, create a new version instead of overwriting:

```text
classes/<SUBJECT>/<YYYY-MM-DD>/video-XX-v2/
classes/<SUBJECT>/<YYYY-MM-DD>/video-XX-v3/
```

Required files for each video:

```text
source.txt
transcript-raw.txt
transcript-original.txt
transcript-revised.txt
lecture-summary.txt
processing-notes.txt
chunks/
```

Use meaningful chunk names:

```text
chunks/original-chunk-001.txt
chunks/revised-chunk-001.txt
chunks/summary-chunk-001.txt
```

## Processing Steps

1. Parse the URL, subject, and date from the user's command.
2. Convert `dd.mm.yyyy` to `yyyy-mm-dd`.
3. Run `scripts/init_task.py` to create the correct target folder and write `source.txt`.
4. Run `scripts/get_youtube_transcript.py` to fetch the transcript.
5. Save the raw transcript output to `transcript-raw.txt`.
6. Save the readable transcript, with timestamps removed, to `transcript-original.txt`.
7. Always split `transcript-original.txt` into chunks before LLM revision.
8. Revise every chunk using `prompts/revise-transcript.md`.
9. Combine revised chunks into `transcript-revised.txt`.
10. Summarize from `transcript-revised.txt`, split into chunks when needed, using `prompts/summarize-lecture.md`.
11. Combine summary chunks into `lecture-summary.txt`.
12. Review the final summary. If it is too short or drops important class information, expand it before finishing.
13. Update or create `readme-<SUBJECT>.md` with course logistics only, such as class schedule, quiz dates, score rules, submission instructions, and required materials. Do not copy ordinary lecture content into this file.
14. Update or create `hint-<SUBJECT>.md` with exam hints only, such as likely exam topics, teacher statements about what will be tested, question formats, required memorization, and concrete preparation instructions.
15. Update `processing-notes.txt` with what was done, what tools worked, and any problems.
16. Run `scripts/build_site_index.py` so the new processed video appears on the static page.

## Transcript Revision Rules

`transcript-revised.txt` is not a summary.

The goal is to correct Thai YouTube speech-to-text errors while preserving the original lecture as closely as possible.

Rules:

- Keep the same sequence as the original transcript.
- Keep the same meaning.
- Keep the amount of detail.
- Keep line breaks reasonably close to the chunk source when possible.
- Correct obvious speech-to-text mistakes using context.
- Preserve technical terms in English when they are useful for study or search, such as `LLM`, `API`, `database`, `policy`, `consent`, `ChatGPT`.
- Do not polish the lecture into an essay.
- Do not remove side comments that contain class content, university agenda, assignments, quizzes, deadlines, or useful background knowledge.
- Remove or reduce only clearly empty filler when it does not carry meaning, such as repeated "เน€เธญเนเธญ", "เธญเนเธฒ", "เนเธญเน€เธ", or repeated false starts.

## Lecture Summary Rules

`lecture-summary.txt` must be in Thai.

This is a detailed lecture-note style summary, not a short abstract.

The minimum length is 2000 words. If the class contains more information, write more. Never compress only because the output is already long.

Think of the summary as dropping only unnecessary spoken filler from the revised transcript. The user did not attend the class, so the summary must preserve enough detail to understand the lecture, class experience, important side knowledge, and all practical announcements.

Must include:

- Main lecture content.
- Examples explained by the teacher.
- Side knowledge and background comments.
- Class or university agenda.
- Assignments, quizzes, meetings, training, deadlines, appointments, and instructions.
- Any detail that may affect exams, homework, attendance, or understanding the course.

Graduation-oriented course context:

- Assume the course is designed so the teacher is trying to help students finish the course and pass 100%.
- Treat exam hints, exam scope, likely exam topics, reading instructions, "this will be on the exam", "read this part", "remember this", "I will ask this", quiz details, scoring rules, grading opportunities, and attendance or training requirements as critical information.
- Mark these critical items clearly in the summary with `⚠️` or another obvious marker, while keeping the summary mostly continuous prose.
- Do not shorten these critical items aggressively. Preserve the teacher's exact meaning, concrete conditions, dates, scores, required actions, and consequences.
- When the teacher explains an agenda item that affects grades, such as training, meetings, assignments, quizzes, attendance, or extra credit, state it directly and concretely. Do not soften it into vague language.
- If the teacher's wording is important, quote a short phrase from the teacher and then explain it in Thai.

Style:

- Thai prose.
- Long continuous lecture-note style.
- Do not use local Thai word segmentation, tokenization, or artificial spaces between Thai words to satisfy word-count checks. Keep the summary in natural Thai prose like normal study notes.
- Paragraphs are allowed.
- When an English technical term or proper concept is useful to keep, write the English term followed by a Thai explanation in parentheses on first use, such as `Democracy (ประชาธิปไตย)`, `Federalism (สหพันธรัฐนิยม)`, or `impeachment (กระบวนการถอดถอน)`.
- After the first use, use either the English term, the Thai term, or both, depending on which is clearest in context.
- Avoid heavy re-organization.
- Preserve the lecture order as much as possible.
- Do not use many headings or bullets unless the source lecture clearly shifts topics and doing so prevents confusion.

## Quality Checks

Before final response, check:

- `transcript-raw.txt` exists.
- `transcript-original.txt` exists and is not empty.
- `transcript-revised.txt` exists and is not a summary.
- `lecture-summary.txt` exists and is at least 2000 words unless the transcript itself is unusually short and this is documented.
- No existing video folder was overwritten.
- `processing-notes.txt` records blockers and assumptions.
- `readme-<SUBJECT>.md` contains relevant course logistics from the new summary.
- `hint-<SUBJECT>.md` contains relevant exam hints from the new summary.
- `data/site-index.json` includes the newly processed video unless processing stopped before a usable summary existed.

If YouTube blocks transcript access, stop after creating the task folder and record the blocker in `processing-notes.txt`.



