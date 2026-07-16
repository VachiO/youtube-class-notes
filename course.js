const INDEX_URL = "data/site-index.json";
const IMPORTANT_PATTERN = /⚠️|ข้อสอบ|สอบ|คะแนน|quiz|ควิส|ส่ง|กำหนด|deadline|อ่าน|จำ|สอบซ่อม|final|midterm/i;

const params = new URLSearchParams(window.location.search);
const subjectCode = params.get("subject");
const initialLectureId = params.get("lecture");

const state = {
  index: null,
  subject: null,
  lectures: [],
  activeLectureId: "",
  paragraphs: [],
  summaryQuery: "",
};

const el = {
  courseCode: document.querySelector("#courseCode"),
  courseTitle: document.querySelector("#courseTitle"),
  courseActions: document.querySelector("#courseActions"),
  courseReadme: document.querySelector("#courseReadme"),
  courseHints: document.querySelector("#courseHints"),
  lectureList: document.querySelector("#lectureList"),
  lectureListMeta: document.querySelector("#lectureListMeta"),
  readerMeta: document.querySelector("#readerMeta"),
  readerTitle: document.querySelector("#readerTitle"),
  summarySearch: document.querySelector("#summarySearch"),
  readerVideoLink: document.querySelector("#readerVideoLink"),
  readerStatus: document.querySelector("#readerStatus"),
  summaryContent: document.querySelector("#summaryContent"),
  copySummary: document.querySelector("#copySummary"),
  readingContext: document.querySelector("#readingContext"),
  readingCourseCode: document.querySelector("#readingCourseCode"),
  readingCourseTitle: document.querySelector("#readingCourseTitle"),
  readingLectureDate: document.querySelector("#readingLectureDate"),
  backToTop: document.querySelector("#backToTop"),
  themeToggle: document.querySelector("#themeToggle"),
};

init();

async function init() {
  restoreTheme();
  bindEvents();

  if (!subjectCode) {
    renderFatal("ไม่พบรหัสวิชาใน URL");
    return;
  }

  try {
    const response = await fetch(INDEX_URL);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.index = await response.json();
    state.subject = (state.index.subjects || []).find((item) => item.code === subjectCode);
    state.lectures = (state.index.lectures || []).filter((lecture) => lecture.subject === subjectCode);

    if (!state.subject || !state.lectures.length) {
      renderFatal(`ไม่พบรายวิชา ${subjectCode}`);
      return;
    }

    renderCourseHeader();
    await renderDossier();
    renderLectureList();

    const initial = state.lectures.find((lecture) => lecture.id === initialLectureId) || state.lectures[0];
    if (initial) openLecture(initial, false);
  } catch (error) {
    renderFatal("โหลดรายวิชาไม่สำเร็จ");
    console.error(error);
  }
}

function bindEvents() {
  el.summarySearch.addEventListener("input", () => {
    state.summaryQuery = el.summarySearch.value.trim();
    renderSummary();
  });

  el.copySummary.addEventListener("click", copySummary);

  el.backToTop.addEventListener("click", () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  });

  window.addEventListener("scroll", () => {
    el.backToTop.hidden = window.scrollY < 500;
  }, { passive: true });

  const readerObserver = new IntersectionObserver(([entry]) => {
    el.readingContext.classList.toggle("is-visible", entry.isIntersecting);
  });
  readerObserver.observe(document.querySelector("#reader"));

  el.themeToggle.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    setTheme(next);
  });
}

function renderFatal(message) {
  el.courseTitle.textContent = message;
  el.courseReadme.innerHTML = `<p class="empty-state">กลับไปที่ <a href="index.html">หน้ารวม</a></p>`;
  el.courseHints.textContent = "";
  if (el.lectureList) el.lectureList.innerHTML = "";
  if (el.lectureListMeta) el.lectureListMeta.textContent = "";
}

function renderCourseHeader() {
  const latest = [...state.lectures].sort((a, b) => b.date.localeCompare(a.date))[0];
  document.title = `${state.subject.code} | RAM Class Notes`;
  el.courseCode.textContent = state.subject.code;
  el.courseTitle.textContent = state.subject.title;
  el.courseActions.innerHTML = `
    <span class="count-pill">${state.lectures.length.toLocaleString("th-TH")} คาบ</span>
    <span class="count-pill">ล่าสุด ${escapeHtml(latest.dateLabelTh)}</span>
  `;
}

