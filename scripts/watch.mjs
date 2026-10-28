const { appendFileSync, writeFileSync, readFileSync, existsSync } = await import('node:fs');
const config = globalThis.kehrdConfig;
const task = await taskSpace(config.space);
const playerFile = `${config.state}/player.json`;
const page = task.page(config.playlistPage && existsSync(playerFile) ? JSON.parse(readFileSync(playerFile, 'utf8')).page : config.page);
const write = (name, text) => writeFileSync(`${config.state}/${name}`, text);
const log = text => appendFileSync(`${config.state}/progress.log`, `${new Date().toISOString()} ${text}\n`);
const seconds = text => text.split(':').reduce((n, part) => n * 60 + Number(part), 0);
let lastKey = '', stuck = 0, autoplayAttempts = 0;
// shortcut: DOM-visible questions only; the agent inspects screenshots on stalled playback.
for (let round = 0; round < 22; round++) {
  try {
    // Browser-side rounds can outlive the CLI process that started them.
    if (existsSync(`${config.state}/STOP`) || existsSync(`${config.state}/QUESTION`) || (config.runId && readFileSync(`${config.state}/watch-generation`, 'utf8') !== config.runId)) break;
    const dialogs = await settleTrainingDialogs(page);
    if (dialogs.blocked) { write('QUESTION', JSON.stringify(dialogs.blocked)); break; }
    if (dialogs.handled) { await page.waitForTimeout(10000); continue; }
    const snap = await page.snapshot();
    write('latest.snapshot', snap);
    if (await restoreDesktopActivity(page, snap)) { log('Restored desktop activity display'); break; }
    const autoplay = snap.match(/button \[ref=(\d+)\]\s*\n\s*container\s*\n\s*text "웹 보안 정책에 따라 자동재생이 제한되었습니다\./);
    if (autoplay) {
      if (++autoplayAttempts > 2) { write('QUESTION', snap); break; }
      await page.click(`@${autoplay[1]}`, { label: '자동재생 제한 안내 해제' });
      await page.waitForTimeout(10000);
      continue;
    }
    autoplayAttempts = 0;
    const progress = snap.match(/진도율\s*:\s*"\s*\n\s*text "([\d.]+)%"/);
    const percent = progress ? Number(progress[1]) : null;
    const time = snap.match(/"(\d{2}:\d{2}) \/ (\d{2}:\d{2})"/);
    const paging = snap.match(/text "(\d{2})"\s*\n\s*text "\/"\s*\n\s*text "(\d{2})"/);
    const playbackComplete = time && paging && seconds(time[2]) > 0 && seconds(time[1]) >= seconds(time[2]) && Number(paging[1]) === Number(paging[2]);
    const frame = snap.split('iframe')[1]?.split('anchor')[0] || '';
    if (/radio|checkbox|정답|퀴즈|문제|평가하기/.test(frame)) { write('QUESTION', snap); break; }
    if (percent !== null && percent >= 100 && (!config.playlistPage || playbackComplete)) {
      log('차시 100%');
      if (config.playlistPage) {
        write('lesson-completed.snapshot', snap);
        await advancePlaylist(task, page, config, write, log);
      } else { write('DONE', snap); log('DONE 100%'); }
      break;
    }
    if (!time || !paging || percent === null) { write('QUESTION', snap); break; }
    const key = `${paging[1]}/${paging[2]} ${time[1]}/${time[2]} progress=${percent}%`;
    log(key);
    if (key === lastKey) stuck++; else { lastKey = key; stuck = 0; }
    const ended = seconds(time[2]) > 0 && seconds(time[1]) >= seconds(time[2]);
    // A completed final video may wait for the site's progress update.
    if (stuck >= 3 && !ended) { write('QUESTION', snap); break; }
    // The displayed timer can reach its end before the player enables navigation.
    if (ended && stuck >= 1 && Number(paging[1]) < Number(paging[2])) {
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
