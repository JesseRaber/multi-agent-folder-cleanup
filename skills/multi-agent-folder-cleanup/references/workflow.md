# Workflow router

The full protocol is split by mode so an agent reads only what its run needs.

| Run | Read |
|---|---|
| Every run | [preconditions.md](preconditions.md) (A1–A6) |
| Audit | [audit-mode.md](audit-mode.md) (B1–B4, audit report) |
| Plan | [plan-mode.md](plan-mode.md) (C1–C3, plan report) |
| Execute: file moves | [execute-moves.md](execute-moves.md) (D0–D7, move verification, failure recovery) |
| Execute: record-only, connector edits, additive intake | [execute-records.md](execute-records.md) (D8–D10, record and additive verification) |

Section labels (A2, B4, C2, D9 and so on) are unchanged from earlier versions, so existing references still identify the same rule.
