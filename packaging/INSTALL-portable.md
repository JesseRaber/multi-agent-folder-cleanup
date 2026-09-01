# Install - Multi-Agent Folder Cleanup

Portable Agent Skill package. Works with ChatGPT, Grok, Codex, Copilot, local
models, and Claude.ai's skill uploader.

The folder `multi-agent-folder-cleanup/` **is** the skill. Keep it intact -
`SKILL.md`, `scripts/`, and `references/` must stay together and keep their
relative paths, because `SKILL.md` points at the other two by relative path.

---

## ChatGPT

**Custom GPT / Projects**

1. Create or open a Custom GPT (or a Project).
2. Upload the three documents as knowledge files:
   - `multi-agent-folder-cleanup/SKILL.md`
   - `multi-agent-folder-cleanup/references/workflow.md`
   - `multi-agent-folder-cleanup/references/navigation-templates.md`
3. Paste this into the GPT's instructions:

   > When the user mentions a messy or sprawling project folder, an AI handoff
   > folder, duplicate or superseded docs, a stale index, or wants a folder
   > audited, restructured, or moved with verification, follow `SKILL.md`.
   > State the operating mode (Audit / Plan / Execute) in the first line.
   > Read `references/workflow.md` before any Audit, Plan, or Execute run.
   > Never move or delete anything without an explicitly approved move map.

4. Upload the `scripts/` files too if Code Interpreter is enabled. ChatGPT can
   run `audit_folder.py` and `verify_move.py` on an uploaded folder ZIP.

**Codex / agent hosts that read Agent Skills natively:** drop
`multi-agent-folder-cleanup/` into the host's skills directory. No wrapper.

---

## Grok

1. Upload the whole `multi-agent-folder-cleanup/` folder (or this ZIP) to the
   conversation or workspace.
2. Give Grok the same instruction block shown under ChatGPT above.
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
`multi-agent-folder-cleanup/SKILL.md`. Load `references/workflow.md` on demand
rather than up front - it is 301 lines and only needed once a mode is chosen.

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
