// Run with: node tests/test_personal_notes.cjs
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "course.js"), "utf8");

async function render(subject, missing = false) {
  const elements = new Map();
  const requested = [];
  const context = vm.createContext({
    URLSearchParams,
    window: { location: { search: `?subject=${subject}` } },
    document: { querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, { hidden: true, innerHTML: "" });
      return elements.get(selector);
    } },
    async fetch(file) {
      requested.push(file);
      const exists = !missing && fs.existsSync(path.join(root, file));
      return { ok: exists, text: async () => fs.readFileSync(path.join(root, file), "utf8") };
    },
  });
  vm.runInContext(source.replace("init();", ""), context);
  await vm.runInContext(`state.subject = { code: '${subject}', readmePath: 'readme-${subject}.md', hintPath: 'hint-${subject}.md' }; renderDossier()`, context);
  return { elements, requested };
}

(async () => {
  const { elements } = await render("POL2129");
  assert.equal(elements.get("#personalNotes").hidden, false);
  const html = elements.get("#personalNotesContent").innerHTML;
  for (const text of ["1 กันยายน 2569", "Resistance", "Reform", "Revolution", "Expressive", "Division of Labour", "Bulmer", "อิสราเอล", "อินเดีย"]) {
    assert.ok(html.includes(text), `Missing note content: ${text}`);
  }
  const other = await render("POL1101");
  const september8 = elements.get("#personalNotesSeptember8Content").innerHTML;
  for (const text of ["8 กันยายน 2569", "Digital Activism", "Direct Democracy", "Misinformation", "Disinformation", "2546 (2003)", "2010", "Arab Spring", "โคลอมเบีย", "ปากีสถาน", "อินเดีย", "เนปาล", "ความย้อนแย้ง", "5.5", "Digital Literacy", "6.4 การตอบโต้อย่างรุนแรง"]) {
    assert.ok(september8.includes(text), `Missing September 8 note content: ${text}`);
  }
  assert.ok(!other.requested.includes("notes-POL2129-2026-09-08.md"));
  assert.ok(!other.requested.includes("notes-POL2129-2026-09-01.md"));
  assert.ok(!other.elements.has("#personalNotes"));
  const missing = await render("POL2129", true);
  assert.ok(missing.elements.get("#personalNotesContent").innerHTML.includes("โหลดบันทึกไม่สำเร็จ"));
  assert.ok(missing.elements.get("#personalNotesSeptember8Content").innerHTML.includes("โหลดบันทึกไม่สำเร็จ"));
  console.log("Personal notes: content, course visibility, and load failure checks passed.");
})().catch(error => { console.error(error); process.exitCode = 1; });
