# Install - Multi-Agent Folder Cleanup (Claude Code plugin)

This ZIP is the **Claude Code plugin**. For the Claude app skill uploader, use
`-UNIVERSAL-skill.zip` instead (section B).

---

## A. Claude Code / Claude Desktop - plugin

This package is in plugin layout and carries its own marketplace catalog:

```
multi-agent-folder-cleanup/
  .claude-plugin/
    plugin.json          plugin manifest
    marketplace.json     catalog listing this folder as its own plugin
  skills/multi-agent-folder-cleanup/
    SKILL.md
    agents/
    scripts/
    references/
```

Either route needs **two** commands: the first registers the catalog, the second
installs the plugin listed in it. `jesseraber-plugins` is the marketplace name
from `marketplace.json`, not the repo or folder name.

**From this ZIP**

1. Unzip so the `multi-agent-folder-cleanup/` folder sits somewhere permanent
   (not Downloads - the path is read at load time).
2. In Claude Code:

   ```
   /plugin marketplace add <path-to-the-unzipped-folder>
   /plugin install multi-agent-folder-cleanup@jesseraber-plugins
   ```

**From GitHub instead**

```
/plugin marketplace add JesseRaber/multi-agent-folder-cleanup
/plugin install multi-agent-folder-cleanup@jesseraber-plugins
```

If the install summary says `Run /reload-plugins to activate.`, run that.
Confirm with `/plugin`.

Not yet verified end to end: these commands match the documented schema and the
package layout satisfies it, but they have not been run against a live Claude
Code install. Report anything that fails.

---

## B. Claude app - skill upload

Do not upload this ZIP to the Claude app: the uploader rejects plugin manifests
and a nested `SKILL.md`. Download `multi-agent-folder-cleanup-<version>-UNIVERSAL-skill.zip`
from the same release and upload it under Settings -> Capabilities -> Skills.

---

## Confirming it loaded

Ask Claude:

> My project folder is a mess and the agents keep citing the wrong spec.

A loaded skill answers with **Mode: Audit** on the first line and offers a
read-only inventory before proposing anything. If it starts suggesting a folder
tree immediately, the skill did not load.

The skill also reports itself as **Loaded Multi-Agent Folder Cleanup v1.6.2**.

Portfolio smoke test:

> Audit this portfolio of project folders. Label counts by scope, reject search results from the wrong project, and separate documentary claims from operationally verified state.

---

## Requirements

- **Scripts:** Python 3.8+, standard library only. No dependencies to install.
- **PowerShell script:** PowerShell 5.1 or 7+. Needed on Windows for the
  audit helper's OneDrive placeholder check, which `audit_folder.py` cannot produce.
  `verify_move.py preflight` checks hydration only under Windows-native Python.
- All four scripts are read-only against the target folder. `verify_move.py`
  never moves, copies, or deletes. `verify_records.py` checks shared records
  and does not modify them.

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

If this copy ever disagrees with
<https://github.com/JesseRaber/multi-agent-folder-cleanup>, the repository is
current and this download is not.

MIT licensed - see `LICENSE`.

## Optional project rules

The skill includes `references/project-rules/AGENTS.proposed.md` and `ADOPTION.md`. They are a versioned copyable template and adoption guide, not active project instructions. Installing this skill does not install those rules. For a named project, obtain separate owner adoption and merge existing policies/records as described in the guide.
