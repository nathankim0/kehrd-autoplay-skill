const { appendFileSync, writeFileSync } = await import('node:fs');
const config = globalThis.kehrdConfig;
const task = await taskSpace(config.space);
const page = task.page(config.page);
const write = (name, text) => writeFileSync(`${config.state}/${name}`, text);
const log = text => appendFileSync(`${config.state}/progress.log`, `${new Date().toISOString()} ${text}\n`);
const seconds = text => text.split(':').reduce((n, part) => n * 60 + Number(part), 0);
let lastKey = '', stuck = 0;
// shortcut: DOM-visible questions only; the agent inspects screenshots on stalled playback.
for (let round = 0; round < 22; round++) {
  try {
    const info = await page.info();
    if (info.dialog) { write('QUESTION', JSON.stringify(info.dialog)); break; }
    const snap = await page.snapshot();
    write('latest.snapshot', snap);
    const progress = snap.match(/진도율\s*:\s*"\s*\n\s*text "([\d.]+)%"/);
    const percent = progress ? Number(progress[1]) : null;
    if (percent !== null && percent >= 100) { write('DONE', snap); log('DONE 100%'); break; }
    const frame = snap.split('iframe')[1]?.split('anchor')[0] || '';
    if (/radio|checkbox|정답|퀴즈|문제|평가하기/.test(frame)) { write('QUESTION', snap); break; }
    const time = snap.match(/"(\d{2}:\d{2}) \/ (\d{2}:\d{2})"/);
    const paging = snap.match(/text "(\d{2})"\s*\n\s*text "\/"\s*\n\s*text "(\d{2})"/);
    if (!time || !paging || percent === null) { write('QUESTION', snap); break; }
    const key = `${paging[1]}/${paging[2]} ${time[1]}/${time[2]} progress=${percent}%`;
    log(key);
    if (key === lastKey) stuck++; else { lastKey = key; stuck = 0; }
    const ended = seconds(time[2]) > 0 && seconds(time[1]) >= seconds(time[2]);
    // A completed final video may wait for the site's progress update.
    if (stuck >= 3 && !ended) { write('QUESTION', snap); break; }
    if (ended && Number(paging[1]) < Number(paging[2])) {
      const next = snap.match(/text "\/"\s*\n\s*text "\d{2}"\s*\n\s*button \[ref=(\d+)\]/);
      if (!next) { write('QUESTION', snap); break; }
      await page.click(`@${next[1]}`, { label: '다음 학습 페이지' });
    }
  } catch (error) {
    write('QUESTION', error.message);
    break;
  }
  await page.waitForTimeout(10000);
}
