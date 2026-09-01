# Multi-Agent Folder Cleanup v1.1.0

This release makes the skill ready for native ChatGPT and Codex packaging while preserving the original conservative Audit / Plan / Execute safety model.

## Downloads

| File | Intended host |
|---|---|
| `multi-agent-folder-cleanup-1.1.0-openai.zip` | ChatGPT and Codex skills-only plugin |
| `multi-agent-folder-cleanup-1.1.0-portable.zip` | Standalone Agent Skill hosts |
| `multi-agent-folder-cleanup-1.1.0-claude.zip` | Claude Code / Claude Desktop plugin |
| `SHA256SUMS.txt` | Checksums for every archive |

## Changes

- Added `.codex-plugin/plugin.json` and `agents/openai.yaml` for native OpenAI plugin and skill discovery.
- Reduced `SKILL.md` to a concise routing and safety contract; moved helper command details to `references/audit-tools.md` while retaining the full protocol in `references/workflow.md`.
- Fixed three Python/PowerShell parity gaps: versioned release-note claim detection, claim size reporting, and dotfile extension classification.
- Added a deterministic cross-language parity test and pull-request CI.
- Added a separate OpenAI release archive and install guide.
- Synchronized package versions at `1.1.0`.

## Validation scope

CI validates the skill frontmatter with OpenAI’s pinned validator, checks version and reference consistency, compiles Python, parses PowerShell, and runs both audit helpers against the same fixture. The release workflow also builds, extracts, and exercises all archives.

Not claimed: installation through the public universal plugin directory, which requires a separate OpenAI submission and review; live OneDrive hydration behavior, which requires a representative synced Windows folder; or live end-to-end loading in every supported host.
