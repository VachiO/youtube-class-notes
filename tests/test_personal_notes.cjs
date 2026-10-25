// Run with: node tests/test_personal_notes.cjs
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "..");
const source = fs.readFileSync(path.join(root, "course.js"), "utf8");

async function render(subject, missing = false, hash = "") {
  const elements = new Map();
  const requested = [];
  const context = vm.createContext({
    URLSearchParams,
    window: { location: { search: `?subject=${subject}`, hash } },
    document: { querySelector(selector) {
      if (!elements.has(selector)) elements.set(selector, {
        hidden: true, innerHTML: "", scrolled: false,
        scrollIntoView() { this.scrolled = true; },
      });
      return elements.get(selector);
    } },
    async fetch(file) {
      requested.push(file);
      const exists = missing !== true && missing !== file && fs.existsSync(path.join(root, file));
      return { ok: exists, text: async () => fs.readFileSync(path.join(root, file), "utf8") };
    },
  });
  vm.runInContext(source.replace("init();", ""), context);
  await vm.runInContext(`state.subject = { code: '${subject}', readmePath: 'readme-${subject}.md', hintPath: 'hint-${subject}.md' }; renderDossier()`, context);
  return { elements, requested, context };
}

(async () => {
  const { elements, requested, context } = await render("POL2129");
  assert.equal(elements.get("#personalNotes").hidden, false);
  const parts = [
    ["30 มิถุนายน 2569", ["Political Economy", "ธนาคารแห่งประเทศไทย", "หนี้สาธารณะ"]],
    ["7 กรกฎาคม 2569", ["Bank-based", "Market-based", "หุ้นกู้"]],
    ["14 กรกฎาคม 2569", ["100 ล้านดอลลาร์", "2,500 ล้านบาท", "5,000 ล้านบาท", "NPL"]],
    ["4 สิงหาคม 2569", ["Dual Track Policy", "Basel Standard", "OTOP"]],
    ["11 สิงหาคม 2569", ["FTA", "ACMECS", "CEO Diplomacy"]],
    ["25 สิงหาคม 2569", ["Partnership", "Autonomy", "Horizontal", "NGO ฝรั่งเศส"]],
    ["1 กันยายน 2569", ["Resistance", "Reform", "Revolution", "Expressive", "Division of Labour", "อินเดีย"]],
    ["8 กันยายน 2569", ["Digital Activism", "Direct Democracy", "misinformation", "disinformation", "2010", "Arab Spring", "โคลอมเบีย", "ปากีสถาน", "อินเดีย", "เนปาล", "ความย้อนแย้ง", "Digital Literacy"]],
    ["22 กันยายน 2569", ["Multitude", "Hardt", "Negri", "Exploitation", "Dispossession"]],
  ];
  const html = elements.get("#personalNotesContent").innerHTML;
  let lastPosition = -1;
  for (const [label, terms] of parts) {
    const position = html.indexOf(`<h4>${label} · `);
    assert.ok(position > lastPosition, `Missing or out-of-order section: ${label}`);
    lastPosition = position;
    const end = html.indexOf("<h4>", position + 1);
    const content = html.slice(position, end);
    for (const term of terms) assert.ok(content.includes(term), `Missing ${label} content: ${term}`);
  }
  const noteRequests = requested.filter(file => file.startsWith("notes-POL2129"));
  assert.deepEqual(noteRequests, ["notes-POL2129-narrative.md"]);
  assert.ok(html.includes("คนขับแท็กซี่"));
  assert.ok(html.includes("อ่านทั้งวิชาให้เป็นเรื่องเดียว"));
  assert.ok(!html.includes("ยังไม่เผยแพร่บนเว็บ"));
  assert.ok(!html.split("<h4>แหล่งเนื้อหา")[0].includes("<ul>"), "Lecture content uses narrative paragraphs");
  assert.ok(html.includes('href="https://www.unesco.org/en/query-list/m/misinformation"'));
  const unsafe = vm.runInContext('escapeInlineMarkdown(\'[bad](javascript:alert(1)) <img src=x onerror=alert(1)>\')', context);
  assert.ok(!unsafe.includes("<a ") && !unsafe.includes("<img"), "Escape HTML and refuse non-HTTPS links");
  const courseHtml = fs.readFileSync(path.join(root, "course.html"), "utf8");
  const panel = courseHtml.split('id="personalNotes"')[1].split('<section class="lecture-picker"')[0];
  assert.ok(panel.includes("อ่านรวดเดียวก่อนสอบ"));
  assert.ok(!panel.includes("<details"), "Read all notes without expanding each day");
  assert.equal(courseHtml.split('id="personalNotesContent"').length - 1, 1);
  const other = await render("POL1101");
  assert.ok(!other.requested.some(file => file.startsWith("notes-POL2129")));
  assert.ok(!other.elements.has("#personalNotes"));
  const missing = await render("POL2129", true);
  assert.equal(missing.elements.get("#personalNotesContent").innerHTML.split("โหลดบันทึกไม่สำเร็จ").length - 1, 1);
  const direct = await render("POL2129", false, "#personalNotes");
  assert.equal(direct.elements.get("#personalNotes").scrolled, true);
  console.log("Narrative review: nine dates in order, stories, single source, safe citations, visibility, load failure, and direct link passed.");
})().catch(error => { console.error(error); process.exitCode = 1; });
