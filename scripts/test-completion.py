"""Check completion requires every saved PDF and launches no blocking dialog."""
import io
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import completion

with tempfile.TemporaryDirectory() as root:
    state = Path(root)
    folder = state / 'certificates'
    folder.mkdir()
    pdf = folder / 'course.pdf'
    data = b'%PDF-1.7\n' + b'%' * 1100 + b'\n%%EOF\n'
    pdf.write_bytes(data)
    courses = [{'url': 'https://kehrd.com/mypage/myclass_detail.html?no=sample', 'status': '수료'}]
    manifest = {'directory': str(folder), 'files': [{'course': courses[0]['url'], 'file': str(pdf)}]}
    (state / 'playlist.json').write_text(json.dumps(courses))
    (state / 'certificates.json').write_text(json.dumps(manifest))
    assert completion.verified_certificates(state) == manifest
    for bad in (b'', b'<html>login required</html>', data[:-10]):
        pdf.write_bytes(bad)
        try:
            completion.verified_certificates(state)
        except ValueError:
            pass
        else:
            raise AssertionError('reject incomplete or non-PDF certificates')
    pdf.write_bytes(data)
    (state / 'playlist.json').write_text(json.dumps([{**courses[0], 'status': '미수료'}]))
    try:
        completion.verified_certificates(state)
    except ValueError:
        pass
    else:
        raise AssertionError('do not report completion for an unfinished course')
    (state / 'playlist.json').write_text(json.dumps(courses + [{'url': 'https://kehrd.com/mypage/myclass_detail.html?no=missing', 'status': '수료'}]))
    try:
        completion.verified_certificates(state)
    except ValueError:
        pass
    else:
        raise AssertionError('require a certificate for every completed course')

    manifest['files'].append({'course': 'https://kehrd.com/mypage/myclass_detail.html?no=missing', 'file': str(pdf)})
    (state / 'certificates.json').write_text(json.dumps(manifest))
    try:
        completion.verified_certificates(state)
    except ValueError:
        pass
    else:
        raise AssertionError('one PDF cannot stand in for multiple certificates')
    manifest['files'].pop()
    (state / 'certificates.json').write_text(json.dumps(manifest))

    for platform, executable in [('darwin', 'osascript'), ('linux', 'notify-send')]:
        with patch.object(completion.sys, 'platform', platform), patch.object(completion.shutil, 'which', side_effect=lambda name: name == executable), patch.object(completion.subprocess, 'Popen') as launch:
            completion.notify(manifest, io.StringIO())
            assert launch.call_args.args[0][0] == executable
            assert str(folder) in launch.call_args.args[0][-1]
            assert launch.call_args.kwargs['start_new_session'] is True
            assert 'timeout' not in launch.call_args.kwargs
    (state / 'playlist.json').write_text(json.dumps(courses))
    manifest['files'][0]['file'] = str(state / 'outside.pdf')
    (state / 'certificates.json').write_text(json.dumps(manifest))
    try:
        completion.verified_certificates(state)
    except ValueError:
        pass
    else:
        raise AssertionError('reject files outside the certificate directory')
print('10 PDF completeness, course coverage, path, and nonblocking-popup checks passed')
