"""Build six install archives locally; never tag, upload, install or overwrite.

Usage: python packaging/build_candidate.py NEW_OUTPUT_DIRECTORY
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / 'skills/multi-agent-folder-cleanup'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    output = Path(sys.argv[1]).resolve()
    version = re.search(r'^  version: "([^"]+)"', (SKILL / 'SKILL.md').read_text(encoding='utf-8'), re.M)[1]
    for name in ('.codex-plugin', '.claude-plugin'):
        assert json.loads((REPO / name / 'plugin.json').read_text())['version'] == version
    files = {}
    for p in sorted(SKILL.rglob('*')):
        if '__pycache__' in p.parts or p.suffix == '.pyc' or not p.is_file():
            continue
        if p.is_symlink():
            raise ValueError('Refusing linked package source')
        files[p.relative_to(SKILL).as_posix()] = p.read_bytes()
    root = 'multi-agent-folder-cleanup/'
    skill = {root + name: data for name, data in files.items()}
    portable = dict(skill)
    portable['LICENSE'] = (REPO / 'LICENSE').read_bytes()
    portable['INSTALL.md'] = (REPO / 'packaging/INSTALL-portable.md').read_bytes()
    packages = {'skill': skill, 'portable': portable}
    for flavor, metadata in [('openai', '.codex-plugin'), ('claude', '.claude-plugin')]:
        items = {root + 'skills/' + name: data for name, data in skill.items()}
        for p in sorted((REPO / metadata).glob('*.json')):
            items[root + metadata + '/' + p.name] = p.read_bytes()
        for name in ('LICENSE', 'README.md', 'CHANGELOG.md'):
            items[root + name] = (REPO / name).read_bytes()
        items[root + 'INSTALL.md'] = (REPO / ('packaging/INSTALL-' + flavor + '.md')).read_bytes()
        packages[flavor] = items
    packages['gemini-apps'] = {root + name: data for name, data in files.items()
        if not name.startswith(('agents/', 'references/project-rules/')) and not name.endswith(('.ps1', '.yaml'))}
    packages['gemini-apps'][root + 'LICENSE.txt'] = (REPO / 'LICENSE').read_bytes()
    packages['project-rules'] = {'project-rules/' + name.split('references/project-rules/', 1)[1]: data
        for name, data in files.items() if name.startswith('references/project-rules/')}
    output.mkdir(parents=True, exist_ok=False)
    evidence = {'version': version, 'status': 'local candidate, not published',
                'source_files': {n: digest(b) for n, b in files.items()}, 'packages': {}}
    for flavor, items in packages.items():
        archive = output / ('multi-agent-folder-cleanup-' + version + '-' + flavor + '.zip')
        with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
            for name, data in sorted(items.items()):
                info = zipfile.ZipInfo(name, date_time=(2026, 10, 2, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(info, data)
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            assert set(z.namelist()) == set(items) and len(z.namelist()) == len(items)
            for name, data in items.items():
                assert z.read(name) == data, name
            with tempfile.TemporaryDirectory(prefix='cleanup-package-') as tmp:
                # Members were constructed above, never accepted from an incoming archive.
                z.extractall(tmp)
                script_root = Path(tmp) / root
                if flavor in ('openai', 'claude'):
                    script_root /= 'skills/multi-agent-folder-cleanup'
                if flavor != 'project-rules':
                    for name in ('audit_folder.py', 'verify_move.py'):
                        result = subprocess.run([sys.executable, str(script_root / 'scripts' / name), '--version'], capture_output=True, text=True, check=True)
                        assert result.stdout.strip().endswith(version), result.stdout
                    fixture = Path(tmp) / 'fixture'
                    fixture.mkdir()
                    (fixture / 'note.md').write_text('synthetic fixture', encoding='utf-8')
                    subprocess.run([sys.executable, str(script_root / 'scripts/audit_folder.py'), '--root', str(fixture), '--brief'], capture_output=True, check=True)
                    if flavor != 'gemini-apps':
                        ps = shutil.which('pwsh') or shutil.which('powershell.exe')
                        if not ps:
                            raise RuntimeError('PowerShell required for packaged smoke tests')
                        subprocess.run([ps, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(script_root / 'scripts/audit_folder.ps1'), '-Root', str(fixture), '-Brief'], capture_output=True, check=True)
        evidence['packages'][archive.name] = {'sha256': digest(archive.read_bytes()), 'files': len(items), 'byte_verified': True, 'smoke': flavor != 'project-rules'}
    with (output / 'SHA256SUMS.txt').open('x', encoding='utf-8', newline='\n') as f:
        f.write(''.join(row['sha256'] + '  ' + name + '\n' for name, row in sorted(evidence['packages'].items())))
    with (output / 'BUILD_EVIDENCE.json').open('x', encoding='utf-8') as f:
        json.dump(evidence, f, indent=2)
    print(json.dumps({'version': version, 'packages': evidence['packages']}, indent=2))

if __name__ == '__main__':
    main()
