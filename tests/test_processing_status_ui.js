const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const elements = new Map();
const getElement = (id) => {
  if (!elements.has(id)) elements.set(id, {});
  return elements.get(id);
};
const context = vm.createContext({ console, Date, setInterval: () => {},
  document: { querySelector: getElement, querySelectorAll: () => [] } });
const app = fs.readFileSync(require('node:path').join(__dirname, '..', 'app.js'), 'utf8');
vm.runInContext(app.replace('init();', ''), context);
async function check() {
  assert.equal(vm.runInContext("thaiDay('2026-09-30T17:00:00Z')", context), '2026-10-01');
  const attempts = [
    ...Array.from({ length: 3 }, () => ({ startedAt: new Date().toISOString(), status: 'succeeded' })),
    ...Array.from({ length: 2 }, () => ({ startedAt: new Date().toISOString(), status: 'failed' })),
    { startedAt: '2020-01-01T00:00:00Z', status: 'succeeded' },
  ];
  context.fetch = async () => ({ ok: true, json: async () => ({ attempts,
    updatedAt: new Date().toISOString(), trackingStartedAt: new Date().toISOString(),
    scan: { checkedAt: new Date().toISOString(), remaining: [{ videoId: 'qoDYh_8_Ls0', subject: '<x>', classDate: '2026-09-21' }], datePages: 47 } }) });
  await vm.runInContext('loadProcessingStatus()', context);
  assert.match(getElement('#processingToday').textContent, /สำเร็จ 3 · ล้มเหลว 2 · รวม 5/);
  assert.match(getElement('#processingCoverage').textContent, /เหลือ 1/);
  assert.match(getElement('#processingPendingList').innerHTML, /&lt;x&gt;/);
  context.fetch = async () => ({ ok: false, status: 404 });
  context.console = { error: () => {} };
  await vm.runInContext('loadProcessingStatus()', context);
  assert.match(getElement('#processingCoverage').textContent, /ยังยืนยันจำนวนคลิปค้างไม่ได้/);
  assert.equal(getElement('#processingToday').textContent, '');
  console.log('processing status UI checks passed');
}
check().catch((error) => { console.error(error); process.exitCode = 1; });
