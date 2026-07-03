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
- Minimum final combined output is 2000 words.
- If the lecture has a lot of information, write more than 2000 words.
- Do not shorten only because the output is already long.
- Preserve the lecture order as much as possible.
- Think of the task as removing unnecessary spoken filler, not compressing the class.
- Include main class content.
- Include examples and explanations.
- Include side knowledge and background comments.
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

Remove only:

- Empty filler such as repeated "เน€เธญเนเธญ", "เธญเนเธฒ", "เนเธญเน€เธเธเธฃเธฑเธ" when it carries no meaning.
- Repeated fragments that do not add information.
- Purely logistical interruptions that have no class value, unless they affect the student.



