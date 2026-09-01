# Install - Multi-Agent Folder Cleanup (Claude)

Two ways to install, depending on which Claude surface you use.

---

## A. Claude Code / Claude Desktop - plugin

This package is already in plugin layout:

```
multi-agent-folder-cleanup/
  .claude-plugin/plugin.json
  skills/multi-agent-folder-cleanup/
    SKILL.md
    scripts/
    references/
```

**From GitHub**

The repository is also its own marketplace catalog, so both commands are needed:
the first registers the catalog, the second installs the plugin listed in it.

```
/plugin marketplace add JesseRaber/multi-agent-folder-cleanup
/plugin install multi-agent-folder-cleanup@jesseraber-plugins
```

The `@jesseraber-plugins` suffix is the marketplace name, not the repo name.
If the install summary says `Run /reload-plugins to activate.`, run that.

**From this ZIP instead**

1. Unzip so the `multi-agent-folder-cleanup/` folder sits somewhere permanent
   (not Downloads - the path is read at load time).
2. This ZIP contains the plugin, not the marketplace catalog, so point Claude
   Code at the folder directly:

   ```
   /plugin marketplace add <path-to-the-unzipped-folder>
   /plugin install multi-agent-folder-cleanup@jesseraber-plugins
   ```

   If that add is rejected because the folder has no `marketplace.json`, use the
   GitHub commands above instead - they are the supported path.

3. Restart the session and confirm with `/plugin`.

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
