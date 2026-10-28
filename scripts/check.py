#!/usr/bin/env python3
"""Request a browser inspection and recover a stopped watcher every 30 minutes."""
import argparse
from datetime import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import subprocess
import sys


def save_session(state, argv):
    config = {'command': [sys.executable, str(Path(__file__).resolve().with_name('watch.py')), *argv],
              'env': {k: os.environ[k] for k in ('PATH', 'CODEX_HOME', 'CLAUDE_CONFIG_DIR') if k in os.environ}}
    path = state / 'watch-session.json'
    path.touch(mode=0o600, exist_ok=True)
    path.chmod(0o600)
    path.write_text(json.dumps(config))
    (state / 'watch.pid').write_text(str(os.getpid()))


def schedule(state):
    label = 'com.kehrd.autoplay.check.' + hashlib.sha256(str(state).encode()).hexdigest()[:12]
    return label, Path.home() / 'Library/LaunchAgents' / (label + '.plist')


def remove_schedule(state):
    label, path = schedule(state)
    if path.exists():
        path.unlink()
        subprocess.run(['launchctl', 'bootout', f'gui/{os.getuid()}/{label}'], capture_output=True)


def install(state):
    config = json.loads((state / 'watch-session.json').read_text())
    if '--no-auto-agent' in config['command']:
        raise ValueError('Periodic inspections require automatic agent mode')
    if (state / 'DONE').exists():
        remove_schedule(state)
        return
    label, path = schedule(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    job = {'Label': label, 'ProgramArguments': [sys.executable, str(Path(__file__).resolve()), '--state-dir', str(state)],
           'StartInterval': 1800, 'EnvironmentVariables': config['env'],
           'StandardOutPath': str(state / 'check.log'), 'StandardErrorPath': str(state / 'check.log')}
    path.write_bytes(plistlib.dumps(job))
    path.chmod(0o600)
    domain = f'gui/{os.getuid()}'
    loaded = subprocess.run(['launchctl', 'print', f'{domain}/{label}'], capture_output=True)
    if loaded.returncode:
        subprocess.run(['launchctl', 'bootstrap', domain, str(path)], check=True)
    subprocess.run(['launchctl', 'print', f'{domain}/{label}'], check=True, stdout=subprocess.DEVNULL)
    print(f'CHECK_SCHEDULED: every 1800 seconds; {label}', flush=True)


def inspect(state):
    if (state / 'DONE').exists():
        remove_schedule(state)
        return 'DONE: periodic checks removed'
    with (state / 'watch.lock').open('a') as watch_lock:
        try:
            fcntl.flock(watch_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            running = False
        except BlockingIOError:
            running = True
    stop = state / 'STOP'
    if stop.exists():
        reason = stop.read_text()
        retryable = re.fullmatch(r'Agent exited \d+|Agent did not resolve QUESTION after recovery retry; inspect agent.log', reason)
        if running or not retryable:
            return 'STOP: retained; no automatic restart'
    if not running:
        lease = state / 'agent.pid'
        if lease.exists():
            try:
                os.kill(int(lease.read_text()), 0)
                return 'WAIT: previous recovery agent is still running'
            except ProcessLookupError:
                lease.unlink()
        config = json.loads((state / 'watch-session.json').read_text())
        if stop.exists():
            stop.unlink()
    try:
        with (state / 'QUESTION').open('x') as question:
            question.write('30-minute check: inspect the current browser. If playback is advancing normally, leave it running and remove QUESTION. Otherwise recover within the authorized training scope; verify the timer advances before returning.')
    except FileExistsError:
        pass
    if not running:
        with (state / 'launcher.log').open('a') as log:
            process = subprocess.Popen(config['command'], env={**os.environ, **config['env']},
                                       cwd=Path(__file__).resolve().parent.parent, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
        (state / 'watch.pid').write_text(str(process.pid))
        return f'RESTARTED: watcher {process.pid}; inspection requested'
    return 'CHECK: inspection requested from the running watcher'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', required=True, type=Path)
    parser.add_argument('--install', action='store_true', help='Register a macOS LaunchAgent with a 30-minute interval')
    args = parser.parse_args()
    state = args.state_dir.resolve()
    if args.install:
        if sys.platform != 'darwin':
            parser.error('Scheduled checks currently use macOS launchd')
        install(state)
        return
    with (state / 'check.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        print(datetime.now().astimezone().isoformat(), inspect(state), flush=True)


if __name__ == '__main__':
    main()
