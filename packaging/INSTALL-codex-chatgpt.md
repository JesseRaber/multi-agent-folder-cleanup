# Install - Multi-Agent Folder Cleanup (Codex / ChatGPT plugin)

For a standalone skill upload instead of a plugin, use `-UNIVERSAL-skill.zip`.

This archive is a native skills-only OpenAI plugin:

```text
multi-agent-folder-cleanup/
  .codex-plugin/plugin.json
  skills/multi-agent-folder-cleanup/
    SKILL.md
    agents/openai.yaml
    scripts/
    references/
```

## Test as a plugin

1. Extract the outer `multi-agent-folder-cleanup/` folder to a permanent local location.
2. Add that folder to a local plugin marketplace using Plugin Creator in ChatGPT Work mode or Codex.
3. Refresh ChatGPT or Codex, install the plugin from the local marketplace, and start a new conversation.
4. Test with: “Audit this portfolio of project folders and separate documentary claims from operationally verified state.”

A loaded skill should report **Loaded Multi-Agent Folder Cleanup v1.7.2** and begin with **Mode: Audit** and offer read-only inspection before proposing changes. Publishing to the universal ChatGPT and Codex plugin directory requires a separate OpenAI submission and review; this archive is prepared for that workflow but is not represented as already published.

## Install as a personal standalone skill

ChatGPT desktop, Codex CLI, and the Codex IDE extension can use standalone skills. Install the inner `skills/multi-agent-folder-cleanup/` folder through the host’s Skills interface or configured skills directory. Keep `SKILL.md`, `agents/`, `scripts/`, and `references/` together.

## Updating an existing install

- Keep the backup of the previous version **outside** every folder the host
  scans for skills (for Codex, not under `.codex/skills`, including
  `_backups` subfolders: Codex loads every `SKILL.md` it finds recursively, and
  an old backup loads as a second skill with the same name). If a backup must
  stay inside, rename its `SKILL.md` to a non-loading name such as
  `SKILL.backup-not-loaded.md`.
- After install, list every `SKILL.md` under the host's skill roots and require
  exactly one whose `name:` is `multi-agent-folder-cleanup`.
- Files matching the ZIP are not proof the host loads them. Restart or refresh
  the host, start a new session and confirm the reported version.

## Requirements and safety

- Python 3.8+ for the portable audit, move-verification, and record-verification helpers.
- PowerShell 5.1 or 7+ for the Windows/OneDrive audit helper.
- All helpers are read-only against the target folder; `verify_move.py` never moves, copies, or deletes anything. `verify_records.py` checks shared records and does not modify them.
- A folder reorganization still requires an explicitly approved literal move map.

Verify the release archives against `SHA256SUMS.txt` before extracting (`sha256sum -c SHA256SUMS.txt`, or `Get-FileHash` on Windows). If a downloaded copy disagrees with https://github.com/JesseRaber/multi-agent-folder-cleanup, the repository is current.

MIT licensed — see `LICENSE`.

## Optional project rules

The skill includes `references/project-rules/AGENTS.proposed.md` and `ADOPTION.md`. They are a versioned copyable template and adoption guide, not active project instructions. Installing this skill does not install those rules. For a named project, obtain separate owner adoption and merge existing policies/records as described in the guide.
