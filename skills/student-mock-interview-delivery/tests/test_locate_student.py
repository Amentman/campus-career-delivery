import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
LOCATOR_PATH = SKILL_DIR / "scripts" / "locate_student.py"
SPEC = importlib.util.spec_from_file_location("locate_student", LOCATOR_PATH)
LOCATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LOCATOR)


class DeliveryRootResolutionTests(unittest.TestCase):
    def test_explicit_root_wins_even_when_auto_candidates_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            explicit = base / "explicit"
            explicit.mkdir()
            auto = base / "校招交付"
            auto.mkdir()

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                explicit_root=explicit,
                candidates=[auto],
            )

            self.assertEqual("ok", result["status"])
            self.assertEqual(explicit.resolve(), result["root"])
            self.assertEqual("explicit", result["resolved_by"])

    def test_auto_selects_the_only_existing_delivery_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            missing = base / "旧目录" / "校招交付"
            existing = base / "新目录" / "校招交付"
            existing.mkdir(parents=True)

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                candidates=[missing, existing],
            )

            self.assertEqual("ok", result["status"])
            self.assertEqual(existing.resolve(), result["root"])
            self.assertEqual("single_existing", result["resolved_by"])

    def test_auto_prefers_unique_root_containing_student_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            first = base / "第一处" / "校招交付"
            second = base / "第二处" / "校招交付"
            first.mkdir(parents=True)
            student_dir = second / "测试同学"
            student_dir.mkdir(parents=True)
            (student_dir / "测试同学简历.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                candidates=[first, second],
            )

            self.assertEqual("ok", result["status"])
            self.assertEqual(second.resolve(), result["root"])
            self.assertEqual("student_evidence", result["resolved_by"])

    def test_auto_stops_when_multiple_roots_contain_student_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            first = base / "第一处" / "校招交付"
            second = base / "第二处" / "校招交付"
            (first / "测试同学").mkdir(parents=True)
            (second / "测试同学").mkdir(parents=True)

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                candidates=[first, second],
            )

            self.assertEqual("ambiguous_root", result["status"])
            self.assertIsNone(result["root"])
            self.assertEqual(
                [first.resolve(), second.resolve()],
                result["candidates"],
            )

    def test_auto_reports_missing_when_no_delivery_root_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)

            result = LOCATOR.resolve_delivery_root(
                name="测试同学",
                candidates=[base / "不存在" / "校招交付"],
            )

            self.assertEqual("missing_root", result["status"])
            self.assertIsNone(result["root"])


class TeamConfiguredLocatorTests(unittest.TestCase):
    def run_locator(self, *arguments, config_path=None):
        env = os.environ.copy()
        if config_path is not None:
            env["JIHUI_SKILLS_CONFIG"] = str(config_path)
        result = subprocess.run(
            [sys.executable, str(LOCATOR_PATH), "--name", "测试同学", *arguments],
            text=True, capture_output=True, env=env,
        )
        return result.returncode, json.loads(result.stdout)

    def make_student(self, root):
        student = root / "测试同学"
        student.mkdir(parents=True)
        (student / "测试同学简历.pdf").write_bytes(b"locator fixture only")

    def test_repeated_roots_keep_earlier_unique_student_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "first", Path(tmp) / "second"
            self.make_student(first)
            second.mkdir()
            code, result = self.run_locator("--root", str(first), "--root", str(second))
            self.assertEqual(0, code, result)
            self.assertEqual(str(first.resolve()), result["delivery_root"])
            self.assertEqual(2, len(result["root_candidates"]))

    def test_configured_student_root_is_used_without_desktop_discovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "members-students"
            self.make_student(root)
            config = base / "team.json"
            config.write_text(json.dumps({"version": 1, "workspace": {"student_root": str(root)}}))
            code, result = self.run_locator(config_path=config)
            self.assertEqual(0, code, result)
            self.assertEqual(str(root.resolve()), result["delivery_root"])
            self.assertEqual("team_config", result["root_resolved_by"])

    def test_invalid_selected_config_is_reported_without_falling_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "team.json"
            config.write_text("not json")
            code, result = self.run_locator(config_path=config)
            self.assertEqual(7, code, result)
            self.assertEqual("config_error", result["status"])
            self.assertIsNone(result["delivery_root"])

    def test_explicit_root_overrides_unreadable_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "explicit"
            self.make_student(root)
            code, result = self.run_locator("--root", str(root), config_path=Path(tmp) / "missing.json")
            self.assertEqual(0, code, result)


if __name__ == "__main__":
    unittest.main()
