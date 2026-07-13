# Summarize Lecture Prompt

You are writing detailed Thai lecture notes from a corrected transcript of a university class recording.

This is not a short summary. The reader did not attend the class.

Input:

```text
{{REVISED_TRANSCRIPT_CHUNK_OR_FULL_TEXT}}
```

Output only Thai lecture-note prose.

Requirements:

- Write in Thai.
- Preserve the lecture order as much as possible.
- Think of the task as removing unnecessary spoken filler, not compressing the class.
- Include main class content.
- Include examples and explanations.
- Include side knowledge, stories, anecdotes, personal experiences, background comments, and meaningful digressions from the teacher.
- Treat the teacher's side knowledge, stories, and off-topic discussion as valuable parts of the class experience. Preserve them unless they are clearly empty filler with no informational, explanatory, contextual, or practical value.
- Include class agenda, university agenda, meetings, training, appointments, assignments, deadlines, quizzes, and practical instructions.
- Include anything that may affect exams, homework, attendance, or understanding the subject.
- Assume this curriculum is designed so the teacher is trying to help students finish the course and pass 100%.
- Treat exam hints, exam scope, likely exam topics, reading instructions, quiz details, scoring rules, grading opportunities, attendance rules, training, meetings, assignments, and deadlines as critical information.
- Mark critical exam/grading/agenda information clearly with `⚠️` or another obvious marker, while keeping the notes mostly continuous prose.
- Do not shorten critical exam/grading/agenda information aggressively. Preserve exact conditions, dates, scores, required actions, and consequences.
- For grade-related agenda items, state the practical meaning directly. For example, do not reduce "ไปอบรมแล้วได้คะแนน" into vague wording like "อาจเป็นผลดีถ้าไปอบรม"; say clearly that attending gives points if the transcript supports that.
- When the teacher's wording matters, quote a short phrase from the teacher and then explain it in Thai.
- Use continuous lecture-note prose with paragraphs.
- When keeping an English technical term or proper concept, add Thai in parentheses on first use, such as `Democracy (ประชาธิปไตย)`, `Federalism (สหพันธรัฐนิยม)`, or `impeachment (กระบวนการถอดถอน)`.
- After the first use, choose the English term, Thai term, or both based on clarity and natural Thai lecture-note style.
- Avoid heavy reorganization.
- Avoid bullet lists unless the lecture itself clearly lists items and bullets make the content clearer.
- Do not invent facts beyond the transcript.

## Completeness and Length

Completeness is more important than conciseness.

This task is an edited lecture record, not a conventional summary. Preserve every substantive information unit from the source, including explanations, arguments, definitions, examples, comparisons, names, events, background knowledge, teacher opinions, cautions, questions, answers, stories, personal experiences, meaningful digressions, and practical announcements.

Use the following retention rules:

- Remove only empty speech filler, accidental repetition, and false starts that add no meaning.
- Do not remove a detail merely because it seems minor or is not part of the main topic.
- Do not merge several distinct explanations into one general sentence.
- Preserve each example and explain what point the teacher used it to demonstrate.
- Preserve chains of reasoning, including causes, effects, contrasts, exceptions, and conditions.
- Preserve repeated explanations when the repetition adds a new example, emphasis, clarification, or exam implication.
- Preserve side knowledge, stories, anecdotes, personal experiences, and off-topic discussion when they reveal context, explain the teacher's thinking, illustrate a concept, describe university or social life, or add useful general knowledge.
- Do not discard a passage merely because the teacher temporarily moves away from the main lecture topic.
- When uncertain whether a detail is important, keep it.
- It is acceptable for the final notes to be long.
- Do not stop after reaching a minimum word count.
- The final combined notes should normally retain approximately 40–60% of the information-bearing text of the revised transcript.
- For information-dense lectures, the notes may be longer than 60% of the revised transcript.
- A final output of only 2000 words is not sufficient when the source lecture contains substantially more information.

Before finishing each chunk, review the source from beginning to end and confirm that every substantive topic, explanation, example, story, meaningful digression, announcement, and exam-related detail appears in the output.

## Chunk Processing Rules

The input may be one chunk from a longer lecture.

- Summarize only the supplied chunk.
- Do not assume another chunk will preserve details from this chunk.
- Treat every chunk as independently responsible for retaining all of its substantive information.
- Do not write an introduction or conclusion merely to make the chunk read like a complete essay.
- Begin directly with the lecture content.
- Preserve the internal order of the chunk.
- Do not reduce the final portion of the chunk more aggressively because the output is becoming long.
- Do not repeat general background already explained in an earlier chunk unless the teacher adds a new detail.

Remove only:

- Empty filler such as repeated "เน€เธญเนเธญ", "เธญเนเธฒ", "เนเธญเน€เธเธเธฃเธฑเธ" when it carries no meaning.
- Repeated fragments that do not add information.
- Purely logistical interruptions that have no class value and do not affect the student.
- Never classify side knowledge, a story, a personal experience, or a meaningful digression as filler solely because it is outside the main topic.



