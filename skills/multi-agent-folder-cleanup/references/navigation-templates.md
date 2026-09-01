# Navigation Templates

Read this only when creating or reviewing navigation files. Never create these during an Audit.

Shared rules:

- **Date everything.** An undated status file becomes a liability within a month.
- **State verification.** Each claim carries `verified` / `unverified` / `superseded`. Agents downstream cannot re-derive this.
- **No secrets.** No keys, tokens, connection strings, or credential paths — not even redacted placeholders that hint at location.
- **Relative paths only**, so the tree survives a move or a re-sync.
- **One authority per topic.** If two files could both answer a question, the navigation must say which one wins.

---

## README.md — entrypoint

```markdown
# <Project name>

<One sentence: what this folder is for.>

## Start here
1. `STATUS.md` — what is true right now
2. `AUTHORITY.md` — which documents govern what
3. `HANDOFF.md` — current master handoff, pick up here
4. `INDEX.md` — full map of the tree

## Ground rules for agents
- `authority/` governs. If your analysis conflicts with it, flag the conflict; do not overwrite.
- `backlog/` is proposed, not real. Never cite it as current state.
- `history/` is superseded. Read for context only.
- `mirrors/` is read-only and externally owned. Do not modify.
- New material arrives in `inbox/` and is untriaged until classified.

Last updated: YYYY-MM-DD
```

---

## STATUS.md — verified current state

```markdown
# Status — as of YYYY-MM-DD

## Verified true now
- <claim> — evidence: `path/to/artifact` (checked YYYY-MM-DD)

## In progress
- <item> — owner: <name> — next step: <one line>

## Known unverified
- <claim someone made that has not been confirmed> — source: `path`

## Recently superseded
- <claim> — replaced by <what> on YYYY-MM-DD — old copy: `history/...`
```

Nothing enters "Verified true now" on the strength of a document that says it. Only on the strength of the artifact it describes.

---

## AUTHORITY.md — who governs what

```markdown
# Authority Map

| Topic | Governing document | Scope | Last confirmed |
|---|---|---|---|
| <topic> | `authority/<file>` | <what it does and does not cover> | YYYY-MM-DD |

## Conflict resolution
1. Owner direction in `STATUS.md` overrides all documents.
2. `authority/` overrides `current/`.
3. `current/` overrides `backlog/` and `history/`.
4. Anything in `inbox/` carries no authority until classified.

## Known conflicts
- <doc A> vs <doc B> on <topic> — unresolved, needs owner decision
```

---

## INDEX.md — map of the tree

```markdown
# Index — generated YYYY-MM-DD

| Path | Bucket | What it is | State |
|---|---|---|---|
| `authority/spec.md` | authority | <one line> | verified |
| `backlog/roadmap.md` | backlog | <one line> | proposed |
```

The index must describe **final** paths. An index still showing proposed paths means the cleanup is not finished.

---

## HANDOFF.md — current master handoff

```markdown
# Handoff — YYYY-MM-DD

## Outcome of the last session
<2-4 bullets, verified facts only>

## State of play
- Done and verified: <list>
- Done but unverified: <list>
- Not started: <list>

## Next action
<the single most useful next step, and why>

## Constraints an agent must know
- <e.g. this tree is OneDrive-synced; hydrate before bulk operations>
- <e.g. `mirrors/vendor-sdk/` is a read-only checkout>

## Superseded handoffs
`history/handoffs/` — do not treat as current.
```

Exactly one master handoff at the root. Every prior handoff moves to `history/handoffs/` with a dated filename. Two live handoffs is the same failure as two live authorities.
