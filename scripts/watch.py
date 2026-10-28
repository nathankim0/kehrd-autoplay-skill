#!/usr/bin/env python3
"""Keep KEHRD playback running through lesson changes and agent handoffs."""
import argparse
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--space', type=int, required=True)
    parser.add_argument('--page', default='p2')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--playlist-page', default='p1', help='Classroom detail page (default: p1); continue all remaining courses')
    mode.add_argument('--current-lesson-only', dest='playlist_page', action='store_const', const=None, help='Stop after the current lesson reaches 100%%')
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--auto-agent', action='store_true', help='Call GPT-6.1 Terra for handoffs; requires explicit user authorization')
    args = parser.parse_args()
    state = args.state_dir.resolve()
    state.mkdir(parents=True, exist_ok=True)
    with (state / 'watch.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, 'A watcher already owns this state directory.\n')
        source = '\n'.join(Path(__file__).with_name(name).read_text() for name in ('dialogs.mjs', 'playlist.mjs', 'watch.mjs'))
        config = json.dumps({'space': args.space, 'page': args.page, 'playlistPage': args.playlist_page, 'state': str(state)})
        with (state / 'runner.log').open('a') as log:
            last_question = None
            while not any((state / name).exists() for name in ('DONE', 'STOP')):
                if (state / 'QUESTION').exists():
                    try:
                        question = (state / 'QUESTION').read_text()
                    except FileNotFoundError:
                        continue
                    if question != last_question:
                        print(f'ACTION_REQUIRED: {state / "QUESTION"}', flush=True)
                        last_question = question
                    if args.auto_agent:
                        context = json.dumps({'space': args.space, 'page': args.page, 'classroom': args.playlist_page, 'state': str(state)}, ensure_ascii=False)
                        prompt = Path(__file__).with_name('agent-task.md').read_text() + '\nSession: ' + context
                        command = ['codex', '--no-daemon', '-a', 'never', '-c', 'model_reasoning_effort="low"', 'exec', '--ignore-user-config', '--sandbox', 'danger-full-access', '--model', 'gpt-6.1-terra', '--skip-git-repo-check', '--cd', str(Path(__file__).resolve().parent.parent), '--output-last-message', str(state / 'agent-last-message.txt'), '-']
                        print('AGENT_START: gpt-6.1-terra', flush=True)
                        try:
                            with (state / 'agent.log').open('a') as agent_log:
                                agent = subprocess.run(command, input=prompt, text=True, stdout=agent_log, stderr=agent_log, timeout=600)
                            failure = f'Agent exited {agent.returncode}' if agent.returncode else None
                        except (OSError, subprocess.TimeoutExpired) as error:
                            failure = str(error)
                        if failure or (state / 'QUESTION').exists():
                            (state / 'STOP').write_text(failure or 'Agent did not resolve QUESTION; inspect agent.log')
                            print(f'AGENT_FAILED: {state / "agent.log"}', flush=True)
                        else:
                            print('AGENT_RESOLVED: resuming browser monitoring', flush=True)
                        continue
                    time.sleep(1)
                    continue
                last_question = None
                result = subprocess.run(['ego-browser', 'nodejs'], input=f'globalThis.kehrdConfig = {config};\n{source}', text=True, stdout=log, stderr=log)
                if result.returncode:
                    (state / 'QUESTION').write_text(f'ego-browser exited with code {result.returncode}; inspect runner.log')
            done = (state / 'DONE').exists()
            if done and shutil.which('osascript'):
                message = '남은 교육을 모두 수료했습니다.' if args.playlist_page else '진도율 100%. 자동 진행을 종료했습니다.'
                notice = subprocess.run(['osascript', '-e', f'display notification "{message}" with title "안전보건교육" sound name "Glass"'], stdout=log, stderr=log)
                if notice.returncode:
                    log.write('Notification failed.\n')
        print(f'{"DONE" if done else "STOP"}: {state}', flush=True)
        return 0 if done else 2


if __name__ == '__main__':
    sys.exit(main())
