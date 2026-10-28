// Submission confirmation is accepted only after the agent intentionally submits an answer.
export async function settleTrainingDialogs(page, { allowSubmission = false } = {}) {
  for (let handled = 0; handled < 6; handled++) {
    const { dialog } = await page.info();
    if (!dialog) return { handled, blocked: null };
    let host;
    try { host = new URL(dialog.url).hostname; } catch { return { handled, blocked: dialog }; }
    const trusted = host === 'kehrd.com' || host.endsWith('.kehrd.com');
    const notice = dialog.type === 'alert' && /^(정답입니다\.|학습을 완료한 후 클릭 가능합니다\.)$/.test(dialog.message.trim());
    const submission = allowSubmission && dialog.type === 'confirm' && dialog.message.startsWith('시험을 제출 하시겠습니까?');
    if (!trusted || (!notice && !submission)) return { handled, blocked: dialog };
    await page.acceptDialog();
  }
  return { blocked: { message: 'Repeated dialogs require inspection.' } };
}
