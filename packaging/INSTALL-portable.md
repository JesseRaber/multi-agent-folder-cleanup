# Install - Multi-Agent Folder Cleanup

Portable standalone Agent Skill package. Use the separate `-openai.zip` when
testing or distributing the native ChatGPT and Codex plugin form.

The folder `multi-agent-folder-cleanup/` **is** the skill. Keep it intact -
`SKILL.md`, `agents/`, `scripts/`, and `references/` must stay together and keep
their relative paths.

When a host has no native skill loader, paste this into its instructions:

> When the user mentions a messy or sprawling project folder, an AI handoff
> folder, duplicate or superseded docs, a stale index, or wants a folder
> audited, restructured, or moved with verification, follow `SKILL.md`.
> State the operating mode (Audit / Plan / Execute) in the first line.
> Report as: Loaded Multi-Agent Folder Cleanup v1.1.0.
> Read `references/workflow.md` before any Audit, Plan, or Execute run.
> Never move or delete anything without an explicitly approved move map.

---

## ChatGPT

ChatGPT desktop, Codex CLI, and the Codex IDE extension support standalone
skills. Install `multi-agent-folder-cleanup/` through the host's Skills
interface or configured skills directory. For distribution across supported
ChatGPT and Codex surfaces, use the native `-openai.zip` plugin package.

Custom GPT / Project without a skill ZIP: upload `SKILL.md`,
`references/workflow.md`, and `references/navigation-templates.md` as knowledge
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

## Claude.ai (skill upload)

Zip the `multi-agent-folder-cleanup/` folder on its own and upload it under
Settings -> Capabilities -> Skills. If you want the Claude Code **plugin** form
instead, use the `-claude` package from the same release.

---

## Local models (Ollama, LM Studio, llama.cpp front-ends)

Point the host's system prompt or context loader at
`multi-agent-folder-cleanup/SKILL.md`. Load references only when the skill
routes to them.

---

## Requirements

- **Scripts:** Python 3.8+. Standard library only - no `pip install`.
- **PowerShell script:** PowerShell 5.1 or PowerShell 7+. Required on Windows if
  you need the OneDrive placeholder check; the Python version cannot produce it.
- All three scripts are read-only against the target folder. `verify_move.py`
  never moves, copies, or deletes anything.

## Verify what you downloaded

```bash
sha256sum -c SHA256SUMS.txt
```

## Authority

If a downloaded copy of this skill ever disagrees with
<https://github.com/JesseRaber/multi-agent-folder-cleanup>, the repository is
current and the download is not.

MIT licensed - see `LICENSE`.
