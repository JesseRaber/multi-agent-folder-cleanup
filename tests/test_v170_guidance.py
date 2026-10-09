"""Stage 1 of v1.7.0: rules template 3.3.0 and Work-mode guidance (register R030, R155-R215)."""

from pathlib import Path
import re
import unittest


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/multi-agent-folder-cleanup"
REFS = SKILL / "references"


def read(rel):
    return (SKILL / rel).read_text(encoding="utf-8")


def section(text, start, end):
    i = text.index(start)
    j = text.index(end, i + len(start)) if end else len(text)
    return text[i:j]


class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.t = read("references/project-rules/AGENTS.proposed.md")

    def test_version_unchanged_at_330(self):
        self.assertIn("Version: 3.3.0", self.t)

    def test_section5_sequential_writer_default(self):
        s5 = section(self.t, "## 5.", "## 6.")
        self.assertIn("Sequential-writer declaration (default; delete this bullet to declare the project multi-operator)", s5)
        self.assertIn("read-back verification", s5)

    def test_section5_same_name_and_conflict_copies(self):
        s5 = section(self.t, "## 5.", "## 6.")
        self.assertIn("Never create a second file with the same name in the same folder.", s5)
        self.assertIn("`name (1).ext`", s5)
        self.assertIn("missing originals", s5)

    def test_section3_ai_context_continuity_only(self):
        s3 = section(self.t, "## 3.", "## 4.")
        self.assertIn("Keep `AI_CONTEXT/` for continuity records", s3)

    def test_section7_session_index_row_at_creation(self):
        s7 = section(self.t, "## 7.", "## 8.")
        self.assertIn("Create the row with the session log (status `in progress`)", s7)

    def test_template_size_recorded(self):
        # R214 warns above 16 KB; the template itself is larger (R039 tracks trimming).
        size = len(self.t.encode("utf-8"))
        self.assertLess(size, 32 * 1024, "template must stay below the 32 KiB Codex limit")

    def test_adoption_notes(self):
        a = read("references/project-rules/ADOPTION.md")
        self.assertIn("needs Project Rules 3.1.0 or later", a)
        self.assertIn("Delete that bullet when adopting to declare the project multi-operator", a)


class WorkModeTests(unittest.TestCase):
    def setUp(self):
        self.w = read("references/work-mode.md")

    def test_arrive_reads_tracker_by_section(self):
        self.assertIn("Read a large tracker by section or item ID and a journal by its tail", self.w)

    def test_arrive_conflict_copies_and_handoffs(self):
        w1 = section(self.w, "## W1.", "## W2.")
        self.assertIn("**Sync conflict copies.**", w1)
        self.assertIn("**Undelivered handoffs.**", w1)
        self.assertIn("#cloud-connectors-and-sync-folders", w1)

    def test_session_index_row_with_log(self):
        self.assertIn("Create your session-index row when you create the log", self.w)

    def test_scratch_exception_only_status_line(self):
        self.assertIn("rewrite only that file's `Status:` line", self.w)

    def test_save_table_rows(self):
        w3 = section(self.w, "## W3.", "## W4.")
        self.assertIn("Never `AI_CONTEXT/`, which holds continuity records only.", w3)
        self.assertIn("| Your review of another agent's work |", w3)
        self.assertIn("| A handoff addressed to another project |", w3)
        self.assertIn("ZIP plus `SHA256SUMS`", w3)

    def test_w5_declaration_and_pending(self):
        w5 = section(self.w, "## W5.", "## W6.")
        self.assertIn("**Sequential-writer declaration.**", w5)
        self.assertIn("a quiet `--orient` result, an absent lock or an old timestamp never does", w5)
        self.assertIn("`PENDING_<TARGET>.md`", w5)
        self.assertIn("**Apply leftover pending files.**", w5)
        self.assertIn("`Status: APPLIED <after-sha8> by <session>/<turn>`", w5)
        self.assertIn("Anything else is **Conflicted**", w5)

    def test_cloud_subsection(self):
        c = section(self.w, "### Cloud connectors and sync folders", "## W6.")
        for needle in ("**Say which view you used.**", "**Work by file id.**", "**Replace without twins.**",
                       "`Replaces: <old file id>`", "**One file type per shared record.**", "**Replicas.**",
                       "replica of unknown status"):
            self.assertIn(needle, c)

    def test_quick_context_lists_candidate_contents(self):
        self.assertIn("quick context lists the item IDs it already contains", self.w)

    def test_anchor_resolves(self):
        heads = {re.sub(r"[^a-z0-9 -]", "", h.lower()).replace(" ", "-")
                 for h in re.findall(r"^#+ (.+)$", self.w, re.M)}
        self.assertIn("cloud-connectors-and-sync-folders", heads)


class AuditGuidanceTests(unittest.TestCase):
    def test_audit_mode(self):
        a = read("references/audit-mode.md")
        for needle in ("warning above 16 KB, high above 32 KiB", "**Sync conflict copies.**",
                       "retired legacy journal, N KB", "**Unpacked packages and working copies.**",
                       "**Continuity folder misuse.**", "fixed timestamps", "`pending-*`, any case"):
            self.assertIn(needle, a)

    def test_connector_audit(self):
        c = read("references/connector-audit.md")
        self.assertIn("## Same-name files and replicas", c)
        self.assertIn("Label every listing with its view", c)

    def test_portfolio_rules_matrix(self):
        p = read("references/portfolio-audit-template.md")
        self.assertIn("## Rules matrix", p)
        self.assertIn("never report `differs` then", p)


if __name__ == "__main__":
    unittest.main()
