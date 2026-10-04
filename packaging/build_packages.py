"""Build and verify the seven install archives. Never tags, uploads or installs.

Usage: python packaging/build_packages.py NEW_OUTPUT_DIRECTORY [--status TEXT]

Used by .github/workflows/release.yml and for local candidate builds. The
output directory must not exist. Every archive is rebuilt from source,
re-read, byte-compared and smoke-tested before SHA256SUMS.txt is written.

Package names say who each archive is for (register R074-R076):
  UNIVERSAL-skill         skill folder for every skill uploader or skills folder
  claude-code-plugin      Claude Code /plugin layout (not the Claude app uploader)
  codex-chatgpt-plugin    OpenAI Codex / ChatGPT plugin layout
  microsoft-copilot-agent-only  Microsoft Copilot agent uploader (no PowerShell)
  gemini-apps-only        Gemini Apps uploader (its security scan rejects some files)
  opal-only               Opal importer (SKILL.md + references/*.md only)
  project-rules-optional  optional Project Rules template on its own
"""
import argparse
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
NAME = 'multi-agent-folder-cleanup'
ROOT = NAME + '/'
STAMP = (2026, 1, 1, 0, 0, 0)

# Gemini Apps: the uploader rejects .ps1/.yaml and the nested project rules,
# and its security scan rejects audit_folder.py (credential-hint read guards).
# Leave them out; never disguise code to pass a scan.
GEMINI_OMIT_FILES = {'scripts/audit_folder.py'}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_files():
    files = {}
    for p in sorted(SKILL.rglob('*')):
        if '__pycache__' in p.parts or p.suffix == '.pyc' or not p.is_file():
            continue
        if p.is_symlink():
            raise ValueError('Refusing linked package source')
        files[p.relative_to(SKILL).as_posix()] = p.read_bytes()
    return files


def opal_skill_md(data):
    """Opal accepts only name and description in the frontmatter, LF endings."""
    text = data.decode('utf-8').replace('\r\n', '\n')
    _, front, body = text.split('---\n', 2)
    keep = [line for line in front.splitlines() if line.startswith(('name:', 'description:'))]
    if len(keep) != 2:
        raise ValueError('SKILL.md frontmatter needs single-line name and description')
    return ('---\n' + '\n'.join(keep) + '\n---\n' + body).encode('utf-8')


def build_packages(files):
    repo = lambda rel: (REPO / rel).read_bytes()
    skill = {ROOT + n: d for n, d in files.items()}
    packages = {}

    universal = dict(skill)
    universal[ROOT + 'LICENSE.txt'] = repo('LICENSE')
    universal[ROOT + 'INSTALL.md'] = repo('packaging/INSTALL-universal.md')
    packages['UNIVERSAL-skill'] = (universal, True)

    # Microsoft Copilot custom-skill sandboxes support Python and common web/
    # POSIX script types, but reject PowerShell (.ps1) at upload validation.
    # Preserve the Python helpers and omit only the unsupported script type.
    copilot = {n: d for n, d in skill.items() if not n.endswith('.ps1')}
    copilot[ROOT + 'LICENSE.txt'] = repo('LICENSE')
    copilot[ROOT + 'INSTALL.md'] = repo('packaging/INSTALL-microsoft-copilot.md')
    packages['microsoft-copilot-agent-only'] = (copilot, True)

    for flavor, metadata, guide in [('claude-code-plugin', '.claude-plugin', 'INSTALL-claude-code.md'),
                                    ('codex-chatgpt-plugin', '.codex-plugin', 'INSTALL-codex-chatgpt.md')]:
        items = {ROOT + 'skills/' + n: d for n, d in skill.items()}
        for p in sorted((REPO / metadata).glob('*.json')):
            items[ROOT + metadata + '/' + p.name] = p.read_bytes()
        for name in ('LICENSE', 'README.md', 'CHANGELOG.md'):
            items[ROOT + name] = repo(name)
        items[ROOT + 'INSTALL.md'] = repo('packaging/' + guide)
        packages[flavor] = (items, True)

    gemini = {ROOT + n: d for n, d in files.items()
              if not n.startswith(('agents/', 'references/project-rules/'))
              and not n.endswith(('.ps1', '.yaml')) and n not in GEMINI_OMIT_FILES}
    gemini[ROOT + 'LICENSE.txt'] = repo('LICENSE')
    packages['gemini-apps-only'] = (gemini, True)

    # Opal: same layout as an Opal export - no folder entries, Markdown only.
    opal = {ROOT + 'SKILL.md': opal_skill_md(files['SKILL.md'])}
    for n, d in files.items():
        if n.startswith('references/') and n.count('/') == 1 and n.endswith('.md'):
            opal[ROOT + n] = d.replace(b'\r\n', b'\n')
    packages['opal-only'] = (opal, False)

    rules = {'project-rules/' + n.split('references/project-rules/', 1)[1]: d
             for n, d in files.items() if n.startswith('references/project-rules/')}
    packages['project-rules-optional'] = (rules, True)
    return packages


