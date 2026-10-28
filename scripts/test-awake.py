"""Check duplicate sleep prevention without changing the Mac's power state."""
import contextlib
import io
import os
from pathlib import Path
import runpy
import subprocess
import sys
from unittest.mock import patch

ensure_awake = runpy.run_path(str(Path(__file__).with_name('watch.py')))['ensure_awake']
cases = [
    ('pid 123(Amphetamine): [0x1] 01:00:00 PreventUserIdleSystemSleep named: "Amphetamine"', False),
    ('pid 124(caffeinate): [0x1] 00:10:00 PreventUserIdleSystemSleep named: "caffeinate"', False),
    ('pid 124(caffeinate): [0x1] 00:10:00 PreventSystemSleep named: "caffeinate"', False),
    ('pid 83(powerd): [0x1] 01:00:00 PreventUserIdleSystemSleep named: "Display on"', True),
    ('pid 123(Amphetamine): [0x1] 01:00:00 PreventUserIdleDisplaySleep named: "Display only"', True),
    ('PreventUserIdleSystemSleep 0', True),
]
for output, starts in cases:
    with patch.object(sys, 'platform', 'darwin'), patch('subprocess.check_output', return_value=output), patch('subprocess.Popen') as spawn, contextlib.redirect_stdout(io.StringIO()):
        ensure_awake()
    assert spawn.called is starts
    if starts:
        assert spawn.call_args.args[0] == ['caffeinate', '-i', '-w', str(os.getpid())]

with patch.object(sys, 'platform', 'linux'), patch('subprocess.check_output') as inspect, patch('subprocess.Popen') as spawn:
    ensure_awake()
    inspect.assert_not_called()
    spawn.assert_not_called()

with patch.object(sys, 'platform', 'darwin'), patch('subprocess.check_output', side_effect=subprocess.CalledProcessError(1, 'pmset')), patch('subprocess.Popen') as spawn, contextlib.redirect_stdout(io.StringIO()):
    ensure_awake()
    spawn.assert_not_called()
print('8 sleep-prevention checks passed')
