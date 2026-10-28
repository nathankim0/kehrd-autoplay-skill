#!/usr/bin/env python3
"""Run bounded ego-browser rounds until completion or agent intervention."""
import argparse
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--space', type=int, required=True)
    parser.add_argument('--page', default='p2')
    parser.add_argument('--state-dir', type=Path, required=True)
    args = parser.parse_args()
    state = args.state_dir.resolve()
    state.mkdir(parents=True, exist_ok=True)
    with (state / 'watch.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, 'A watcher already owns this state directory.\n')
        source = Path(__file__).with_name('watch.mjs').read_text()
        config = json.dumps({'space': args.space, 'page': args.page, 'state': str(state)})
        with (state / 'runner.log').open('a') as log:
            while not any((state / name).exists() for name in ('DONE', 'QUESTION')):
                result = subprocess.run(['ego-browser', 'nodejs'], input=f'globalThis.kehrdConfig = {config};\n{source}', text=True, stdout=log, stderr=log)
                if result.returncode:
                    (state / 'QUESTION').write_text(f'ego-browser exited with code {result.returncode}; inspect runner.log')
                    break
            done = (state / 'DONE').exists()
            if shutil.which('osascript'):
                message = '진도율 100%. 자동 진행을 종료했습니다.' if done else '화면 확인 또는 중간 문제 풀이가 필요합니다.'
                notice = subprocess.run(['osascript', '-e', f'display notification "{message}" with title "안전보건교육" sound name "Glass"'], stdout=log, stderr=log)
                if notice.returncode:
                    log.write('Notification failed.\n')
        print(f'{"DONE" if done else "QUESTION"}: {state}', flush=True)
        return 0 if done else 2


if __name__ == '__main__':
    sys.exit(main())
