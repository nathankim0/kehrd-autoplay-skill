import { strict as assert } from 'node:assert';
import { settleTrainingDialogs } from './dialogs.mjs';
const confirm = { type: 'confirm', message: '시험을 제출 하시겠습니까? : \n제출된 답안은 수정제출이 불가능합니다.', url: 'https://kehrd.com/sanup/last.html' };
const correct = { type: 'alert', message: '정답입니다.', url: 'https://kehrd.com/sanup/test_proc.php' };
async function check(dialogs, options, accepted, blocked) {
  let index = 0;
  const page = { info: async () => ({ dialog: dialogs[index] }), acceptDialog: async () => { index++; } };
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
console.log('6 dialog behavior checks passed');
