import { strict as assert } from 'node:assert';
import { mkdtempSync, readFileSync, writeFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { saveCertificates } from './certificates.mjs';

const courses = ['1001', '1002'].map(id => ({ title: '교육 / ' + id, status: '수료', url: 'https://kehrd.com/mypage/myclass_detail.html?no=' + id }));
const pdf = Buffer.from('%PDF-1.7\n' + '%'.repeat(1100) + '\n%%EOF\n');
async function fixture(run) {
  const state = mkdtempSync(join(tmpdir(), 'kehrd-certs-'));
  const config = { state, certificateDir: join(state, 'output') };
  const opened = [], closed = [], prints = [], navigation = [];
  let current, limited = false, broken = false, origin = 'kehrd.com';
  const classroom = {
    evaluate: async fn => fn.toString().includes('학습종료') ? 'https://kehrd.com/mypage/myclass_end.html' : courses.slice(0, limited ? 1 : 2).map((course, index) => ({ index, review: course.url.replace('myclass_detail', 'myclass_review') })),
    goto: async url => navigation.push(url),
    waitForSelector: async () => {},
    snapshot: async () => 'observed completed courses',
    click: async selector => {
      if (selector.startsWith('a:')) current = Number(selector.match(/nth=(\d+)/)[1]);
    },
    waitForEvent: async () => {
      const id = ['1001', '1002'][current];
      opened.push(id);
      let attempts = 0;
      return {
        waitForLoadState: async () => {},
        close: async () => closed.push(id),
        cdp: async (method, params) => {
          if (method === 'Page.getFrameTree') return { frameTree: { frame: { url: `https://${origin}/report/openCert_grad.html?no=${id}` } } };
          if (method === 'DOM.getDocument') return { root: { nodeId: 1 } };
          if (method === 'DOM.getOuterHTML') return { outerHTML: '<div class="certif_input">수료증</div>' };
          assert.equal(method, 'Page.printToPDF');
          assert.equal(params.scale, .79);
          assert.ok(params.paperHeight > 11.6 && params.paperWidth > 8.2);
          prints.push(id);
          if (++attempts === 1) throw new Error('CDP request timed out: Page.printToPDF');
          return { data: (broken ? Buffer.from('login page') : pdf).toString('base64') };
        },
      };
    },
  };
  try { await run({ state, config, classroom, opened, closed, prints, navigation, limit: value => { limited = value; }, breakPdf: () => { broken = true; }, untrusted: () => { origin = 'other.example'; } }); }
  finally { rmSync(state, { recursive: true, force: true }); }
}

await fixture(async f => {
  const result = await saveCertificates(f.classroom, f.config, courses);
  assert.equal(result.files.length, 2);
  assert.deepEqual(f.opened, ['1001', '1002']);
  assert.deepEqual(f.closed, f.opened);
  for (const record of result.files) assert.deepEqual(readFileSync(record.file), pdf);
  assert.equal(JSON.parse(readFileSync(join(f.state, 'certificates.json'))).files.length, 2);
  await saveCertificates(f.classroom, f.config, courses);
  assert.equal(f.opened.length, 2, 'reuse previously saved certificates');
  writeFileSync(result.files[1].file, 'do not overwrite this existing file');
  const recovered = await saveCertificates(f.classroom, f.config, courses);
  assert.equal(f.opened.length, 3, 'download only the missing or damaged certificate');
  assert.equal(readFileSync(result.files[1].file, 'utf8'), 'do not overwrite this existing file');
  assert.notEqual(recovered.files[1].file, result.files[1].file);
});
await fixture(async f => {
  f.limit(true);
  await assert.rejects(saveCertificates(f.classroom, f.config, courses), /발급/);
  assert.equal(JSON.parse(readFileSync(join(f.state, 'certificates.json'))).files.length, 1);
  f.limit(false);
  await saveCertificates(f.classroom, f.config, courses);
  assert.deepEqual(f.opened, ['1001', '1002'], 'resume a partial export');
});
await fixture(async f => {
  f.breakPdf();
  await assert.rejects(saveCertificates(f.classroom, f.config, courses), /PDF/);
  assert.equal(JSON.parse(readFileSync(join(f.state, 'certificates.json'))).files.length, 0);
  assert.deepEqual(f.closed, ['1001']);
});
await fixture(async f => {
  f.untrusted();
  await assert.rejects(saveCertificates(f.classroom, f.config, courses), /공식 수료증/);
  assert.equal(f.prints.length, 0);
  assert.deepEqual(f.closed, ['1001']);
});
await fixture(async f => {
  await assert.rejects(saveCertificates(f.classroom, f.config, [{ ...courses[0], status: '미수료' }]), /수료/);
  assert.equal(existsSync(join(f.state, 'certificates.json')), false);
});
await fixture(async f => {
  await assert.rejects(saveCertificates(f.classroom, f.config, [{ ...courses[0], url: 'https://kehrd.com/mypage/myclass_detail.html?no=../../outside' }]), /유효한 과정 번호/);
  assert.equal(f.opened.length, 0);
});
console.log('9 export, resume, overwrite, incomplete PDF, origin, and completion-boundary checks passed');
