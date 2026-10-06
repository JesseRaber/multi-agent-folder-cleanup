# Install - Multi-Agent Folder Cleanup

Universal skill package: the `multi-agent-folder-cleanup/` skill folder, with
this guide and the license inside it. Use it for every skill uploader or skills
folder unless the table below names a host-specific package.

| Your AI app | Download |
|---|---|
| **Almost everything**: Claude app skill upload, ChatGPT/Codex standalone skills, Grok, local models, any skills folder | `…-UNIVERSAL-skill.zip` |
| Claude Code `/plugin install` (not the Claude app uploader) | `…-claude-code-plugin.zip` |
| Codex / ChatGPT plugin marketplace | `…-codex-chatgpt-plugin.zip` |
| Microsoft Copilot agent skill upload | `…-microsoft-copilot-agent-only.zip` |
| Gemini Apps skill upload | `…-gemini-apps-only.zip` |
| Opal skill import | `…-opal-only.zip` |
| Optional Project Rules template only | `…-project-rules-optional.zip` |

Coding agents that install from GitHub (Antigravity, Claude Code, Codex CLI) can use the repository directly.

The folder `multi-agent-folder-cleanup/` **is** the skill. Keep it intact -
`SKILL.md`, `agents/`, `scripts/`, and `references/` must stay together and keep
their relative paths.

When a host has no native skill loader, paste this into its instructions:

> When the user mentions a messy or sprawling project folder, an AI handoff
> folder, duplicate or superseded docs, a stale index, or wants a folder
> audited, restructured, or moved with verification, follow `SKILL.md`.
> State the operating mode (Work / Audit / Plan / Execute) in the first line.
> Report as: Loaded Multi-Agent Folder Cleanup v1.6.0.
> Read `references/preconditions.md` before any run, then only the file for the
> mode: `work-mode.md`, `audit-mode.md`, `plan-mode.md`, `execute-moves.md` or
> `execute-records.md`. If `SKILL.md` is loaded, follow its mode routing.
> Never move or delete anything without an explicitly approved move map.

---

## ChatGPT

ChatGPT desktop, Codex CLI, and the Codex IDE extension support standalone
skills. Install `multi-agent-folder-cleanup/` through the host's Skills
interface or configured skills directory. For distribution across supported
ChatGPT and Codex surfaces, use the `-codex-chatgpt-plugin.zip` package.

Custom GPT / Project without a skill ZIP: upload `SKILL.md`,
`references/preconditions.md`, `references/work-mode.md`, `references/audit-mode.md`,
`references/plan-mode.md` and `references/navigation-templates.md` as knowledge
files and paste the instruction block above.

---

## Grok

1. Upload the whole `multi-agent-folder-cleanup/` folder (or this ZIP) to the
   conversation or workspace.
2. Paste the instruction block at the top of this file.
3. In a Grok sandbox with Python, run the scripts directly:

   ```bash
   python multi-agent-folder-cleanup/scripts/audit_folder.py \
     --root <folder> --index-path INDEX.md --hash-files
   ```

Grok sandboxes are POSIX. Hydration of OneDrive/SharePoint files **cannot** be
checked there - record it as unverified and re-check on Windows before any
Execute run. The skill says this too; it is the most common way a run goes wrong.

---

## Claude app (skill upload)

Upload this ZIP as it is: Settings -> Capabilities -> Skills -> Upload skill.
It holds the one `multi-agent-folder-cleanup/` folder, which is the shape the
uploader expects. For the Claude Code **plugin** form, use
`-claude-code-plugin.zip` instead; the Claude app uploader rejects plugin files.

---

## Local models (Ollama, LM Studio, llama.cpp front-ends)

Point the host's system prompt or context loader at
`multi-agent-folder-cleanup/SKILL.md`. Load references only when the skill
routes to them.

---

## Smoke test

> Audit this portfolio of project folders. Label counts by scope, reject search results from the wrong project, and separate documentary claims from operationally verified state.

A loaded skill states **Mode: Audit** first and reports
**Loaded Multi-Agent Folder Cleanup v1.6.0**.

---

## Requirements

- **Scripts:** Python 3.8+. Standard library only - no `pip install`.
- **PowerShell script:** PowerShell 5.1 or PowerShell 7+. Required on Windows if
  you need the audit helper's OneDrive placeholder check; `audit_folder.py` cannot
  produce it. `verify_move.py preflight` checks hydration only under Windows-native Python.
- All four scripts are read-only against the target folder. `verify_move.py`
  never moves, copies, or deletes anything.

## Verify what you downloaded

Run this in the folder that holds the downloaded ZIPs and `SHA256SUMS.txt`,
before extracting anything:

```bash
sha256sum -c SHA256SUMS.txt          # macOS: shasum -a 256 -c SHA256SUMS.txt
```

```powershell
Get-FileHash .\multi-agent-folder-cleanup-*.zip -Algorithm SHA256
# compare each Hash with the matching line in SHA256SUMS.txt
```

## Authority

If a downloaded copy of this skill ever disagrees with
<https://github.com/JesseRaber/multi-agent-folder-cleanup>, the repository is
current and the download is not.

MIT licensed - see `LICENSE.txt`.

## Optional project rules

The skill includes `references/project-rules/AGENTS.proposed.md` and `ADOPTION.md`. They are a versioned copyable template and adoption guide, not active project instructions. Installing this skill does not install those rules. For a named project, obtain separate owner adoption and merge existing policies/records as described in the guide.
