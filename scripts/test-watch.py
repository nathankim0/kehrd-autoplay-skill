"""Check runner handoff without launching a browser or sending notifications."""
import contextlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import patch
import agent_accounts

main = runpy.run_path(str(Path(__file__).with_name('watch.py')))['main']
accounts_patch = patch.object(agent_accounts, 'discover_accounts', return_value=[('codex', Path('/fake/.codex'))])
accounts_patch.start()
for extra, expected in [([], 'p1'), (['--current-lesson-only'], None), (['--playlist-page', 'p7'], 'p7')]:
    with tempfile.TemporaryDirectory() as state:
        state = Path(state)
        calls = []

        def run(command, **kwargs):
            config = json.loads(kwargs['input'].splitlines()[0].removeprefix('globalThis.kehrdConfig = ').removesuffix(';'))
            assert config['playlistPage'] == expected
            calls.append(config)
            (state / ('QUESTION' if len(calls) == 1 else 'DONE')).write_text('observed state')
            return subprocess.CompletedProcess(command, 0)

        def sleep(seconds):
            assert len(calls) == 1, 'must not replay browser actions during handoff'
            (state / 'player.json').write_text('{"page":"p5"}')
            (state / 'QUESTION').unlink()

        argv = ['watch.py', '--space', '1', '--state-dir', str(state), '--no-auto-agent', *extra]
        with patch.object(sys, 'argv', argv), patch.object(sys, 'platform', 'linux'), patch('subprocess.run', side_effect=run), patch('time.sleep', side_effect=sleep), patch('shutil.which', return_value=None), contextlib.redirect_stdout(io.StringIO()) as output:
            assert main() == 0
        assert len(calls) == 2, 'same runner must resume after handoff'
        assert output.getvalue().count('ACTION_REQUIRED') == 1
print('3 default-mode and continuous-handoff checks passed')

for extra, outcome in [([], 'success'), ([], 'failure'), (['--auto-agent'], 'success'), ([], 'retry'), ([], 'stop')]:
    with tempfile.TemporaryDirectory() as state:
        state = Path(state)
        (state / 'QUESTION').write_text('assessment needs attention')
        agents = []

        def run(command, **kwargs):
            if command[0] == 'codex':
                assert command[command.index('--model') + 1] == 'gpt-6.1-terra'
                assert 'model_reasoning_effort="low"' in command
                assert '--ignore-user-config' in command
                assert kwargs['timeout'] == 600
                agents.append(command)
                context = json.loads(kwargs['input'].split('Session: ')[-1])
                assert context['attempt'] == len(agents)
                if outcome == 'success' or (outcome == 'retry' and len(agents) == 2):
                    (state / 'QUESTION').unlink()
                if outcome == 'stop':
                    (state / 'STOP').write_text('user took control')
                if outcome == 'retry' and len(agents) == 1:
                    return subprocess.CompletedProcess(command, 1)
            else:
                (state / 'DONE').write_text('completed')
            return subprocess.CompletedProcess(command, 0)

        argv = ['watch.py', '--space', '1', '--state-dir', str(state), *extra]
        with patch.object(sys, 'argv', argv), patch.object(sys, 'platform', 'linux'), patch('subprocess.run', side_effect=run), patch('shutil.which', return_value=None), contextlib.redirect_stdout(io.StringIO()):
            assert main() == (2 if outcome in ('failure', 'stop') else 0)
        assert len(agents) == (2 if outcome in ('failure', 'retry') else 1), 'allow only one recovery retry and respect explicit STOP'
        assert (state / 'STOP').exists() == (outcome in ('failure', 'stop'))
        if outcome == 'stop':
            assert (state / 'STOP').read_text() == 'user took control'
print('5 default Terra invocation, retry, and failure-boundary checks passed')