async function renderDossier() {
  const [readme, hints] = await Promise.all([
    fetchText(state.subject.readmePath),
    fetchText(state.subject.hintPath),
  ]);
  el.courseReadme.innerHTML = markdownToHtml(readme || `# ${state.subject.code}\n\nยังไม่มีข้อมูลวิชา`);
  el.courseHints.innerHTML = markdownToHtml(hints || `# แนวสอบ ${state.subject.code}\n\nยังไม่มีแนวสอบที่บันทึกไว้`);
}

function renderLectureList() {
  el.lectureListMeta.textContent = `${state.lectures.length.toLocaleString("th-TH")} คาบ`;
  el.lectureList.innerHTML = state.lectures
    .map((lecture) => {
      const isActive = lecture.id === state.activeLectureId;
      const classes = isActive ? "lecture-row is-active" : "lecture-row";
      return `
        <article class="${classes}" data-lecture-id="${escapeHtml(lecture.id)}">
          <div>
            <h3>${escapeHtml(lecture.dateLabelTh)}</h3>
            <p>${escapeHtml(lecture.video)} · ${lecture.paragraphCount.toLocaleString("th-TH")} ย่อหน้า · ${lecture.wordCount.toLocaleString("th-TH")} คำ</p>
          </div>
          <div class="lecture-row-actions">
            <button class="open-button" type="button" data-open-lecture="${escapeHtml(lecture.id)}">
              ${isActive ? "กำลังอ่าน" : "อ่านคาบนี้"}
            </button>
            ${lecture.sourceUrl ? `<a class="open-button is-secondary" href="${escapeHtml(lecture.sourceUrl)}" target="_blank" rel="noopener">วิดิโอ</a>` : ""}
          </div>
        </article>
      `;
    })
    .join("");

  el.lectureList.querySelectorAll("[data-open-lecture]").forEach((button) => {
    button.addEventListener("click", () => {
      const lecture = state.lectures.find((item) => item.id === button.dataset.openLecture);
      if (lecture) openLecture(lecture, true);
    });
  });
}

async function openLecture(lecture, scrollToReader) {
  state.activeLectureId = lecture.id;
  state.paragraphs = [];
  state.summaryQuery = "";
  el.summarySearch.value = "";
  el.copySummary.disabled = true;
  el.readerMeta.textContent = `${lecture.subject} · ${lecture.video}`;
  el.readerTitle.textContent = lecture.dateLabelTh;
  el.readingCourseCode.textContent = lecture.subject;
  el.readingCourseTitle.textContent = lecture.courseTitle;
  el.readingLectureDate.textContent = `${lecture.dateLabelTh} · ${lecture.video}`;
  el.readingContext.hidden = false;
  if (lecture.sourceUrl) {
    el.readerVideoLink.href = lecture.sourceUrl;
    el.readerVideoLink.hidden = false;
  } else {
    el.readerVideoLink.removeAttribute("href");
    el.readerVideoLink.hidden = true;
  }
  el.readerStatus.textContent = "กำลังโหลดสรุป...";
  el.summaryContent.innerHTML = "";
  renderLectureList();
  window.history.replaceState(null, "", `course.html?subject=${encodeURIComponent(lecture.subject)}&lecture=${encodeURIComponent(lecture.id)}`);

  try {
    const response = await fetch(lecture.summaryPath);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const text = await response.text();
    state.paragraphs = parseParagraphs(text);
    el.copySummary.disabled = false;
    renderSummary();
    if (scrollToReader) document.querySelector("#reader").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    el.readerStatus.textContent = "โหลดสรุปไม่สำเร็จ";
    el.summaryContent.innerHTML = `<p class="empty-state">ไม่พบไฟล์ ${escapeHtml(lecture.summaryPath)}</p>`;
    console.error(error);
  }
}

function parseParagraphs(text) {
  return text
    .split(/\r?\n\s*\r?\n/)
    .map((paragraph) => paragraph.replace(/\s+/g, " ").trim())
    .filter(Boolean)
    .map((text, index) => ({
      id: `summary-p-${index + 1}`,
      text,
      important: IMPORTANT_PATTERN.test(text),
    }));
}