def write_zip(archive, items, folder_entries):
    names = sorted(items)
    dirs = set()
    if folder_entries:
        for n in names:
            parts = n.split('/')[:-1]
            for i in range(1, len(parts) + 1):
                dirs.add('/'.join(parts[:i]) + '/')
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as z:
        for d in sorted(dirs):
            info = zipfile.ZipInfo(d, date_time=STAMP)
            info.external_attr = 0o40755 << 16 | 0x10
            z.writestr(info, b'')
        for n in names:
            info = zipfile.ZipInfo(n, date_time=STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, items[n])
    return dirs


def verify(archive, flavor, items, dirs, version):
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        listed = z.namelist()
        assert len(listed) == len(set(listed)), 'duplicate members'
        assert set(listed) == set(items) | dirs, sorted(set(listed) ^ (set(items) | dirs))
        for name, data in items.items():
            assert z.read(name) == data, name
        if flavor == 'opal-only':
            assert not any(n.endswith('/') for n in listed)
            assert all(n.endswith('.md') for n in listed)
            assert all(b'\r' not in z.read(n) for n in listed)
            return
        if flavor == 'project-rules-optional':
            return
        with tempfile.TemporaryDirectory(prefix='cleanup-package-') as tmp:
            z.extractall(tmp)  # members were constructed above, not accepted from input
            scripts = Path(tmp) / NAME
            if flavor.endswith('-plugin'):
                scripts /= 'skills/' + NAME
            scripts /= 'scripts'
            for name in ('audit_folder.py', 'verify_move.py'):
                if not (scripts / name).exists():
                    assert flavor == 'gemini-apps-only', (flavor, name)
                    continue
                out = subprocess.run([sys.executable, str(scripts / name), '--version'],
                                     capture_output=True, text=True, check=True)
                assert out.stdout.strip().endswith(version), out.stdout
            if flavor in ('gemini-apps-only', 'microsoft-copilot-agent-only'):
                if flavor == 'microsoft-copilot-agent-only':
                    assert not any(n.lower().endswith('.ps1') for n in listed)
                return
            fixture = Path(tmp) / 'fixture'
            fixture.mkdir()
            (fixture / 'note.md').write_text('synthetic fixture', encoding='utf-8')
            subprocess.run([sys.executable, str(scripts / 'audit_folder.py'), '--root', str(fixture), '--brief'],
                           capture_output=True, check=True)
            ps = shutil.which('pwsh') or shutil.which('powershell.exe')
            if not ps:
                raise RuntimeError('PowerShell required for packaged smoke tests')
            subprocess.run([ps, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                            str(scripts / 'audit_folder.ps1'), '-Root', str(fixture), '-Brief'],
                           capture_output=True, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output')
    parser.add_argument('--status', default='local candidate, not published')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    version = re.search(r'^  version: "([^"]+)"', (SKILL / 'SKILL.md').read_text(encoding='utf-8'), re.M)[1]
    for name in ('.codex-plugin', '.claude-plugin'):
        assert json.loads((REPO / name / 'plugin.json').read_text())['version'] == version
    files = source_files()
    output.mkdir(parents=True, exist_ok=False)
    evidence = {'version': version, 'status': args.status,
                'source_files': {n: digest(b) for n, b in files.items()}, 'packages': {}}
    for flavor, (items, folder_entries) in build_packages(files).items():
        archive = output / f'{NAME}-{version}-{flavor}.zip'
        dirs = write_zip(archive, items, folder_entries)
        verify(archive, flavor, items, dirs, version)
        evidence['packages'][archive.name] = {'sha256': digest(archive.read_bytes()), 'files': len(items),
                                              'byte_verified': True}
    with (output / 'SHA256SUMS.txt').open('x', encoding='utf-8', newline='\n') as f:
        f.write(''.join(row['sha256'] + '  ' + name + '\n' for name, row in sorted(evidence['packages'].items())))
    with (output / 'BUILD_EVIDENCE.json').open('x', encoding='utf-8') as f:
        json.dump(evidence, f, indent=2)
    print(json.dumps({'version': version, 'packages': evidence['packages']}, indent=2))


if __name__ == '__main__':
    main()
