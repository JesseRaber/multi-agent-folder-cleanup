# Install - Multi-Agent Folder Cleanup (ChatGPT and Codex)

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
4. Test with: “My shared project folder is messy and agents keep citing the wrong spec.”

A loaded skill should begin with **Mode: Audit** and offer read-only inspection before proposing changes. Publishing to the universal ChatGPT and Codex plugin directory requires a separate OpenAI submission and review; this archive is prepared for that workflow but is not represented as already published.

## Install as a personal standalone skill

ChatGPT desktop, Codex CLI, and the Codex IDE extension can use standalone skills. Install the inner `skills/multi-agent-folder-cleanup/` folder through the host’s Skills interface or configured skills directory. Keep `SKILL.md`, `agents/`, `scripts/`, and `references/` together.

## Requirements and safety

- Python 3.8+ for the portable audit and move-verification helpers.
- PowerShell 5.1 or 7+ for the Windows/OneDrive audit helper.
- All helpers are read-only against the target folder; `verify_move.py` never moves, copies, or deletes anything.
- A folder reorganization still requires an explicitly approved literal move map.

Verify the release archives against `SHA256SUMS.txt`. If a downloaded copy disagrees with https://github.com/JesseRaber/multi-agent-folder-cleanup, the repository is current.

MIT licensed — see `LICENSE`.
