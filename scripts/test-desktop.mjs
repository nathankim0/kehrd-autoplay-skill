import { strict as assert } from 'node:assert';
import { restoreDesktopActivity } from './desktop.mjs';

const message = 'PC로 접속하면 학습활동을 할 수 있습니다.';
for (const [snapshot, desktop, url, expected] of [
  [message, true, 'https://cdn.kehrd.com/course/page.html?progress=undefined&capture=undefined&trans=true', true],
  [message, false, 'https://cdn.kehrd.com/course/page.html?capture=undefined', false],
  [message, true, 'https://cdn.kehrd.com/course/page.html?capture=true', false],
  [message, true, 'https://other.example/page.html?capture=undefined', false],
  ['normal playback', true, 'https://cdn.kehrd.com/page.html?capture=undefined', false],
]) {
  const navigations = [];
  const page = {
    evaluate: async () => desktop,
    cdp: async (method, params) => {
      if (method === 'Page.getFrameTree') return { frameTree: { childFrames: [{ frame: { id: 'frame', url } }] } };
      assert.equal(method, 'Page.navigate');
      navigations.push(params);
    },
  };
  assert.equal(await restoreDesktopActivity(page, snapshot), expected);
  assert.equal(navigations.length, Number(expected));
  if (expected) {
    const target = new URL(navigations[0].url);
    assert.equal(target.searchParams.has('capture'), false);
    assert.equal(target.searchParams.get('progress'), 'undefined');
    assert.equal(target.searchParams.get('trans'), 'true');
    assert.equal(navigations[0].frameId, 'frame');
  }
}
console.log('5 desktop activity compatibility checks passed');
