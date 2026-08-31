"""present skill 文档契约测试."""

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent


class TestSkillContract(unittest.TestCase):
    def test_model_invocation_frontmatter(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: present", skill)
        description = next(
            line for line in skill.splitlines() if line.startswith("description:")
        )
        self.assertIn("我要求可视化", description)
        self.assertIn("复杂到文字难以承载", description)

    def test_browser_helper_path_is_resolved_from_skill_directory(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("将 `scripts/browser_session.py` 相对本 skill 目录解析为绝对路径", skill)

    def test_remote_ssh_mode_contract(self):
        """TC-024: SKILL.md 远程 (ssh) 模式段文本契约 (D003/D004/D009/D001/D011/D006/D013-7)."""
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        # (a) 远程检测: SSH_TTY/SSH_CONNECTION 任一存在即远程, 用户明示可覆盖
        self.assertIn("SSH_TTY", skill)
        self.assertIn("SSH_CONNECTION", skill)
        self.assertIn("用户明示", skill)
        # (b) 远程不起 Chromium, 经 web_server.py 挂载/复用 web 服务交付 URL
        self.assertIn("不起 Chromium", skill)
        self.assertIn("`scripts/web_server.py`", skill)
        # (c) 端口 LLM 在 49152-65534 随机选, port_in_use 换端口重试 ≤10 次 (D009)
        self.assertIn("49152-65534", skill)
        self.assertIn("port_in_use", skill)
        self.assertIn("≤10 次", skill)
        # (d) bind: ssh 场景默认 0.0.0.0; 127.0.0.1 时 ssh -L 转发指引 (D001/D011)
        self.assertIn("0.0.0.0", skill)
        self.assertIn("ssh -L", skill)
        # (e) 成功后 chat 给出可点击 URL (D011/D013-7)
        self.assertIn("可点击 URL", skill)
        # (f) 失败出口: 本地路径+摘要 (D013-7)
        self.assertIn("重试与备选 bind 均失败后", skill)
        self.assertIn("本地绝对路径", skill)
        # (g) 远程降级纯展示: 无 __PRESENTATION_STATE__ 回读, 反馈与确认在 chat (D003)
        self.assertIn("纯展示", skill)
        self.assertIn("`__PRESENTATION_STATE__` 回读", skill)
        # (h) 复用语义: bind 一致幂等复用; 不一致报 bind_conflict 先 stop (D006)
        self.assertIn("幂等复用", skill)
        self.assertIn("bind_conflict", skill)


if __name__ == "__main__":
    unittest.main()
