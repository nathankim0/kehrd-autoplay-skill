import { strict as assert } from 'node:assert';
import { readFileSync } from 'node:fs';
const source = readFileSync(new URL('./playlist.mjs', import.meta.url), 'utf8');
const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
const advance = await new AsyncFunction(`${source}\nreturn advancePlaylist;`)();
const listUrl = 'https://kehrd.com/mypage/myclass.html';
const detailUrl = 'https://kehrd.com/mypage/myclass_detail.html?no=example';
async function check(evaluations, marker, expectedNavigation = []) {
  const writes = {}, navigation = [], clicks = [];
  const classroom = {
    reload: async () => {},
    evaluate: async () => { assert.ok(evaluations.length, 'unexpected DOM read'); return evaluations.shift(); },
    waitForEvent: async () => ({ label: 'p3', waitForLoadState: async () => {} }),
    click: async selector => clicks.push(selector),
    url: async () => detailUrl,
    goto: async url => navigation.push(url),
    snapshot: async () => 'observed classroom',
  };
  await advance({ page: () => classroom }, { click: async () => {} }, { playlistPage: 'p1' }, (name, text) => { writes[name] = text; }, () => {});
  assert.ok(marker in writes, `missing ${marker}`);
  assert.deepEqual(navigation, expectedNavigation);
  assert.equal(evaluations.length, 0);
  if (marker === 'player.json') {
    assert.equal(JSON.parse(writes[marker]).page, 'p3');
    assert.deepEqual(clicks, ['a.detail_btn >> nth=0']);
    assert.ok(!('DONE' in writes));
  } else assert.deepEqual(clicks, []);
}
await check([0], 'player.json');
await check([-1, true], 'QUESTION');
const nextUrl = 'https://kehrd.com/mypage/myclass_detail.html?no=next';
await check([-1, false, listUrl, [{ status: '수료' }, { status: '미수료', url: nextUrl }], 0], 'player.json', [listUrl, nextUrl]);
await check([-1, false, listUrl, [{ status: '수료' }]], 'DONE', [listUrl]);
await check([-1, false, listUrl, [{ status: '미수료' }]], 'QUESTION', [listUrl]);
await check([-1, false, listUrl, [{ status: '미수료', url: detailUrl }]], 'QUESTION', [listUrl]);
await check([-1, false, listUrl, [{ status: 'unknown' }]], 'QUESTION', [listUrl]);
await check([-1, false, listUrl, []], 'QUESTION', [listUrl]);
console.log('8 playlist behavior checks passed');
