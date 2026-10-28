export async function saveCertificates(classroom, config, courses) {
  const fs = await import('node:fs');
  const path = await import('node:path');
  const { randomUUID } = await import('node:crypto');
  const validPdf = file => {
    if (!fs.existsSync(file)) return false;
    const bytes = fs.readFileSync(file);
    return bytes.length > 1024 && bytes.subarray(0, 5).toString() === '%PDF-' && bytes.subarray(-1024).includes('%%EOF');
  };
  if (!courses.length || courses.some(course => course.status !== '수료' || !course.url)) throw new Error('모든 과정의 수료와 과정 링크부터 확인해야 합니다.');
  const manifestFile = path.join(config.state, 'certificates.json');
  const manifest = fs.existsSync(manifestFile) ? JSON.parse(fs.readFileSync(manifestFile, 'utf8')) : { directory: config.certificateDir, files: [] };
  fs.mkdirSync(manifest.directory, { recursive: true, mode: 0o700 });
  const saveManifest = () => {
    fs.writeFileSync(manifestFile + '.tmp', JSON.stringify(manifest, null, 2), { mode: 0o600 });
    fs.renameSync(manifestFile + '.tmp', manifestFile);
  };
  saveManifest();
  const endUrl = await classroom.evaluate(() => [...document.querySelectorAll('a')].find(a => a.textContent.includes('학습종료된 수업'))?.href);
  if (!endUrl) throw new Error('학습종료된 수업 링크를 확인해야 합니다.');
  await classroom.goto(endUrl);
  await classroom.waitForSelector('a:has-text("수료증발급") >> nth=0', { state: 'visible', timeout: 15000 });
  const links = await classroom.evaluate(() => [...document.querySelectorAll('a')].filter(a => a.textContent.includes('수료증발급')).map((a, index) => ({
    index, review: a.parentElement.querySelector('a[href*="myclass_review"]')?.href,
  })));
  for (const course of courses) {
    const id = new URL(course.url).searchParams.get('no');
    if (!id || !/^\d+$/.test(id)) throw new Error('유효한 과정 번호가 없는 수료증은 저장하지 않습니다.');
    const saved = manifest.files.find(record => record.course === course.url);
    if (saved && validPdf(saved.file)) continue;
    const link = links.find(item => item.review && new URL(item.review).searchParams.get('no') === id);
    if (!link) throw new Error('완료 과정의 수료증 발급 버튼을 확인해야 합니다.');
    await classroom.snapshot();
    await classroom.click(`a:has-text("수료증발급") >> nth=${link.index}`, { label: '완료 과정 수료증 발급' });
    const [certificate] = await Promise.all([
      classroom.waitForEvent('popup', { timeout: 10000 }),
      classroom.click('loc=role:button[name="수료증"]', { label: '공식 수료증 문서 열기' }),
    ]);
    try {
      await certificate.waitForLoadState('load', { timeout: 15000 });
      const { frameTree } = await certificate.cdp('Page.getFrameTree');
      const url = new URL(frameTree.frame.url);
      if (url.protocol !== 'https:' || url.hostname !== 'kehrd.com' || url.pathname !== '/report/openCert_grad.html' || url.searchParams.get('no') !== id) throw new Error('요청한 과정의 공식 수료증 화면이 아닙니다.');
      const document = await certificate.cdp('DOM.getDocument', { depth: 0 });
      const { outerHTML } = await certificate.cdp('DOM.getOuterHTML', { nodeId: document.root.nodeId });
      if (!outerHTML.includes('certif_input')) throw new Error('수료증 내용이 아직 표시되지 않았습니다.');
      // The site's 1000×1400 layout fits A4 at this scale without editing its content.
      const options = { paperWidth: 210 / 25.4, paperHeight: 297 / 25.4, scale: .79, printBackground: true, preferCSSPageSize: false, marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0 };
      let result;
      try { result = await certificate.cdp('Page.printToPDF', options, { timeout: 5000 }); }
      catch (error) {
        if (!error.message.includes('timed out: Page.printToPDF')) throw error;
        // window.onload calls window.print(); its first print request may remain blocked.
        await certificate.cdp('DOM.getDocument', { depth: 0 }, { timeout: 5000 });
        result = await certificate.cdp('Page.printToPDF', options, { timeout: 15000 });
      }
      const bytes = Buffer.from(result.data, 'base64');
      if (bytes.length <= 1024 || bytes.subarray(0, 5).toString() !== '%PDF-' || !bytes.subarray(-1024).includes('%%EOF')) throw new Error('수료증 PDF가 비어 있거나 저장이 완료되지 않았습니다.');
      const name = `${id}-${(course.title || '수료증').replace(/[\\/:*?"<>|\x00-\x1f]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 60)}`;
      let file = path.join(manifest.directory, name + '.pdf');
      if (fs.existsSync(file)) file = path.join(manifest.directory, `${name}-${randomUUID().slice(0, 8)}.pdf`);
      fs.writeFileSync(file, bytes, { flag: 'wx', mode: 0o600 });
      manifest.files = manifest.files.filter(record => record.course !== course.url);
      manifest.files.push({ course: course.url, title: course.title, file });
      saveManifest();
    } finally {
      await certificate.close();
    }
  }
  return manifest;
}
