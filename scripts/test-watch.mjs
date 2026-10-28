import { strict as assert } from 'node:assert';
import { mkdtempSync, readFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const source = readFileSync(new URL('./watch.mjs', import.meta.url), 'utf8');
const snapshot = (time, progress = '15', extra = '') => `iframe\n video\n text "${time}"\n${extra}\n text "02"\n text "/"\n text "06"\n button [ref=22]\nanchor\n text "1 차시 진도율 : "\n text "${progress}%"`;
async function check(snapshots, expected, expectedClicks = [], extraConfig = {}) {
  const state = mkdtempSync(join(tmpdir(), 'kehrd-test-'));
  const clicks = [];
  let index = 0;
  globalThis.kehrdConfig = { space: 1, page: 'p2', state, ...extraConfig };
  globalThis.advancePlaylist = async (task, page, config, write) => write('ADVANCED', '1');
  globalThis.taskSpace = async () => ({ page: () => ({
    info: async () => ({}),
    snapshot: async () => snapshots[Math.min(index++, snapshots.length - 1)],
    click: async ref => clicks.push(ref),
    waitForTimeout: async () => {},
  }) });
  try {
    await new (Object.getPrototypeOf(async function(){}).constructor)(source)();
    assert.ok(existsSync(join(state, expected)), expected);
    assert.deepEqual(clicks, expectedClicks);
  } finally { rmSync(state, { recursive: true, force: true }); }
}
await check(['text "차시 진도율 : "\n text "100%"'], 'DONE');
await check([snapshot('00:02 / 01:00', '15', 'radio "보기"')], 'QUESTION');
await check([snapshot('00:59 / 01:00')], 'QUESTION'); // Never advance early.
await check([snapshot('01:00 / 01:00'), snapshot('01:00 / 01:00'), snapshot('00:00 / 01:00', '100')], 'DONE', ['@22']);
await check([snapshot('00:02 / 01:00', 'unknown')], 'QUESTION');
await check(['unexpected screen'], 'QUESTION');
await check([snapshot('00:02 / 01:00', '100')], 'QUESTION', [], { playlistPage: 'p1' });
await check([snapshot('01:00 / 01:00', '100').replace('text "02"', 'text "06"')], 'ADVANCED', [], { playlistPage: 'p1' });
await check([snapshot('01:00 / 01:00', '100', 'radio "문제"').replace('text "02"', 'text "06"')], 'QUESTION', [], { playlistPage: 'p1' });
console.log('9 watcher behavior checks passed');
