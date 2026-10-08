# multi-agent-folder-cleanup 1.6.2

Release-safety release. No change to the skill's modes or rules.

## Changes

- **Grok** now points to `-microsoft-copilot-agent-only.zip` in the README and install guide. Grok rejected the Universal ZIP because of `audit_folder.ps1` and accepted the Copilot package (owner upload test, 2026-10-05). The shipped Work-mode text already said this; the install table was stale.
- **Draft-first releases.** The release workflow creates a draft, refuses to run if a release for the tag already exists, requires this notes file, and no longer replaces assets (`--clobber` removed). The draft's assets are verified against a local candidate before publishing.
- **Version and asset checks.** `packaging/check_versions.py` (every version touch point, stale versions, workflow safety) and `packaging/verify_release.py` (assets vs `SHA256SUMS.txt`, GitHub digests and the local candidate), both from the github-release skill.
- **Same bytes on every OS.** The packager pins ZIP metadata and `.gitattributes` keeps text LF, so Windows and Linux builds give identical archives.
- `HOST_INSTALL_LOG.md` starts the per-host install record.
- Workflow comment corrected: the packager builds seven archives.

## Packages

Same seven archives and host rules as 1.6.1. Verify downloads with `sha256sum -c SHA256SUMS.txt`.

## Publication boundary

Installed host copies are updated separately; this release does not change any host by itself.
