# Multi-Agent Folder Cleanup v1.9.0

Pending-edit checks now resolve absolute targets inside a project while refusing external paths. Older relative-path markup remains supported.

Unresolved pending edits appear before recorded Applied/Superseded history, preserving existing totals and list limits.

Orientation discovers project indexes from an explicit index flag, a section 13 Index declaration, or conventional locations. Multiple candidates are checked and reported without declaring one authoritative; missing declared indexes remain visible.

Includes regression tests for Windows paths, external junctions, index selection and read-only behavior, plus Windows/Ubuntu package checksum comparison. Project Rules remain 4.0.1. Existing host-specific package layouts are unchanged.
