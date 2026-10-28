"""Verify scheduled recovery without launchd, a browser, or real agents."""
import fcntl
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
from unittest.mock import MagicMock, patch
import check

with tempfile.TemporaryDirectory() as root:
    state = Path(root)
    with patch.dict(os.environ, {'CODEX_HOME': '/fake/.codex', 'SECRET_TOKEN': 'private'}):
        check.save_session(state, ['--space', '1', '--state-dir', str(state)])
    config = json.loads((state / 'watch-session.json').read_text())
    assert config['env']['CODEX_HOME'] == '/fake/.codex'
    assert 'SECRET_TOKEN' not in config['env']
    assert (state / 'watch-session.json').stat().st_mode & 0o777 == 0o600

    with (state / 'watch.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with patch('subprocess.Popen') as launch:
            assert check.inspect(state).startswith('CHECK:')
            assert (state / 'QUESTION').exists()
            launch.assert_not_called()
        (state / 'QUESTION').write_text('quiz already pending')
        check.inspect(state)
        assert (state / 'QUESTION').read_text() == 'quiz already pending'

    with patch('subprocess.Popen', return_value=MagicMock(pid=2345)) as launch:
        assert check.inspect(state).startswith('RESTARTED:')
        assert launch.call_args.kwargs['start_new_session'] is True
        assert launch.call_args.kwargs['env']['CODEX_HOME'] == '/fake/.codex'

    for reason in ('user took control', 'login required', 'codex timed out after 600 seconds'):
        (state / 'STOP').write_text(reason)
        with patch('subprocess.Popen') as launch:
            assert check.inspect(state).startswith('STOP:')
            assert (state / 'STOP').read_text() == reason
            launch.assert_not_called()
    (state / 'STOP').write_text('Agent exited 1')
    with patch('subprocess.Popen', return_value=MagicMock(pid=3456)):
        assert check.inspect(state).startswith('RESTARTED:')
        assert not (state / 'STOP').exists()

    (state / 'agent.pid').write_text('9999')
    with patch('os.kill') as alive, patch('subprocess.Popen') as launch:
        assert check.inspect(state).startswith('WAIT:')
        launch.assert_not_called()
    with patch('os.kill', side_effect=ProcessLookupError), patch('subprocess.Popen', return_value=MagicMock(pid=4567)):
        assert check.inspect(state).startswith('RESTARTED:')
        assert not (state / 'agent.pid').exists()

    with patch('pathlib.Path.home', return_value=state), patch('subprocess.run', return_value=subprocess.CompletedProcess([], 0)) as run:
        check.install(state)
        label, path = check.schedule(state)
        job = plistlib.loads(path.read_bytes())
        assert job['StartInterval'] == 1800
        assert job['ProgramArguments'][-1] == str(state)
        (state / 'DONE').write_text('all completed')
        with patch('subprocess.Popen') as launch:
            assert check.inspect(state).startswith('DONE:')
            launch.assert_not_called()
        assert not path.exists()
        assert run.call_args.args[0] == ['launchctl', 'bootout', f'gui/{os.getuid()}/{label}']
print('11 session, periodic inspection, restart, overlap, STOP, and completion checks passed')
