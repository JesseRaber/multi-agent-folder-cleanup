# Install in a Microsoft Copilot agent

Use the archive ending in `-microsoft-copilot-agent-only.zip` when uploading this skill to a Microsoft Copilot Studio or Microsoft 365 Copilot agent.

This package contains `SKILL.md`, references, the supported Python helpers (`audit_folder.py`, `verify_move.py`, `verify_records.py`) and installation metadata. It intentionally omits `audit_folder.ps1`: Microsoft's custom-skill upload validator does not support `.ps1` script files. Do not rename or disguise the PowerShell script to bypass that validation.

Upload the complete ZIP through the agent's Skills interface. After upload, confirm that the displayed skill name and description match `multi-agent-folder-cleanup`, then test a read-only audit request. A successful upload proves only package acceptance; it does not prove filesystem, connector, tenant-permission or script-runtime behavior.

The Python helpers require only the standard library, but Copilot's sandbox has no direct network access. Connector/API work must use capabilities enabled through the agent orchestrator rather than network calls from a packaged script.

Expected loaded version: **Multi-Agent Folder Cleanup v1.6.3**.
