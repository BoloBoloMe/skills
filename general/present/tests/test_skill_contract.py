"""present skill 文档契约测试."""

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent


class TestSkillContract(unittest.TestCase):
    def test_user_invocation_frontmatter(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: present", skill)
        self.assertIn("disable-model-invocation: true", skill)
        description = next(
            line for line in skill.splitlines() if line.startswith("description:")
        )
        self.assertIn("展示", description)

    def test_browser_helper_path_is_resolved_from_skill_directory(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("将 `scripts/browser_session.py` 相对本 skill 目录解析为绝对路径", skill)

    def test_mermaid_rendered_via_inlined_component(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/embed_mermaid.py", skill)
        self.assertIn('<pre class="mermaid">', skill)
        self.assertIn("不输出裸 Mermaid 源码", skill)

    def test_diagram_rules_block_known_failure_modes(self):
        """2026-10-26 事故: 图放进折叠块 + 页面脚本二次渲染 -> 页面停在源码上."""
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        # 图与隐藏容器互斥
        self.assertIn("图表不得放进默认隐藏的容器", skill)
        self.assertIn("`hidden` 属性", skill)
        # 只渲染一次, 禁止擦除后重画
        self.assertIn("图表只渲染一次", skill)
        self.assertIn("擦回源码再重画", skill)

    def test_self_check_is_mandatory_before_delivery(self):
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        remote = (SKILL_DIR / "REMOTE.md").read_text(encoding="utf-8")
        self.assertIn("scripts/check_page.py", skill)
        self.assertIn("<check> <html-file>", skill)
        self.assertIn("自检 `success` 为 true", skill)
        # 远程看不到渲染结果, 同样必须过自检
        self.assertIn("<check>", remote)

    def test_rework_discipline_is_documented(self):
        """先复现定位, 再改; 不先换实现盖掉现象."""
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("返工纪律", skill)
        self.assertIn("不先用别的实现把现象盖过去", skill)

    def test_remote_ssh_mode_contract(self):
        """TC-024: 远程规则按需披露, 关键行为仍受文档契约保护."""
        skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        remote = (SKILL_DIR / "REMOTE.md").read_text(encoding="utf-8")
        self.assertIn("`REMOTE.md`", skill)
        text = skill + remote
        # 远程检测: SSH_TTY/SSH_CONNECTION 任一存在即远程, 用户明示可覆盖
        self.assertIn("SSH_TTY", text)
        self.assertIn("SSH_CONNECTION", text)
        self.assertIn("我明确说明", text)
        self.assertIn("明确说明优先", text)
        # 远程不起 Chromium, 经 web_server.py 挂载/复用 web 服务交付 URL
        self.assertIn("不启动 Chromium", text)
        self.assertIn("scripts/web_server.py", text)
        # 端口范围与重试 (D009)
        self.assertIn("49152-65534", text)
        self.assertIn("port_in_use", text)
        self.assertIn("最多 10 次", text)
        # bind, 安全提示及本机访问的端口转发 (D001/D011)
        self.assertIn("0.0.0.0", text)
        self.assertIn("ssh -L", text)
        self.assertIn("可点击 URL", text)
        # 失败出口 (D013-7)
        self.assertIn("重试与备选 bind 均失败后", text)
        self.assertIn("本地绝对路径", text)
        # 纯展示模式及复用冲突 (D003/D006)
        self.assertIn("没有读取通道", text)
        self.assertIn("__PRESENTATION_STATE__", text)
        self.assertIn("幂等复用", text)
        self.assertIn("bind_conflict", text)


if __name__ == "__main__":
    unittest.main()
