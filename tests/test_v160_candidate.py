"""v1.6.0 regressions for register rows R140-R146."""

from pathlib import Path
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / "skills/multi-agent-folder-cleanup"


def insert_table_row_once(path: Path, row: bytes) -> None:
    """Representative idempotent agent edit that preserves the file's bytes."""
    original = path.read_bytes()
    if row in original.splitlines(keepends=False):
        return
    newline = b"\r\n" if b"\r\n" in original else b"\n"
    lines = original.splitlines(keepends=True)
    table_rows = [i for i, line in enumerate(lines) if line.startswith(b"|")]
    if not table_rows:
        raise ValueError("table not found")
    insertion = table_rows[-1] + 1
    lines.insert(insertion, row + newline)
    path.write_bytes(b"".join(lines))


def archive_once(source: Path, archived: Path) -> str:
    """Representative idempotent archive move that never overwrites a target."""
    if archived.exists():
        if source.exists():
            raise FileExistsError("archived original exists; inspect current state")
        return "already-archived"
    if not source.exists():
        raise FileNotFoundError(source)
    source.rename(archived)
    return "archived"


class CandidateGuidanceTests(unittest.TestCase):
    def test_register_requirements_are_routed_to_requested_sections(self) -> None:
        work = (SKILL / "references/work-mode.md").read_text(encoding="utf-8")
        audit = (SKILL / "references/audit-mode.md").read_text(encoding="utf-8")
        records = (SKILL / "references/execute-records.md").read_text(encoding="utf-8")
        moves = (SKILL / "references/execute-moves.md").read_text(encoding="utf-8")
        principles = (SKILL / "references/cleanup-principles.md").read_text(encoding="utf-8")
        proposed = (SKILL / "references/project-rules/AGENTS.proposed.md").read_text(encoding="utf-8")

        self.assertIn("map every actionable item", work)
        self.assertIn("proof that it was completed or superseded", audit)
        self.assertIn("byte-for-byte pre-edit copy", work)
        self.assertIn("line endings", records)
        self.assertIn("safe to run twice", records)
        self.assertIn("must never overwrite an archived original", moves)
        self.assertIn("Write only in your own session log", work)
        self.assertIn("names every known unresolved item", work)
        self.assertIn("Private links, local or cloud paths", principles)
        self.assertIn("ask the owner before", principles)
        self.assertIn("ordinary business details", proposed)

    def test_crlf_markdown_table_insert_is_idempotent_and_byte_preserving(self) -> None:
        original = (
            b"# Tracker\r\n\r\n"
            b"| ID | Status |\r\n"
            b"|---|---|\r\n"
            b"| R140 | Proposed |\r\n"
            b"\r\nAfter table.\r\n"
        )
        row = b"| R141 | Proposed |"
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "tracker.md"
            target.write_bytes(original)
            insert_table_row_once(target, row)
            once = target.read_bytes()
            insert_table_row_once(target, row)
            twice = target.read_bytes()

        self.assertEqual(once, twice)
        self.assertEqual(once.count(row), 1)
        self.assertNotIn(b"\n\n", once)
        table = once[once.index(b"| ID"):].split(b"\r\n\r\n", 1)[0]
        self.assertNotIn(b"\r\n\r\n", table)
        self.assertEqual(once.replace(row + b"\r\n", b"", 1), original)
        self.assertNotIn(b"\n", once.replace(b"\r\n", b""))

    def test_archive_move_twice_keeps_original_archive_bytes(self) -> None:
        payload = b"canonical original\r\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "current.md"
            archived = root / "archive.md"
            source.write_bytes(payload)

            self.assertEqual(archive_once(source, archived), "archived")
            first = archived.read_bytes()
            self.assertEqual(archive_once(source, archived), "already-archived")

            self.assertFalse(source.exists())
            self.assertEqual(archived.read_bytes(), first)
            self.assertEqual(first, payload)


if __name__ == "__main__":
    unittest.main()
