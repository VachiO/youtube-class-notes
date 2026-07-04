const INDEX_URL = "data/site-index.json";
const IMPORTANT_PATTERN = /⚠️|ข้อสอบ|สอบ|คะแนน|quiz|ควิส|ส่ง|กำหนด|deadline|อ่าน|จำ|สอบซ่อม|final|midterm/i;

const params = new URLSearchParams(window.location.search);
const subjectCode = params.get("subject");
const initialLectureId = params.get("lecture");

const state = {
  index: null,
  subject: null,
  lectures: [],
  paragraphs: [],
  summaryQuery: "",
};

const el = {
  courseCode: document.querySelector("#courseCode"),
  courseTitle: document.querySelector("#courseTitle"),
  courseActions: document.querySelector("#courseActions"),
  courseReadme: document.querySelector("#courseReadme"),
  courseHints: document.querySelector("#courseHints"),
  readerMeta: document.querySelector("#readerMeta"),
  readerTitle: document.querySelector("#readerTitle"),
  summarySearch: document.querySelector("#summarySearch"),
  readerVideoLink: document.querySelector("#readerVideoLink"),
  readerStatus: document.querySelector("#readerStatus"),
  summaryContent: document.querySelector("#summaryContent"),
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

  el.themeToggle.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    setTheme(next);
  });
}

function renderFatal(message) {
  el.courseTitle.textContent = message;
  el.courseReadme.innerHTML = `<p class="empty-state">กลับไปที่ <a href="index.html">หน้ารวม</a></p>`;
  el.courseHints.textContent = "";
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

async function openLecture(lecture, scrollToReader) {
  state.paragraphs = [];
  state.summaryQuery = "";
  el.summarySearch.value = "";
  el.readerMeta.textContent = `${lecture.subject} · ${lecture.video}`;
  el.readerTitle.textContent = lecture.dateLabelTh;
  if (lecture.sourceUrl) {
    el.readerVideoLink.href = lecture.sourceUrl;
    el.readerVideoLink.hidden = false;
  } else {
    el.readerVideoLink.removeAttribute("href");
    el.readerVideoLink.hidden = true;
  }
  el.readerStatus.textContent = "กำลังโหลดสรุป...";
  el.summaryContent.innerHTML = "";

  try {
    const response = await fetch(lecture.summaryPath);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const text = await response.text();
    state.paragraphs = parseParagraphs(text);
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
  const filtered = state.paragraphs.filter((paragraph) => {
    const matchesQuery = !query || paragraph.text.toLowerCase().includes(query);
    return matchesQuery;
  });

  el.readerStatus.textContent = `แสดง ${filtered.length.toLocaleString("th-TH")} จาก ${state.paragraphs.length.toLocaleString("th-TH")} ย่อหน้า`;
  if (!filtered.length) {
    el.summaryContent.innerHTML = `<p class="empty-state">ไม่พบข้อความที่ตรงกับตัวกรองนี้</p>`;
    return;
  }

  el.summaryContent.innerHTML = filtered
    .map((paragraph) => {
      const classes = paragraph.important ? "summary-block is-important" : "summary-block";
      return `<p class="${classes}" id="${paragraph.id}">${highlight(paragraph.text, state.summaryQuery)}</p>`;
    })
    .join("");
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
