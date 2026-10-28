"""Verify saved certificates before reporting completion and launch a nonblocking popup."""
import json
from pathlib import Path
import shutil
import subprocess
import sys


def verified_certificates(state):
    courses = json.loads((state / 'playlist.json').read_text())
    manifest = json.loads((state / 'certificates.json').read_text())
    if not courses or any(course.get('status') != '수료' or not course.get('url') for course in courses):
        raise ValueError('전체 과정의 수료 상태가 필요합니다.')
    records = {record['course']: record for record in manifest['files']}
    directory = Path(manifest['directory']).resolve()
    saved_paths = set()
    for course in courses:
        record = records.get(course['url'])
        if not record:
            raise ValueError('아직 저장하지 않은 수료증이 있습니다.')
        file = Path(record['file']).resolve()
        if directory not in file.parents or file.suffix.lower() != '.pdf' or file in saved_paths:
            raise ValueError('수료증 저장 경로를 확인해야 합니다.')
        saved_paths.add(file)
        data = file.read_bytes()
        if len(data) <= 1024 or not data.startswith(b'%PDF-') or b'%%EOF' not in data[-1024:]:
            raise ValueError('수료증 PDF가 비어 있거나 저장이 완료되지 않았습니다.')
    return manifest


def notify(manifest, log):
    message = f"남은 교육을 모두 수료했습니다.\n수료증 {len(manifest['files'])}개 저장 완료\n\n{manifest['directory']}"
    if sys.platform == 'darwin' and shutil.which('osascript'):
        script = 'on run argv\n display dialog (item 1 of argv) with title "KEHRD 교육 완료" buttons {"확인"} default button "확인" giving up after 60\nend run'
        command = ['osascript', '-e', script, message]
    elif shutil.which('notify-send'):
        command = ['notify-send', 'KEHRD 교육 완료', message]
    else:
        print(message, flush=True)
        return
    # The popup must not keep the watcher alive while waiting for confirmation.
    subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
