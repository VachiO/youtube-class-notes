# Revise Transcript Prompt

You are correcting a Thai YouTube auto-transcript of a university class recording.

This task is transcript correction, not summarization.

Input:

```text
{{TRANSCRIPT_CHUNK}}
```

Output only the corrected transcript text.

Rules:

- Keep the original lecture order.
- Keep the meaning and amount of information.
- Keep line breaks close to the source when possible.
- Correct obvious Thai speech-to-text errors using context.
- Preserve technical terms in English when they are useful, such as `LLM`, `API`, `database`, `ChatGPT`, `policy`, `consent`.
- Do not translate technical English terms into awkward Thai if the class likely used the English term.
- Do not add new content that is not supported by the transcript.
- Do not summarize.
- Do not turn the transcript into polished essay prose.
- Keep side knowledge, teacher comments, announcements, deadlines, quiz information, assignment details, meeting notices, training notices, and university agenda.
- Remove only meaningless filler or repeated false starts when they do not affect meaning.

Example:

```text
ผมชอบ แคทเอพีที เพราะ มันเป็น llm ที่ดี
```

should become:

```text
ผมชอบ ChatGPT เพราะมันเป็น LLM ที่ดี
```

