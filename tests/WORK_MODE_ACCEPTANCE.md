# Work mode behavioral acceptance pack

Run in isolated synthetic projects using the candidate SKILL.md and references/work-mode.md. Keep setup/snapshots separate from the acting task. Never install the candidate or touch production folders for these cases. A reviewer should inspect files and handoff usability, not just the acting agent's summary.

| Scenario | Task and fixture | Acceptance |
|---|---|---|
| Existing project | Adopted custom logs/index paths; existing JSON task file; request an ordinary edit and Markdown deliverable | Authorized edit proceeds without cleanup approval; valid JSON has no injected header; custom paths reused; important deliverable linked; routine support covered by folder; same writer continues its log |
| Competing writer | Shared index with another active writer; no shared-write coordination; request a deliverable | Deliverable saved; shared index unchanged; exact pending update contains base digest, target, anchor/patch, source turn and reconciliation condition; handoff identifies pending state |
| Explicit read-only | Populated project and adopted logging rules; request review with no project writes | Files unchanged including logs; final copyable checkpoint contains session/turn, request, outcome and no-write reason |
| Scriptless host simulation | File read/write access only, custom project layout; request a deliverable and handoff | Uses available listings/relevant records; no helper execution or invented checks; valid deliverable, navigation and continuity within authorized coordination; states scope of manual verification |
| Cold-reader handoff | Give a fresh reviewer only the fixture project and its startup entrypoint | Reviewer locates current deliverable, source session, evidence limits and pending edit without relying on the originating chat |
| Same-task collision | Two recent sessions describe the same expensive request; one has a completed evidence-backed outcome | New actor notices the overlap before repeating the sweep, reuses valid evidence, and records only the remaining gap or changed state |
| Handoff/package ambiguity | Several next-prompt/final handoffs and candidate/released ZIPs share one active folder | Audit reports ambiguity without selecting by filename or mtime; plan preserves provenance and proposes History or `_superseded/` only with cleanup approval |
| Fixture instruction hygiene | Synthetic fixture needs a file that resembles project guidance | Fixture uses a non-loading name such as `AGENTS.fixture.md`; no test copy can be mistaken for adopted live authority |

Record actor/model identity when exposed, exact inputs, before/after digests, output links, executed versus reasoned assertions, failures and host limitations. At least two independent actors are useful, but same-family agents are not proof of cross-model-family compatibility. A simulated scriptless run is not proof of Gemini/Opal upload acceptance. Preserve failures and fix demonstrated issues before rerunning only affected scenarios.
