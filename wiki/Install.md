# Install

Prebuilt packages are attached to each [release](https://github.com/JesseRaber/multi-agent-folder-cleanup/releases). Extract and keep the structure intact. Coding agents that install from GitHub (Antigravity, Claude Code, Codex CLI) can use the repository directly.

| Host | Package |
|---|---|
| Claude app skill upload, ChatGPT/Codex standalone skills, local models, any skills folder | `…-UNIVERSAL-skill.zip` |
| Claude Code `/plugin install` (not the Claude app uploader) | `…-claude-code-plugin.zip` |
| Codex / ChatGPT plugin marketplace | `…-codex-chatgpt-plugin.zip` |
| Microsoft Copilot agent skill upload, Grok | `…-microsoft-copilot-agent-only.zip` |
| Gemini Apps skill upload | `…-gemini-apps-only.zip` |
| Opal skill import | `…-opal-only.zip` |
| Optional Project Rules template on its own (no skill) | `…-project-rules-optional.zip` |

Older pre-v1.5.0 package names (`-skill`, `-portable`, `-claude`, `-openai`, `-gemini-apps`, `-project-rules`) are retired.

Host-specific omissions: microsoft-copilot-agent-only has no `.ps1` (Copilot rejects PowerShell skill scripts; Grok rejected UNIVERSAL for `.ps1` in the 2026-10-05 owner upload test). gemini-apps-only omits `audit_folder.py`, `audit_folder.ps1`, `agents/openai.yaml`, and project rules (upload scan rejects the credential-guard code). opal-only is Markdown only (`SKILL.md` name/description header plus `references/*.md`).
