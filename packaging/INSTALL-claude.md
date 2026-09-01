# Install - Multi-Agent Folder Cleanup (Claude)

Two ways to install, depending on which Claude surface you use.

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

## B. Claude.ai / Claude app - skill upload

1. Zip **only** the inner folder `skills/multi-agent-folder-cleanup/`, so that
   `SKILL.md` sits at the root of the ZIP alongside `scripts/` and
   `references/`.
2. Settings -> Capabilities -> Skills -> Upload skill.

Or just use the `-portable` package from the same release, which is already in
that shape.

---

## Confirming it loaded

Ask Claude:

> My project folder is a mess and the agents keep citing the wrong spec.

A loaded skill answers with **Mode: Audit** on the first line and offers a
read-only inventory before proposing anything. If it starts suggesting a folder
tree immediately, the skill did not load.

The skill also reports itself as **Loaded Multi-Agent Folder Cleanup v1.0.0**.

---

## Requirements

- **Scripts:** Python 3.8+, standard library only. No dependencies to install.
- **PowerShell script:** PowerShell 5.1 or 7+. Needed on Windows for the
  OneDrive placeholder check, which the Python version cannot produce.
- All three scripts are read-only against the target folder. `verify_move.py`
  never moves, copies, or deletes.

## Verify what you downloaded

```bash
sha256sum -c SHA256SUMS.txt
```

## Authority

If this copy ever disagrees with
<https://github.com/JesseRaber/multi-agent-folder-cleanup>, the repository is
current and this download is not.

MIT licensed - see `LICENSE`.