with tempfile.TemporaryDirectory() as state:
    state = Path(state)
    (state / 'QUESTION').write_text('assessment needs attention')
    argv = ['watch.py', '--space', '1', '--state-dir', str(state)]
    with patch.object(sys, 'argv', argv), patch.object(sys, 'platform', 'linux'), patch('subprocess.run', side_effect=subprocess.TimeoutExpired('codex', 600)) as run, patch('shutil.which', return_value=None), contextlib.redirect_stdout(io.StringIO()):
        assert main() == 2
        assert run.call_count == 1, 'do not overlap an agent whose timeout state is uncertain'
        assert (state / 'STOP').exists()
print('1 agent-timeout boundary check passed')

profiles = [('codex', Path('/fake/.codex')), ('codex', Path('/fake/.codex2')), ('claude', Path('/fake/.claude'))]
for outcome in ('recovered', 'exhausted', 'ordinary_error'):
    with tempfile.TemporaryDirectory() as state:
        state = Path(state)
        (state / 'QUESTION').write_text('continue current browser state')
        used = []

        def account_run(account, prompt, folder):
            used.append(account)
            if outcome == 'ordinary_error':
                return subprocess.CompletedProcess([], 1), False
            if account == profiles[-1] and outcome == 'recovered':
                (folder / 'QUESTION').unlink()
                return subprocess.CompletedProcess([], 0), False
            return subprocess.CompletedProcess([], 1), True

        def browser_run(command, **kwargs):
            (state / 'DONE').write_text('completed')
            return subprocess.CompletedProcess(command, 0)

        def wait_for_quota(seconds):
            assert 0 < seconds <= 60
            (state / 'STOP').write_text('user stopped while waiting')

        argv = ['watch.py', '--space', '1', '--state-dir', str(state)]
        with patch.object(sys, 'argv', argv), patch.object(sys, 'platform', 'linux'), patch.object(agent_accounts, 'discover_accounts', return_value=profiles), patch.object(agent_accounts, 'run_account', side_effect=account_run), patch('subprocess.run', side_effect=browser_run), patch('time.sleep', side_effect=wait_for_quota) as sleep, patch('shutil.which', return_value=None), contextlib.redirect_stdout(io.StringIO()):
            assert main() == (0 if outcome == 'recovered' else 2)
        assert used == ([profiles[0], profiles[0]] if outcome == 'ordinary_error' else profiles), 'switch accounts only for usage limits'
        assert sleep.called is (outcome == 'exhausted'), 'wait for quota rather than exiting after all accounts are limited'
print('3 quota rotation, ordinary-error boundary, and exhausted-pool checks passed')

with tempfile.TemporaryDirectory() as state:
    state = Path(state)
    (state / 'QUESTION').write_text('resume when quota returns')
    used = []
    clock = [100000]

    def account_run(account, prompt, folder):
        used.append(account)
        if len(used) == 3:
            (folder / 'QUESTION').unlink()
            return subprocess.CompletedProcess([], 0), False
        return subprocess.CompletedProcess([], 1), True

    def browser_run(command, **kwargs):
        (state / 'DONE').write_text('completed')
        return subprocess.CompletedProcess(command, 0)

    def reset_quota(seconds):
        clock[0] += 901

    argv = ['watch.py', '--space', '1', '--state-dir', str(state)]
    with patch.object(sys, 'argv', argv), patch.object(sys, 'platform', 'linux'), patch.object(agent_accounts, 'discover_accounts', return_value=profiles[:2]), patch.object(agent_accounts, 'run_account', side_effect=account_run), patch('subprocess.run', side_effect=browser_run), patch('time.time', side_effect=lambda: clock[0]), patch('time.sleep', side_effect=reset_quota), patch('shutil.which', return_value=None), contextlib.redirect_stdout(io.StringIO()):
        assert main() == 0
    assert used == [profiles[0], profiles[1], profiles[0]], 'return to the primary account after the quota recheck interval'
print('1 quota-reset resume check passed')
accounts_patch.stop()
