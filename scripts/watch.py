#!/usr/bin/env python3
"""Keep KEHRD playback running through lesson changes and agent handoffs."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


def ensure_awake():
    # shortcut: check at startup; add periodic checks if existing awake sessions can end mid-course.
    if sys.platform != 'darwin':
        return
    try:
        assertions = subprocess.check_output(['pmset', '-g', 'assertions'], text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        print('KEEP_AWAKE: could not inspect power assertions; no extra caffeinate started', flush=True)
        return
    active = re.search(r'^\s*pid \d+\((?:Amphetamine|caffeinate)\):.*\b(?:PreventUserIdleSystemSleep|PreventSystemSleep|NoIdleSleepAssertion)\b', assertions, re.MULTILINE)
    if active:
        print('KEEP_AWAKE: Amphetamine or caffeinate already active; reusing it', flush=True)
        return
    try:
        subprocess.Popen(['caffeinate', '-i', '-w', str(os.getpid())], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print('KEEP_AWAKE: started caffeinate for this watcher', flush=True)
    except OSError:
        print('KEEP_AWAKE: caffeinate could not start', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--space', type=int, required=True)
    parser.add_argument('--page', default='p2')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--playlist-page', default='p1', help='Classroom detail page (default: p1); continue all remaining courses')
    mode.add_argument('--current-lesson-only', dest='playlist_page', action='store_const', const=None, help='Stop after the current lesson reaches 100%%')
    parser.add_argument('--state-dir', type=Path, required=True)
    agent_mode = parser.add_mutually_exclusive_group()
    agent_mode.add_argument('--auto-agent', action='store_true', default=True, help='Call GPT-6.1 Terra for handoffs (default: enabled)')
    agent_mode.add_argument('--no-auto-agent', dest='auto_agent', action='store_false', help='Let the active agent handle questions without launching Codex')
    args = parser.parse_args()
    state = args.state_dir.resolve()
    state.mkdir(parents=True, exist_ok=True)
    with (state / 'watch.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, 'A watcher already owns this state directory.\n')
        ensure_awake()
        source = '\n'.join(Path(__file__).with_name(name).read_text() for name in ('dialogs.mjs', 'playlist.mjs', 'watch.mjs'))
        config = json.dumps({'space': args.space, 'page': args.page, 'playlistPage': args.playlist_page, 'state': str(state)})
        with (state / 'runner.log').open('a') as log:
            last_question = None
            agent_attempts = 0
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
                        agent_attempts += 1
                        context = json.dumps({'space': args.space, 'page': args.page, 'classroom': args.playlist_page, 'state': str(state), 'attempt': agent_attempts}, ensure_ascii=False)
                        prompt = Path(__file__).with_name('agent-task.md').read_text() + '\nSession: ' + context
                        command = ['codex', '--no-daemon', '-a', 'never', '-c', 'model_reasoning_effort="low"', 'exec', '--ignore-user-config', '--sandbox', 'danger-full-access', '--model', 'gpt-6.1-terra', '--skip-git-repo-check', '--cd', str(Path(__file__).resolve().parent.parent), '--output-last-message', str(state / 'agent-last-message.txt'), '-']
                        print('AGENT_START: gpt-6.1-terra', flush=True)
                        try:
                            with (state / 'agent.log').open('a') as agent_log:
                                agent = subprocess.run(command, input=prompt, text=True, stdout=agent_log, stderr=agent_log, timeout=600)
                            failure = f'Agent exited {agent.returncode}' if agent.returncode else None
                        except OSError as error:
                            (state / 'STOP').write_text(str(error))
                            failure = str(error)
                        except subprocess.TimeoutExpired as error:
                            (state / 'STOP').write_text(str(error))
                            failure = str(error)
                        if failure or (state / 'QUESTION').exists():
                            if not (state / 'STOP').exists() and agent_attempts < 2:
                                print('AGENT_RETRY: inspect current state before any resubmission', flush=True)
                                continue
                            if not (state / 'STOP').exists():
                                (state / 'STOP').write_text(failure or 'Agent did not resolve QUESTION after recovery retry; inspect agent.log')
                            print(f'AGENT_FAILED: {state / "agent.log"}', flush=True)
                        else:
                            agent_attempts = 0
                            print('AGENT_RESOLVED: resuming browser monitoring', flush=True)
                        continue
                    time.sleep(1)
                    continue
                last_question = None
                agent_attempts = 0
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
