// Called after a lesson reaches 100%; all navigation uses the visible classroom UI.
async function advancePlaylist(task, player, config, write, log) {
  const classroom = task.page(config.playlistPage);
  await player.click('a.end_btn', { label: '완료한 차시 학습 종료' });
  await classroom.reload();

  async function openLesson() {
    const index = await classroom.evaluate(() => [...document.querySelectorAll('a.detail_btn')].findIndex(link => {
      const row = link.closest('li');
      const progress = row?.querySelector('b.font18')?.textContent?.match(/([\d.]+)%/);
      return link.textContent.includes('학습하기') && progress && Number(progress[1]) < 100;
    }));
    if (index < 0) return false;
    const popup = classroom.waitForEvent('popup');
    await classroom.click(`a.detail_btn >> nth=${index}`, { label: '다음 미완료 차시 시작' });
    const next = await popup;
    await next.waitForLoadState();
    write('player.json', JSON.stringify({ page: next.label }));
    log('다음 미완료 차시 시작');
    return true;
  }

  if (await openLesson()) return;
  const pending = await classroom.evaluate(() => [...document.querySelectorAll('li.eval_item')].some(item => /미제출|불합격/.test(item.querySelector('b.font18')?.textContent || '')));
  if (pending) {
    write('QUESTION', `차시별 평가를 에이전트가 처리해야 합니다.\n${await classroom.snapshot({ scope: 'full_page' })}`);
    return;
  }

  const detailUrl = await classroom.url();
  // The list link is discovered in the page, rather than constructing enrollment URLs.
  const listUrl = await classroom.evaluate(() => [...document.querySelectorAll('a')].find(a => a.textContent.trim() === '목록가기')?.href);
  if (!listUrl) { write('QUESTION', '과정 목록 링크를 확인해야 합니다.'); return; }
  await classroom.goto(listUrl);
  const courses = await classroom.evaluate(() => [...document.querySelectorAll('.course-card')].map(card => ({
    title: card.querySelector('.course-title')?.textContent.trim(),
    status: card.querySelector('.status-badge')?.textContent.trim(),
    url: card.querySelector('a.btn-study[href*="myclass_detail"]')?.href,
  })));
  write('playlist.json', JSON.stringify(courses, null, 2));
  if (!courses.length) { write('QUESTION', '과정 목록의 화면 구조를 확인해야 합니다.'); return; }
  if (courses.some(course => !['수료', '미수료'].includes(course.status))) { write('QUESTION', '과정별 수료 상태를 확인해야 합니다.'); return; }
  const next = courses.find(course => course.status === '미수료' && course.url);
  if (!next) {
    const snap = await classroom.snapshot({ scope: 'full_page' });
    if (courses.some(course => course.status === '미수료')) { write('QUESTION', snap); return; }
    await saveCertificates(classroom, config, courses);
    write('DONE', snap);
    return;
  }
  if (next.url === detailUrl) { write('QUESTION', '차시 재생은 완료했지만 과정이 미수료입니다. 평가와 수료조건을 확인해야 합니다.'); return; }
  await classroom.goto(next.url);
  log(`다음 과정: ${next.title}`);
  if (!await openLesson()) write('QUESTION', `다음 과정의 학습 버튼을 확인해야 합니다.\n${await classroom.snapshot({ scope: 'full_page' })}`);
}
