# FAQ

**Which package does Grok use?**  
The microsoft-copilot-agent-only ZIP, because Grok rejects `.ps1` files (owner upload test, 2026-10-05). See [Install](Install).

**Does it move or delete files by itself?**  
No. See [Safety rules](Safety-rules) and [Modes](Modes).

**Does installing the skill adopt the Project Rules?**  
No. `references/project-rules/` is an optional template. Adoption is a separate owner decision.

**Will it fix OneDrive or SharePoint placeholders?**  
Only the Windows PowerShell audit helper can inspect placeholder attributes. Connector listings are not an Execute path for moves.
