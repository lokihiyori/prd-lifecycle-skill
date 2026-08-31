from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "Sample_PRD_v0.1.0.md"
PROGRESS = ROOT / "scripts" / "prd_progress.py"
VALIDATE = ROOT / "scripts" / "prd_validate.py"


class SkillScriptTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, *map(str, args)], text=True, capture_output=True, check=False)

    def write_update(self, folder: Path, payload: dict) -> Path:
        path = folder / "updates.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def test_strict_validator_accepts_canonical_fixture(self) -> None:
        result = self.run_cmd(VALIDATE, FIXTURE, "--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_progress_update_uses_patch_and_preserves_action_id(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            output = folder / "Sample_PRD_v0.1.1.md"
            updates = self.write_update(folder, {
                "updates": [{
                    "id": "FR-CORE-001", "status": "Reported Complete",
                    "evidence": "PR #42 and CI", "status_basis": "Owner report with CI",
                }]
            })
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", output,
                "--actor", "Engineer", "--date", "2026-09-01", "--expected-version", "v0.1.0",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            content = output.read_text(encoding="utf-8")
            self.assertIn("| PRD Version | v0.1.1 |", content)
            self.assertIn("| A-001 | Q-001 |", content)
            self.assertIn("Reported Complete", content)
            self.assertEqual(self.run_cmd(VALIDATE, output, "--strict").returncode, 0)

    def test_noop_refuses_fake_version_bump(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            updates = self.write_update(folder, {"updates": [{"id": "FR-CORE-001", "status": "Not Started"}]})
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", folder / "out.md",
                "--actor", "Product", "--date", "2026-09-01",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("No effective changes", result.stderr)

    def test_verified_requires_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            updates = self.write_update(folder, {
                "updates": [{"id": "FR-CORE-001", "status": "Verified", "verification_confirmed": True}]
            })
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", folder / "out.md",
                "--actor", "QA", "--date", "2026-09-01",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("cannot become Verified", result.stderr)

    def test_priority_change_automatically_uses_minor(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            output = folder / "Sample_PRD_v0.2.0.md"
            updates = self.write_update(folder, {"updates": [{"id": "FR-CORE-001", "priority": "P1"}]})
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", output,
                "--actor", "Product", "--date", "2026-09-01",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("| PRD Version | v0.2.0 |", output.read_text(encoding="utf-8"))

    def test_expected_version_detects_stale_input(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            updates = self.write_update(folder, {"updates": [{"id": "FR-CORE-001", "status": "In Progress"}]})
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", folder / "out.md",
                "--actor", "Engineer", "--expected-version", "v9.9.9",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Input version changed", result.stderr)

    def test_dependency_resolution_unblocks_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            output = folder / "Sample_PRD_v0.1.1.md"
            updates = self.write_update(folder, {
                "dependency_updates": [{
                    "id": "Q-001", "status": "Resolved", "evidence": "Approved scope decision"
                }]
            })
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", output,
                "--actor", "Product", "--date", "2026-09-01",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            content = output.read_text(encoding="utf-8")
            self.assertIn("| A-002 | FR-CORE-001 |", content)
            self.assertIn("| Q-001 | Decision | Gate | Confirm launch scope | Resolved |", content)
            self.assertEqual(self.run_cmd(VALIDATE, output, "--strict").returncode, 0)

    def test_semantic_change_rejects_forced_patch(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            updates = self.write_update(folder, {"updates": [{"id": "FR-CORE-001", "priority": "P1"}]})
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", folder / "out.md",
                "--actor", "Product", "--bump", "patch",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("requires at least a minor", result.stderr)

    def test_explicit_version_cannot_regress(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            updates = self.write_update(folder, {"updates": [{"id": "FR-CORE-001", "status": "In Progress"}]})
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", folder / "out.md",
                "--actor", "Engineer", "--new-version", "v0.1.0",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("greater than the current version", result.stderr)

    def test_multiline_evidence_is_safe_in_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            output = folder / "Sample_PRD_v0.1.1.md"
            updates = self.write_update(folder, {
                "updates": [{"id": "FR-CORE-001", "status": "Reported Complete", "evidence": "PR #42\nCI passed"}]
            })
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", output,
                "--actor", "Engineer", "--date", "2026-09-01",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PR #42<br>CI passed", output.read_text(encoding="utf-8"))
            self.assertEqual(self.run_cmd(VALIDATE, output, "--strict").returncode, 0)

    def test_secret_in_update_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            folder = Path(raw)
            updates = self.write_update(folder, {
                "updates": [{"id": "FR-CORE-001", "notes": "api_key=abcdefghijklmnop"}]
            })
            result = self.run_cmd(
                PROGRESS, "--prd", FIXTURE, "--updates", updates, "--output", folder / "out.md",
                "--actor", "Engineer",
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("credential or secret", result.stderr)

    def test_validator_rejects_aggregate_decision_ids(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "Bad_PRD_v0.1.0.md"
            content = FIXTURE.read_text(encoding="utf-8").replace("Q-001 | Decision", "Q-001–Q-012 | Decision", 1)
            path.write_text(content, encoding="utf-8")
            result = self.run_cmd(VALIDATE, path, "--strict")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ranges", result.stdout)


if __name__ == "__main__":
    unittest.main()
