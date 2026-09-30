# v1.3.0 forward-evaluation results — 2026-09-30

An independent GPT-6-sol agent received the candidate skill and four fresh local
fixture requests, without prior findings, desired outcomes or corrective prompts.
It was authorized to save external evaluation reports and perform only the work
allowed by each request. The coordinating Codex agent inspected all four reports,
the saved continuity record and the original-file manifest independently.

| Case | Observed result |
|---|---|
| Unadopted README | Proposed rules were not treated as governing; audit stayed read-only |
| Adopted README | Routine project question answered; one session log saved with UUID, offset timestamp, writer, source-unavailable label and result |
| Recovery | Staging verification passed; target verification exited 1 with a hash mismatch; newer target and original staged bytes retained |
| Incomplete plan | Receipt-bound preflight exited 0; missing approved navigation/staging scope blocked movement; original source and index retained |

All 18 initial fixture files matched the preserved manifest afterward. The only
fixture addition was the required session log in the adopted-README case; four
reports were written outside the fixture projects. This is a single independent
local evaluation across four requests, using a model different from the earlier
Gemini test family. It is not a live host, OneDrive, multi-device or universal
cross-model certification. No guided rerun was needed for these cases.

Separately, automated regression tests exercise map rendering, receipt rejection,
relative-map relocation, source/target change detection and evidence preservation.
Their results are reported by CI, not inferred from this behavioral run.
