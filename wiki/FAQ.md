# FAQ

Answers below match repository `main` and release **v1.8.1**. The [repository](https://github.com/JesseRaber/multi-agent-folder-cleanup) wins if this page and a downloaded copy disagree.

## What is Multi-Agent Folder Cleanup?

An MIT-licensed agent skill for a shared project folder used by more than one AI model. It covers ordinary saving and indexing (Work mode) and read-only audit, proposed reorganization, and approved execution for folder cleanup.

## Which file do I install?

Use the ZIP that matches the host. The usual download is `multi-agent-folder-cleanup-1.8.1-UNIVERSAL-skill.zip`. Claude Code, Codex/ChatGPT plugins, Microsoft Copilot (also used for Grok), Gemini Apps, and Opal each have a narrower package. See [Install](Install).

## Which package does Grok use?

The `microsoft-copilot-agent-only` ZIP, because Grok rejects the Universal ZIP because of `audit_folder.ps1`.

## Does it move or delete files by itself?

No. Audit is read-only. Plan only proposes a map. Execute follows an approved mutation list. Deletion is never included unless a separate approval names each target. Before any delete, run the recycle-path test and stop if it fails. The scripts do not move files.

## What changed in v1.8.1?

The bundled Project Rules template is 4.0.1 (eight wording fixes from the October audits: append preservation on hosts without a true append, SUPERSEDED staging marker, one session-index layout and three status values, clock-read timestamps, close-time pending hand-off, legacy slug declarations). Helper fixes: Work routing detected for Rules 4.0.0+, pre-edit copies not counted as pending, split-table and oversized-quick-context findings, link targets with parentheses, PowerShell `-Out` header parity, bold log labels, case-insensitive pending JSON keys. Install guides route Work-mode reads correctly; plugin manifests describe Work mode.

## What changed in v1.8.0?

Smaller per-mode read sets (new on-demand references: work-mode-baseline.md, audit-edge-cases.md, execute-principles.md, release-packages.md). Recycle-path test before any delete (no delete through a remote shell or bridge without a passing test). Helper fixes for report times and session-index. See [Changelog](Changelog).

## What changed in v1.7.2?

Work-mode trim. Install backups must stay outside every folder the host scans for skills; afterward exactly one SKILL.md with name multi-agent-folder-cleanup under the host skill roots. Files matching the ZIP are not proof of loading. See [Changelog](Changelog).

## What changed in v1.7.1?

Aligns with Project Rules 4.0.0. Work-mode refinements around session logs, tool slugs, pre-edit copies, provenance PENDING rows, and PowerShell 5.1 write mechanics. Helpers treat closed sessions correctly, use file times for activity, and `verify_records.py` now flags UTF-16/NUL damage. See [Changelog](Changelog).

## What changed in v1.7.0?

Add-only agent fallback with `_PROVENANCE.md`, opt-in sequential writers, leftover pending file handling, sync conflict copy checks, cloud connector guidance, and expanded audit helpers. Optional Project Rules 3.3.0. See [Changelog](Changelog).

## What changed in v1.6.2?

Release safety only; the skill behaves the same as v1.6.1. Grok now points to the Copilot package, releases are created as drafts and verified before publishing, published assets are never replaced, and Windows and Linux builds give identical archives. See [Changelog](Changelog).

## What changed in v1.6.1?

It adds read-only `scripts/verify_records.py` for hash, encoding, line-ending, link, and Markdown-table checks. Work mode asks agents to cite that output before calling a shared-record edit verified. See [Changelog](Changelog).

## What is Work mode?

The mode for ordinary work in a folder other agents also use: where to save, how to name, one roadmap, a session log, and a handoff. It is not a cleanup. See [Modes](Modes).

## Will it fix OneDrive or SharePoint placeholders?

Only the Windows PowerShell audit helper can inspect placeholder attributes. A Linux or macOS run must record hydration as unverified. Connector listings are not an Execute path for moves.

## Does installing the skill adopt the Project Rules?

No. `references/project-rules/` is an optional template. Adoption is a separate owner decision. Fill section 13 and paste section 0 into hosts that never read the folder.

## Where is workflow.md?

Removed in v1.5.2. [SKILL.md](https://github.com/JesseRaber/multi-agent-folder-cleanup/blob/main/skills/multi-agent-folder-cleanup/SKILL.md) is the router. There is no `adapters/` tree.

## How do I update an existing install?

Keep the old copy outside every folder the host scans for skills. Afterward there must be exactly one `SKILL.md` with `name: multi-agent-folder-cleanup` under the host skill roots. Restart and check the reported version; files matching the ZIP are not proof the host loaded them. See [Install](Install).
