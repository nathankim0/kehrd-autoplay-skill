import { strict as assert } from 'node:assert';
import { settleTrainingDialogs } from './dialogs.mjs';
const confirm = { type: 'confirm', message: '시험을 제출 하시겠습니까? : \n제출된 답안은 수정제출이 불가능합니다.', url: 'https://kehrd.com/sanup/last.html' };
const correct = { type: 'alert', message: '정답입니다.', url: 'https://kehrd.com/sanup/test_proc.php' };
async function check(dialogs, options, accepted, blocked) {
  let index = 0;
  const page = {
    info: async () => { throw new Error('Runtime.evaluate blocked by dialog'); },
    acceptDialog: async () => { throw new Error('Runtime.evaluate blocked by dialog'); },
    events: async () => dialogs[index] ? [{ method: 'Page.javascriptDialogOpening', params: dialogs[index] }] : [],
    cdp: async (method, params) => {
      assert.equal(method, 'Page.handleJavaScriptDialog');
      assert.deepEqual(params, { accept: true });
      index++;
    },
  };
  const result = await settleTrainingDialogs(page, options);
  assert.equal(index, accepted);
  assert.equal(Boolean(result.blocked), blocked);
}
await check([confirm, correct], { allowSubmission: true }, 2, false);
await check([confirm], {}, 0, true);
await check([correct], {}, 1, false);
await check([{ ...correct, url: 'https://example.com' }], {}, 0, true);
await check([{ ...correct, message: '알 수 없는 안내' }], {}, 0, true);
await check([{ ...correct, message: '학습을 완료한 후 클릭 가능합니다.' }], {}, 1, false);
let reads = 0, accepts = 0;
const delayed = {
  events: async () => {
    reads++;
    if (reads === 1) return [{ method: 'Page.javascriptDialogOpening', params: confirm }];
    if (reads === 3) return [{ method: 'Page.javascriptDialogOpening', params: correct }];
    return [];
  },
  cdp: async () => { accepts++; },
};
assert.equal((await settleTrainingDialogs(delayed, { allowSubmission: true })).handled, 2);
assert.equal(accepts, 2, 'result alert arriving after confirmation must also close');
const closed = { events: async () => [{ method: 'Page.javascriptDialogOpening', params: correct }, { method: 'Page.javascriptDialogClosed' }], cdp: async () => { throw new Error('must not accept an already-closed dialog'); } };
assert.equal((await settleTrainingDialogs(closed)).handled, 0);
console.log('8 dialog behavior checks passed');
