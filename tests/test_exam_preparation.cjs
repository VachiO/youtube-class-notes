// Run with: node tests/test_exam_preparation.cjs
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "course.js"), "utf8").replace("init();", "");

async function render(subject, missing = "", hash = "") {
  const elements = new Map();
  const requested = [];
  let copied = "";
  function element() {
    return {
      hidden: true, innerHTML: "", scrolled: false,
      scrollIntoView() { this.scrolled = true; },
      querySelectorAll() {
        return [...this.innerHTML.matchAll(/data-copy-exam="(\d+)">([^<]+)</g)].map(match => ({
          dataset: { copyExam: match[1] }, textContent: match[2],
          addEventListener(event, callback) { this.click = callback; },
        }));
      },
    };
  }
  const context = vm.createContext({
    URLSearchParams,
    window: { location: { search: `?subject=${subject}`, hash }, setTimeout() {} },
    document: { querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, element());
      return elements.get(selector);
    } },
    async fetch(file) {
      requested.push(file);
      return { ok: file !== missing, text: async () => fs.readFileSync(path.join(root, file), "utf8") };
    },
    captureCopy(text) { copied = text; },
  });
  vm.runInContext(source, context);
  vm.runInContext("writeClipboard = async text => captureCopy(text)", context);
  // Retain the actual buttons whose handlers the renderer binds.
  const panel = element();
  const getButtons = panel.querySelectorAll;
  panel.querySelectorAll = function () { return this.buttons = getButtons.call(this); };
  elements.set("#examPreparationContent", panel);
  await vm.runInContext(`state.subject = { code: '${subject}', readmePath: 'readme-${subject}.md', hintPath: 'hint-${subject}.md' }; renderDossier()`, context);
  return { elements, requested, panel, getCopied: () => copied };
}

(async () => {
  const result = await render("POL2100", "", "#examPreparation");
  assert.equal(result.elements.get("#examPreparation").hidden, false);
  assert.equal(result.elements.get("#examPreparation").scrolled, true);
  assert.equal(result.panel.buttons.length, 4);
  const html = result.panel.innerHTML;
  assert.ok(html.indexOf('id="exam-question-1"') < html.indexOf('id="exam-question-2"'));
  for (const [number, counts] of [[1, [4, 5, 4, 5, 5, 3]], [2, [5, 6, 5, 5, 5, 3]]]) {
    const answer = fs.readFileSync(path.join(root, `exam-answer-${number}-POL2100.md`), "utf8");
    const outline = fs.readFileSync(path.join(root, `exam-outline-${number}-POL2100.md`), "utf8");
    const sections = answer.trim().split(/\r?\n\r?\n(?=## )/).slice(1);
    assert.equal(sections.length, 6);
    sections.forEach((section, index) => {
      assert.equal(section.split(/\r?\n\r?\n/).length - 1, counts[index], `Question ${number}, topic ${index + 1}: paragraph count`);
      assert.ok(outline.includes(`## ${number}.${index + 1} `));
    });
    assert.ok(outline.includes(`รวม ${counts.reduce((a, b) => a + b)} ย่อหน้า`));
    assert.ok(html.includes(`${number}.5 วัฒนธรรมการเมือง`));
    for (const kind of ["answer", "outline"]) assert.ok(result.requested.includes(`exam-${kind}-${number}-POL2100.md`));
  }
  for (const button of result.panel.buttons) {
    await button.click();
    const index = Number(button.dataset.copyExam);
    const file = `exam-${index % 2 ? "outline" : "answer"}-${Math.floor(index / 2) + 1}-POL2100.md`;
    assert.equal(result.getCopied(), fs.readFileSync(path.join(root, file), "utf8").replace(/^#{1,2} /gm, ""));
    assert.equal(button.textContent, "คัดลอกแล้ว");
  }
  const partial = await render("POL2100", "exam-outline-1-POL2100.md");
  assert.equal(partial.panel.buttons.length, 3);
  assert.ok(partial.panel.innerHTML.includes("โหลดเนื้อหาไม่สำเร็จ"));
  assert.ok(partial.panel.innerHTML.includes("2.6 อาหาร"));
  const other = await render("POL1101");
  assert.ok(!other.requested.some(file => file.startsWith("exam-")));
  assert.ok(!other.elements.has("#examPreparation"));
  console.log("Exam preparation: paired versions, six topics, matching paragraph counts, copying, partial failure, deep link, and course isolation passed.");
})().catch(error => { console.error(error); process.exitCode = 1; });
