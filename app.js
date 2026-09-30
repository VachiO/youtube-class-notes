const INDEX_URL = "data/site-index.json";

const state = {
  index: null,
  lectures: [],
  view: "day",
  query: "",
};

const el = {
  lectureCount: document.querySelector("#lectureCount"),
  subjectCount: document.querySelector("#subjectCount"),
  latestDate: document.querySelector("#latestDate"),
  globalSearch: document.querySelector("#globalSearch"),
  viewButtons: document.querySelectorAll("[data-view]"),
  catalogStatus: document.querySelector("#catalogStatus"),
  catalogContent: document.querySelector("#catalogContent"),
  themeToggle: document.querySelector("#themeToggle"),
};

init();

async function init() {
  restoreTheme();
  bindEvents();
  loadProcessingStatus();
  setInterval(loadProcessingStatus, 60000);

  try {
    const response = await fetch(INDEX_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    state.index = await response.json();
    state.lectures = state.index.lectures || [];
    renderStats();
    renderCatalog();
  } catch (error) {
    el.catalogStatus.textContent = "โหลดรายการไม่สำเร็จ";
    el.catalogContent.innerHTML = `<p class="empty-state">ไม่พบไฟล์ ${INDEX_URL}</p>`;
    console.error(error);
  }
}

function thaiDay(value) {
  return new Date(new Date(value).getTime() + 7 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

function processingCounts(attempts, day) {
  const today = attempts.filter((a) => thaiDay(a.startedAt) === day);
  return {
    succeeded: today.filter((a) => a.status === "succeeded").length,
    failed: today.filter((a) => a.status === "failed").length,
    running: today.filter((a) => a.status === "running").length,
    total: today.length,
  };
}

async function loadProcessingStatus() {
  const coverage = document.querySelector("#processingCoverage");
  const today = document.querySelector("#processingToday");
  const checked = document.querySelector("#processingChecked");
  const pending = document.querySelector("#processingPending");
  try {
    const response = await fetch("data/processing-status.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    const scan = data.scan;
    const count = processingCounts(data.attempts, thaiDay(new Date()));
    const stale = !scan || Date.now() - new Date(scan.checkedAt).getTime() > 24 * 60 * 60 * 1000;
    coverage.textContent = scan
      ? `${data.scanError || stale ? "ผลตรวจครั้งล่าสุด: " : ""}เหลือ ${scan.remaining.length} คลิปที่ยังไม่มีสรุป จากการตรวจแหล่งวิดีโอจริง`
      : "ยังไม่มีผลตรวจแหล่งวิดีโอที่ครบถ้วน";
    today.textContent = `วันนี้ (เวลาไทย) สำเร็จ ${count.succeeded} · ล้มเหลว ${count.failed} · รวม ${count.total} ครั้ง${count.running ? ` · กำลังดำเนินการ ${count.running}` : ""}`;
    const format = (value) => new Date(value).toLocaleString("th-TH", { timeZone: "Asia/Bangkok" });
    checked.textContent = `${scan ? `ตรวจแหล่งวิดีโอ ${format(scan.checkedAt)} (${scan.datePages} หน้ารายวัน) · ` : ""}อัปเดตผลประมวลผล ${format(data.updatedAt)} · เริ่มนับ ${format(data.trackingStartedAt)}${data.scanError ? " · ตรวจครั้งล่าสุดไม่สำเร็จ ยังยืนยันจำนวนปัจจุบันไม่ได้" : stale ? " · ผลตรวจเกิน 24 ชั่วโมง รอการตรวจใหม่" : ""}`;
    pending.hidden = !scan || !scan.remaining.length;
    document.querySelector("#processingPendingList").innerHTML = (scan?.remaining || []).map((v) =>
      `<li><a href="https://www.youtube.com/watch?v=${encodeURIComponent(v.videoId)}" target="_blank" rel="noopener">${escapeHtml(v.subject)} · ${escapeHtml(v.classDate)}</a></li>`
    ).join("");
  } catch (error) {
    coverage.textContent = "โหลดสถานะไม่สำเร็จ ยังยืนยันจำนวนคลิปค้างไม่ได้";
    today.textContent = "";
    checked.textContent = "";
    pending.hidden = true;
    console.error(error);
  }
}

function bindEvents() {
  el.globalSearch.addEventListener("input", () => {
    state.query = el.globalSearch.value.trim();
    renderCatalog();
  });

  el.viewButtons.forEach((button) => {
    button.addEventListener("click", () => {
      state.view = button.dataset.view;
      el.viewButtons.forEach((item) => {
        const active = item === button;
        item.classList.toggle("is-active", active);
        item.setAttribute("aria-selected", active ? "true" : "false");
      });
      renderCatalog();
    });
  });

  el.themeToggle.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    setTheme(next);
  });

  el.catalogContent.addEventListener("click", (event) => {
    if (event.target.closest("a")) return;
    const card = event.target.closest("[data-href]");
    if (card) window.location.href = card.dataset.href;
  });

  el.catalogContent.addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const card = event.target.closest("[data-href]");
    if (!card) return;
    event.preventDefault();
    window.location.href = card.dataset.href;
  });
}

