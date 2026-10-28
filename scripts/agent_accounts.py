"""Use existing CLI logins without copying or printing their credentials."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess


def account_environment(provider, profile):
    env = dict(os.environ)
    variable = 'CODEX_HOME' if provider == 'codex' else 'CLAUDE_CONFIG_DIR'
    explicit = env.get(variable)
    # Claude's default keychain login differs from an explicitly named config directory.
    if provider == 'claude' and profile == (Path.home() / '.claude').resolve() and not (explicit and Path(explicit).expanduser().resolve() == profile):
        env.pop(variable, None)
    else:
        env[variable] = str(profile)
    return env


def discover_accounts():
    accounts = []
    for provider, variable in (('codex', 'CODEX_HOME'), ('claude', 'CLAUDE_CONFIG_DIR')):
        if not shutil.which(provider):
            continue
        home = Path.home()
        profiles = [Path(os.environ.get(variable, str(home / f'.{provider}'))), home / f'.{provider}']
        profiles.extend(sorted((p for p in home.iterdir() if re.fullmatch(rf'\.{provider}\d+', p.name)), key=lambda p: (len(p.name), p.name)))
        seen = set()
        for profile in profiles:
            profile = profile.expanduser().resolve()
            if profile in seen or not profile.is_dir():
                continue
            seen.add(profile)
            env = account_environment(provider, profile)
            command = ['codex', 'login', 'status'] if provider == 'codex' else ['claude', 'auth', 'status', '--json']
            try:
                status = subprocess.run(command, env=env, capture_output=True, text=True, timeout=15)
                logged_in = status.returncode == 0 and (provider == 'codex' or json.loads(status.stdout).get('loggedIn') is True)
            except (OSError, subprocess.TimeoutExpired, ValueError):
                logged_in = False
            if logged_in:
                accounts.append((provider, profile))
    return accounts


def quota_error(output):
    messages = []
    try:
        output = json.dumps(json.loads(output), ensure_ascii=False)
    except ValueError:
        pass
    for line in output.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            if re.search(r'\b(?:ERROR|Error|API Error)\b|^(?:You.ve|Usage limit|Rate limit)', line):
                messages.append(line)
            continue
        if isinstance(event, dict) and (event.get('type') in ('error', 'turn.failed') or event.get('is_error') is True):
            messages.append(json.dumps(event, ensure_ascii=False))
    return bool(re.search(r'usage_limit_reached|rate_limit_exceeded|insufficient_quota|rate_limit_error|out of credits|you.ve (?:hit|reached) (?:your |the )?(?:usage )?limit|usage limit (?:reached|exceeded)|rate limit (?:reached|exceeded)|too many requests|\b429\b', '\n'.join(messages), re.IGNORECASE))


def run_account(account, prompt, state):
    provider, profile = account
    env = account_environment(provider, profile)
    if provider == 'codex':
        command = ['codex', '--no-daemon', '-a', 'never', '-c', 'model_reasoning_effort="low"', 'exec', '--ignore-user-config', '--json', '--sandbox', 'danger-full-access', '--model', 'gpt-6.1-terra', '--skip-git-repo-check', '--cd', str(Path(__file__).resolve().parent.parent), '--output-last-message', str(state / 'agent-last-message.txt'), '-']
    else:
        tools = 'Bash,Read,Write,WebSearch,WebFetch'
        command = ['claude', '-p', '--model', 'sonnet', '--effort', 'low', '--output-format', 'json', '--strict-mcp-config', '--setting-sources', '', '--permission-mode', 'dontAsk', '--permission-prompts', 'none', '--allowedTools', tools, '--tools', tools, '--no-session-persistence']
    with (state / 'agent.log').open('a+') as log:
        log.seek(0, 2)
        offset = log.tell()
        with subprocess.Popen(command, stdin=subprocess.PIPE, text=True, env=env, cwd=Path(__file__).resolve().parent.parent, stdout=log, stderr=log) as process:
            (state / 'agent.pid').write_text(str(process.pid))
            try:
                process.communicate(prompt, timeout=600)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                raise
            finally:
                (state / 'agent.pid').unlink(missing_ok=True)
            result = subprocess.CompletedProcess(command, process.returncode)
        log.flush()
        log.seek(offset)
        output = log.read()
    if provider == 'claude':
        for line in output.splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            if isinstance(event, dict) and isinstance(event.get('result'), str):
                (state / 'agent-last-message.txt').write_text(event['result'])
    return result, quota_error(output)
