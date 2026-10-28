import json
import os
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch
from agent_accounts import account_environment, discover_accounts, quota_error, run_account

with tempfile.TemporaryDirectory() as root:
    home = Path(root).resolve()
    for name in ('.codex', '.codex2', '.codex3', '.claude'):
        (home / name).mkdir()

    def status(command, **kwargs):
        env = kwargs['env']
        if command[0] == 'codex':
            return subprocess.CompletedProcess(command, 1 if env['CODEX_HOME'].endswith('.codex3') else 0, 'Logged in', '')
        return subprocess.CompletedProcess(command, 0, '{"loggedIn":true}', '')

    with patch('pathlib.Path.home', return_value=home), patch.dict(os.environ, {'CODEX_HOME': str(home / '.codex2')}, clear=True), patch('shutil.which', return_value='/fake/cli'), patch('subprocess.run', side_effect=status):
        assert discover_accounts() == [('codex', home / '.codex2'), ('codex', home / '.codex'), ('claude', home / '.claude')]
        assert 'CLAUDE_CONFIG_DIR' not in account_environment('claude', home / '.claude'), 'retain the default Claude keychain namespace'

quota_cases = [
    ({'type': 'error', 'message': "You've hit your usage limit."}, True),
    ({'type': 'turn.failed', 'error': {'code': 'usage_limit_reached'}}, True),
    ({'is_error': True, 'result': "You've hit your limit · resets later"}, True),
    ({'type': 'error', 'message': 'rate_limit_exceeded'}, True),
    ({'type': 'error', 'message': 'insufficient_quota'}, True),
    ({'type': 'error', 'message': 'network disconnected'}, False),
    ({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'rate_limit_exceeded'}}, False),
    ({'is_error': False, 'result': 'rate_limit_error'}, False),
]
for event, expected in quota_cases:
    assert quota_error(json.dumps(event)) is expected
assert quota_error('ERROR: HTTP 429 Too Many Requests')
assert not quota_error('The training question mentions usage_limit_reached')
assert quota_error(json.dumps({'is_error': True, 'result': 'rate_limit_error'}, indent=2))

for provider in ('codex', 'claude'):
    with tempfile.TemporaryDirectory() as root:
        state = Path(root)
        profile = state / 'profile'

        def execute(command, **kwargs):
            variable = 'CODEX_HOME' if provider == 'codex' else 'CLAUDE_CONFIG_DIR'
            assert kwargs['env'][variable] == str(profile)
            assert command[command.index('--model') + 1] == ('gpt-6.1-terra' if provider == 'codex' else 'sonnet')
            assert '--bare' not in command, 'Claude subscription login must remain available'
            assert kwargs['timeout'] == 600
            kwargs['stdout'].write('{"is_error":true,"result":"rate_limit_error"}\n')
            return subprocess.CompletedProcess(command, 1)

        before = dict(os.environ)
        with patch('subprocess.run', side_effect=execute):
            result, limited = run_account((provider, profile), 'continue the same task', state)
        assert limited and result.returncode == 1
        assert dict(os.environ) == before, 'switch child environment only'
print('15 account discovery, quota classification, and isolated-environment checks passed')