function renderStats() {
  const latest = [...state.lectures].sort((a, b) => b.date.localeCompare(a.date))[0];
  el.lectureCount.textContent = state.lectures.length.toLocaleString("th-TH");
  el.subjectCount.textContent = (state.index.subjects || []).length.toLocaleString("th-TH");
  el.latestDate.textContent = latest ? latest.dateLabelTh.replace(/^วัน.+?ที่ /, "") : "-";
}

function filteredLectures() {
  const query = state.query.toLowerCase();
  return state.lectures.filter((lecture) => {
    const haystack = [
      lecture.subject,
      lecture.courseTitle,
      lecture.date,
      lecture.dateLabelTh,
      lecture.video,
      lecture.excerpt,
    ].join(" ").toLowerCase();
    return !query || haystack.includes(query);
  });
}

function renderCatalog() {
  const lectures = filteredLectures();
  el.catalogStatus.textContent = `${lectures.length.toLocaleString("th-TH")} คาบ`;

  if (!lectures.length) {
    el.catalogContent.innerHTML = `<p class="empty-state">ไม่พบรายการที่ตรงกับคำค้นหา</p>`;
    return;
  }

  el.catalogContent.innerHTML = state.view === "day" ? renderByDay(lectures) : renderBySubject(lectures);
}

function renderBySubject(lectures) {
  const subjects = (state.index.subjects || [])
    .map((subject) => ({
      ...subject,
      lectures: lectures.filter((lecture) => lecture.subject === subject.code),
    }))
    .filter((subject) => subject.lectures.length);

  return `
    <div class="course-card-grid">
      ${subjects.map(renderCourseCard).join("")}
    </div>
  `;
}

function renderCourseCard(subject) {
  const latest = [...subject.lectures].sort((a, b) => b.date.localeCompare(a.date))[0];
  const href = `course.html?subject=${encodeURIComponent(subject.code)}`;
  return `
    <article class="course-card clickable-card" data-href="${escapeHtml(href)}" tabindex="0" role="link" aria-label="ไปยังรายวิชา ${escapeHtml(subject.code)}">
      <p class="kicker">${subject.lectures.length.toLocaleString("th-TH")} คาบ</p>
      <div class="course-code-line">
        <h2>${escapeHtml(subject.code)}</h2>
        ${renderExamStatus(subject.noExam)}
      </div>
      <p class="course-title">${escapeHtml(subject.title)}</p>
      <p class="course-latest">${escapeHtml(latest.dateLabelTh)}</p>
    </article>
  `;
}

function renderByDay(lectures) {
  const days = groupBy([...lectures].sort((a, b) => b.date.localeCompare(a.date)), (lecture) => lecture.date);
  return Object.entries(days)
    .sort(([a], [b]) => b.localeCompare(a))
    .map(([, items]) => {
      const first = items[0];
      const sorted = [...items].sort((a, b) => a.subject.localeCompare(b.subject) || a.video.localeCompare(b.video));
      return `
        <section class="day-group">
          <div class="group-head">
            <h2>${escapeHtml(first.dateLabelTh)}</h2>
            <span class="count-pill">${items.length.toLocaleString("th-TH")} คาบ</span>
          </div>
          <div class="lecture-grid">
            ${sorted.map(renderDayLectureCard).join("")}
          </div>
        </section>
      `;
    })
    .join("");
}

function renderDayLectureCard(lecture) {
  const href = `course.html?subject=${encodeURIComponent(lecture.subject)}&lecture=${encodeURIComponent(lecture.id)}`;
  const videoLink = lecture.sourceUrl
    ? `<a class="text-link" href="${escapeHtml(lecture.sourceUrl)}" target="_blank" rel="noopener">วิดีโอ</a>`
    : "";
  return `
    <article class="lecture-card clickable-card" data-href="${escapeHtml(href)}" tabindex="0" role="link" aria-label="อ่านสรุป ${escapeHtml(lecture.subject)} ${escapeHtml(lecture.dateLabelTh)}">
      <div class="lecture-topline">
        <span>${escapeHtml(lecture.subject)}</span>
        ${renderExamStatus(lecture.noExam)}
        <span>${escapeHtml(lecture.video)}</span>
      </div>
      <h3>${escapeHtml(lecture.courseTitle)}</h3>
      <p>${escapeHtml(lecture.excerpt)}</p>
      <div class="card-actions">
        ${videoLink}
      </div>
    </article>
  `;
}

function groupBy(items, getKey) {
  return items.reduce((groups, item) => {
    const key = getKey(item);
    groups[key] ||= [];
    groups[key].push(item);
    return groups;
  }, {});
}

function renderExamStatus(noExam) {
  return noExam ? '<span class="status-badge">ไม่ต้องสอบ</span>' : "";
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

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
