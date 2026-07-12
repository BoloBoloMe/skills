"""adaptive-presentation skill 文档契约测试."""

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent


class TestSkillContract(unittest.TestCase):
    def test_model_invocation_frontmatter(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: adaptive-presentation", skill)
        description = next(
            line for line in skill.splitlines() if line.startswith("description:")
        )
        self.assertIn("当你要向我展示信息", description)
        self.assertIn("我要求可视化", description)
        self.assertIn("禁用/恢复自动可视化", description)

    def test_browser_helper_path_is_resolved_from_skill_directory(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("将 `scripts/browser_session.py` 相对本 skill 目录解析为绝对路径", skill)


if __name__ == "__main__":
    unittest.main()
