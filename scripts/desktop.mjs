// The legacy player treats the literal query string "undefined" as capture mode.
export async function restoreDesktopActivity(page, snapshot) {
  if (!snapshot.includes('PC로 접속하면 학습활동을 할 수 있습니다.')) return false;
  const desktop = await page.evaluate(() => !/Android|iPhone|iPad|Mobile/i.test(navigator.userAgent) && navigator.maxTouchPoints === 0);
  if (!desktop) return false;
  const { frameTree } = await page.cdp('Page.getFrameTree');
  for (const { frame } of frameTree.childFrames || []) {
    const url = new URL(frame.url);
    if (url.protocol !== 'https:' || url.hostname !== 'cdn.kehrd.com' || url.searchParams.get('capture') !== 'undefined') continue;
    url.searchParams.delete('capture');
    await page.cdp('Page.navigate', { frameId: frame.id, url: url.href });
    return true;
  }
  return false;
}
