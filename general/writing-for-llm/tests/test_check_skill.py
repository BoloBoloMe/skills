"""writing-for-llm 的机械校验回归测试."""

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "check_skill.py"
spec = importlib.util.spec_from_file_location("check_skill", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class CheckSkillTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "sample-skill" / "SKILL.md"
        self.path.parent.mkdir()

    def check_text(self, text):
        self.path.write_text(text, encoding="utf-8")
        return checker.check(self.path)

    def test_valid_modes(self):
        for flag, description in [("", "自动调用"), ("disable-model-invocation: true\n", "'人工: 调用'")]:
            with self.subTest(flag=flag):
                self.assertEqual([], self.check_text(
                    f"---\nname: sample-skill\ndescription: {description}\n{flag}---\n正文"
                ))

    def test_name_rules(self):
        errors = self.check_text("---\nname: SampleSkill\ndescription: 有效\n---\n")
        self.assertTrue(any("kebab-case" in error for error in errors))
        self.assertTrue(any("目录名" in error for error in errors))

    def test_model_description_colon_and_quoted_scalar(self):
        for description in ('"触发: 条件"', "触发: 条件", "'触发: 条件'"):
            with self.subTest(description=description):
                errors = self.check_text(f"---\nname: sample-skill\ndescription: {description}\n---\n")
                self.assertTrue(any("冒号" in error for error in errors))

    def test_does_not_accept_unchecked_description(self):
        for desc in ("|", "", "\"坏的\\q\"", "null", "~", "false", "123", "0x10", ".nan", "2024-05-01"):
            with self.subTest(desc=desc):
                self.assertTrue(self.check_text(f"---\nname: sample-skill\ndescription: {desc}\n---\n"))
        self.assertEqual([], self.check_text('---\nname: sample-skill\ndescription: "null"\n---\n'))

    def test_model_invocation_field_must_be_omitted(self):
        for value in ("false", '"true"', "null"):
            with self.subTest(value=value):
                errors = self.check_text(
                    f"---\nname: sample-skill\ndescription: 触发条件\ndisable-model-invocation: {value}\n---\n"
                )
                self.assertTrue(any("disable-model-invocation" in error for error in errors))

    def test_missing_header_and_duplicate_name(self):
        self.assertTrue(self.check_text("name: sample-skill"))
        errors = self.check_text("---\nname: sample-skill\nname: sample-skill\ndescription: 好\n---\n")
        self.assertTrue(any("重复字段" in error for error in errors))

    def test_cli_exit_code_and_diagnostic(self):
        self.check_text("---\nname: sample-skill\ndescription: 触发: 条件\n---\n")
        run = subprocess.run([sys.executable, str(SCRIPT), str(self.path)], capture_output=True, text=True)
        self.assertEqual(1, run.returncode)
        self.assertIn("冒号", run.stderr)
        self.check_text("---\nname: sample-skill\ndescription: 触发条件\n---\n")
        run = subprocess.run(
            [sys.executable, str(SCRIPT), str(self.path)], cwd=self.tmp.name, capture_output=True, text=True
        )
        self.assertEqual(0, run.returncode)
        self.assertIn("OK", run.stdout)


if __name__ == "__main__":
    unittest.main()
