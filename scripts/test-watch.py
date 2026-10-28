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

main = runpy.run_path(str(Path(__file__).with_name('watch.py')))['main']
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

        argv = ['watch.py', '--space', '1', '--state-dir', str(state), *extra]
        with patch.object(sys, 'argv', argv), patch('subprocess.run', side_effect=run), patch('time.sleep', side_effect=sleep), patch('shutil.which', return_value=None), contextlib.redirect_stdout(io.StringIO()) as output:
            assert main() == 0
        assert len(calls) == 2, 'same runner must resume after handoff'
        assert output.getvalue().count('ACTION_REQUIRED') == 1
print('3 default-mode and continuous-handoff checks passed')

for resolves in (True, False):
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
                if resolves:
                    (state / 'QUESTION').unlink()
            else:
                (state / 'DONE').write_text('completed')
            return subprocess.CompletedProcess(command, 0)

        argv = ['watch.py', '--space', '1', '--state-dir', str(state), '--auto-agent']
        with patch.object(sys, 'argv', argv), patch('subprocess.run', side_effect=run), patch('shutil.which', return_value=None), contextlib.redirect_stdout(io.StringIO()):
            assert main() == (0 if resolves else 2)
        assert len(agents) == 1, 'do not repeatedly bill for an unresolved question'
        assert (state / 'STOP').exists() is not resolves
print('2 Terra invocation and failure-boundary checks passed')