function renderSummary() {
  const query = state.summaryQuery.toLowerCase();
  const matches = query
    ? state.paragraphs.reduce((total, paragraph) => total + paragraph.text.toLowerCase().split(query).length - 1, 0)
    : 0;

  el.readerStatus.textContent = query
    ? `พบ ${matches.toLocaleString("th-TH")} จุด · แสดงครบ ${state.paragraphs.length.toLocaleString("th-TH")} ย่อหน้า`
    : `${state.paragraphs.length.toLocaleString("th-TH")} ย่อหน้า`;

  el.summaryContent.innerHTML = state.paragraphs
    .map((paragraph) => {
      const classes = paragraph.important ? "summary-block is-important" : "summary-block";
      return `<p class="${classes}" id="${paragraph.id}">${highlight(paragraph.text, state.summaryQuery)}</p>`;
    })
    .join("");
}

async function copySummary() {
  if (!state.paragraphs.length) return;
  const label = el.copySummary.textContent;

  try {
    await writeClipboard(state.paragraphs.map((paragraph) => paragraph.text).join("\n\n"));
    el.copySummary.textContent = "คัดลอกแล้ว";
  } catch {
    el.copySummary.textContent = "คัดลอกไม่สำเร็จ";
  }

  window.setTimeout(() => {
    el.copySummary.textContent = label;
  }, 1800);
}

async function writeClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    await navigator.clipboard.writeText(text);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.append(textarea);
  textarea.select();
  const copied = document.execCommand("copy");
  textarea.remove();
  if (!copied) throw new Error("Clipboard unavailable");
}

async function fetchText(path) {
  try {
    const response = await fetch(path);
    if (!response.ok) return "";
    return await response.text();
  } catch {
    return "";
  }
}

function markdownToHtml(markdown) {
  const lines = markdown.replace(/^\ufeff/, "").split(/\r?\n/);
  const html = [];
  let listOpen = false;
  let codeOpen = false;

  for (const rawLine of lines) {
    const line = rawLine.trimEnd();

    if (line.startsWith("```")) {
      if (codeOpen) {
        html.push("</code></pre>");
        codeOpen = false;
      } else {
        closeList();
        html.push("<pre><code>");
        codeOpen = true;
      }
      continue;
    }

    if (codeOpen) {
      html.push(`${escapeHtml(line)}\n`);
      continue;
    }

    if (!line.trim()) {
      closeList();
      continue;
    }

    if (line.startsWith("# ")) {
      closeList();
      html.push(`<h3>${escapeHtml(line.slice(2))}</h3>`);
      continue;
    }

    if (line.startsWith("## ")) {
      closeList();
      html.push(`<h4>${escapeHtml(line.slice(3))}</h4>`);
      continue;
    }

    if (line.startsWith("- ")) {
      if (!listOpen) {
        html.push("<ul>");
        listOpen = true;
      }
      html.push(`<li>${escapeInlineMarkdown(line.slice(2))}</li>`);
      continue;
    }

    closeList();
    html.push(`<p>${escapeInlineMarkdown(line)}</p>`);
  }

  closeList();
  if (codeOpen) html.push("</code></pre>");
  return html.join("");

  function closeList() {
    if (listOpen) {
      html.push("</ul>");
      listOpen = false;
    }
  }
}

function highlight(text, query) {
  if (!query) return escapeHtml(text);
  return escapeHtml(text).replace(new RegExp(`(${escapeRegExp(query)})`, "gi"), "<mark>$1</mark>");
}

function setTheme(theme) {
  if (theme === "dark") {
    document.documentElement.dataset.theme = "dark";
  } else {
    document.documentElement.removeAttribute("data-theme");
  }
  localStorage.setItem("preferred-theme", theme);
}

function restoreTheme() {
  const saved = localStorage.getItem("preferred-theme");
  if (saved) {
    setTheme(saved);
    return;
  }
  setTheme(window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

function escapeInlineMarkdown(value) {
  return escapeHtml(value).replace(/`([^`]+)`/g, "<code>$1</code>");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
