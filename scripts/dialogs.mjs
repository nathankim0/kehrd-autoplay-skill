// Submission confirmation is accepted only after the agent intentionally submits an answer.
export async function settleTrainingDialogs(page, { allowSubmission = false, dialog: initialDialog = null } = {}) {
  let dialog = initialDialog, handled = 0, quiet = 0;
  for (let step = 0; step < 12; step++) {
    // info()/acceptDialog() can evaluate page JavaScript, which a modal dialog blocks.
    for (const event of await page.events()) {
      if (event.method === 'Page.javascriptDialogOpening') dialog = event.params;
      if (event.method === 'Page.javascriptDialogClosed') dialog = null;
    }
    if (!dialog) {
      if (handled && quiet++ < 2) {
        await new Promise(resolve => setTimeout(resolve, 250));
        continue;
      }
      return { handled, blocked: null };
    }
    let host;
    try { host = new URL(dialog.url).hostname; } catch { return { handled, blocked: dialog }; }
    const trusted = host === 'kehrd.com' || host.endsWith('.kehrd.com');
    const notice = dialog.type === 'alert' && /^(정답입니다\.|학습을 완료한 후 클릭 가능합니다\.)$/.test(dialog.message.trim());
    const submission = allowSubmission && dialog.type === 'confirm' && dialog.message.startsWith('시험을 제출 하시겠습니까?');
    if (!trusted || (!notice && !submission)) return { handled, blocked: dialog };
    if (handled >= 6) break;
    try {
      await page.cdp('Page.handleJavaScriptDialog', { accept: true }, { timeout: 5000 });
      handled++;
    } catch (error) {
      if (!/No dialog is showing/i.test(error.message)) throw error;
    }
    dialog = null;
    quiet = 0;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  return { blocked: { message: 'Repeated dialogs require inspection.' } };
}
