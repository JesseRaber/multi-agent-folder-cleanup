# Install Multi-Agent Folder Cleanup

Source documentation: repository source is 2.1.0; as of 2026-10-29 the latest published release is 2.0.0. Source installs and published downloads may report different versions.

Install the current published release, **v2.0.0**, from [GitHub releases](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases/tag/v2.0.0). The repository is the authority if a downloaded copy disagrees with it.

This page names the package. Host steps stay in the install guides shipped inside each ZIP and in the [README](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/README.md).

## Which ZIP

| Your AI app | Download | Why this package |
|---|---|---|
| Claude app skill upload, ChatGPT or Codex standalone skills, local models, any skills folder | `multi-agent-folder-cleanup-2.0.0-UNIVERSAL-skill.zip` | Full skill folder, including Work mode and the Python and PowerShell helpers |
| Claude Code `/plugin install` | `multi-agent-folder-cleanup-2.0.0-claude-code-plugin.zip` | Plugin layout. The Claude app uploader rejects this ZIP |
| Codex / ChatGPT plugin marketplace | `multi-agent-folder-cleanup-2.0.0-codex-chatgpt-plugin.zip` | OpenAI plugin package. Directory publication is a separate OpenAI review and is not claimed here |
| Microsoft Copilot agent skill upload, **Grok** | `multi-agent-folder-cleanup-2.0.0-microsoft-copilot-agent-only.zip` | No `.ps1`. Copilot's skill upload rejects PowerShell scripts; Grok rejects the Universal ZIP because of `audit_folder.ps1` and accepts this one |
| Gemini Apps skill upload | `multi-agent-folder-cleanup-2.0.0-gemini-apps-only.zip` | Omits audit scripts, `agents/openai.yaml`, and project rules. Gemini's upload scan rejects the audit script; regular Gemini chat rejects packages with scripts |
| Opal skill import | `multi-agent-folder-cleanup-2.0.0-opal-only.zip` | Markdown only: `SKILL.md` plus `references/*.md` |
| Optional Project Rules template only | `multi-agent-folder-cleanup-2.0.0-project-rules-optional.zip` | Copyable template. Installing the skill does not adopt it |

Coding agents that install from GitHub (Antigravity, Claude Code, Codex CLI) can use [the repository](https://github.com/JesseRaber/multi-agent-folder-cleanup) directly.

Keep the extracted structure intact. Do not install from a mixed archive with nested packages or loose duplicate scripts. Releases before v1.5.0 used older asset names (`-skill`, `-portable`, `-claude`, `-openai`, `-gemini-apps`, `-project-rules`). There is no `adapters/` tree.

Host-specific packages leave out what that host rejects. The Copilot package has no `.ps1`. The Gemini Apps package omits the audit helpers (`audit_folder.py`, `audit_folder.ps1`), `agents/openai.yaml`, and project rules; it keeps `verify_move.py` and `verify_records.py`. Opal imports Markdown only. If a host package has no `references/project-rules/` folder, use the optional ZIP or the repository; do not reconstruct the template.

## Updating an existing install

Keep the backup of the previous version outside every folder the host scans for skills. For Codex, that includes not under `.codex/skills` (including `_backups` subfolders), because Codex loads every `SKILL.md` it finds recursively. If a backup must stay inside, rename its `SKILL.md` to a non-loading name such as `SKILL.backup-not-loaded.md`.

After install, list every `SKILL.md` under the host's skill roots and require exactly one whose `name:` is `multi-agent-folder-cleanup`.

Files matching the ZIP are not proof the host loaded them. Restart the host and check the reported version.

## Check the download

Compare the ZIP to `SHA256SUMS.txt` on the same release before extracting.

```bash
sha256sum -c SHA256SUMS.txt
```

```powershell
Get-FileHash .\multi-agent-folder-cleanup-*.zip -Algorithm SHA256
```

## Loaded check

A loaded skill reports **Loaded Multi-Agent Folder Cleanup v2.1.0 (SKILL.md at <path>; helpers <version>)**. A folder question starts with **Mode: Audit** and stays read-only until a specific mutation list is approved.

See [Modes](Modes), [Scripts](Scripts), and [FAQ](FAQ).
