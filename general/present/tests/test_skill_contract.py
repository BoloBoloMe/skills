"""present skill 文档契约测试."""

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent


def read_skill():
    return (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")


class TestSkillContract(unittest.TestCase):
    def test_user_invocation_frontmatter(self):
        skill = read_skill()
        self.assertIn("name: present", skill)
        self.assertIn("disable-model-invocation: true", skill)
        description = next(
            line for line in skill.splitlines() if line.startswith("description:")
        )
        self.assertIn("展示", description)
        self.assertIn("局域网地址", description)

    def test_mermaid_rendered_via_inlined_component(self):
        skill = read_skill()
        self.assertIn("scripts/embed_mermaid.py", skill)
        self.assertIn('<pre class="mermaid">', skill)
        self.assertIn("不输出裸 Mermaid 源码", skill)

    def test_diagram_rules_block_known_failure_modes(self):
        """2026-10-26 事故: 图放进折叠块 + 页面脚本二次渲染 -> 页面停在源码上."""
        skill = read_skill()
        # 图与隐藏容器互斥
        self.assertIn("图表不得放进默认隐藏的容器", skill)
        self.assertIn("`hidden` 属性", skill)
        # 只渲染一次, 禁止擦除后重画
        self.assertIn("图表只渲染一次", skill)
        self.assertIn("擦回源码再重画", skill)

    def test_self_check_is_mandatory_before_delivery(self):
        skill = read_skill()
        self.assertIn("scripts/check_page.py", skill)
        self.assertIn("<check> <html-file>", skill)
        self.assertIn("自检 `success` 为 true", skill)
        # 自检失败不交付, 也不把该目录挂到服务上
        self.assertIn("自检失败: 报告 `findings` 的具体位置", skill)
        self.assertIn("交付结果里不出现 URL 和文件路径", skill)

    def test_rework_discipline_is_documented(self):
        """先复现定位, 再改; 不先换实现盖掉现象."""
        skill = read_skill()
        self.assertIn("返工纪律", skill)
        self.assertIn("不先用别的实现把现象盖过去", skill)

    def test_single_delivery_flow_contract(self):
        """TC-002: 只有一条交付流程 (D001), 旧的本地浏览器分支与 REMOTE.md 已删除."""
        skill = read_skill()
        # 单一入口: 只读 SKILL.md, 不再有按环境分叉的第二份文档
        self.assertFalse((SKILL_DIR / "REMOTE.md").exists())
        self.assertFalse((SKILL_DIR / "scripts" / "browser_session.py").exists())
        self.assertNotIn("REMOTE.md", skill)
        self.assertNotIn("browser_session.py", skill)
        self.assertNotIn("ssh -L", skill)
        # 明确不按 SSH 变量选分支, 不在本机开浏览器
        self.assertIn("不用 SSH 环境变量选分支", skill)
        self.assertIn("不在本机开浏览器", skill)
        self.assertNotIn("选择模式", skill)
        self.assertIn("只有一条交付路径", skill)
        # 仍交付局域网 URL, 不交文件路径或 loopback
        self.assertIn("不给页面文件路径", skill)
        self.assertIn("不给 loopback 地址", skill)

    def test_no_state_object_requirement(self):
        """D002: 不再强制 __PRESENTATION_STATE__, 也未新增状态回传通道."""
        skill = read_skill()
        self.assertIn("页面不再要求提供 `window.__PRESENTATION_STATE__`", skill)
        self.assertIn("反馈与最终确认都在 chat 完成", skill)
        # 旧强制要求与回读流程的措辞都不再出现为要求
        self.assertNotIn("每页都提供", skill)
        self.assertNotIn("回读状态", skill)

    def test_address_resolution_contract_is_documented(self):
        """D011: 地址来源顺序, 缺口出口与容器映射都写进唯一流程."""
        skill = read_skill()
        self.assertIn("--lan-host", skill)
        self.assertIn("address_missing.code=no_confirmed_address", skill)
        self.assertIn("address_missing.code=container_env_missing", skill)
        self.assertIn("~/.agents/sandbox-worktree/lan-address", skill)
        self.assertIn("SWT_HOST_LAN_IP", skill)
        self.assertIn("SWT_HOST_WEB_PORT", skill)
        self.assertIn("我确认前不交付任何 URL", skill)
        # 信箱出口与用户出口的顺序
        self.assertIn("宿主会话索取", skill)
        self.assertIn("信箱不可用才请我提供", skill)

    def test_port_and_lifetime_rules_are_documented(self):
        """BR-001/BR-009/BR-017/BR-018: 端口纪律, 共享 stop, 风险说明与命名规则."""
        skill = read_skill()
        self.assertIn("49152-65534", skill)
        self.assertIn("最多 10 次", skill)
        self.assertIn("port_in_use", skill)
        self.assertIn("--fixed-port", skill)
        self.assertIn("8800", skill)
        self.assertIn("stop` 关闭该用户全部共用页面", skill)
        self.assertIn("不在收工清理里执行", skill)
        self.assertIn("同网段主体可读取全部已挂载目录", skill)
        self.assertIn("只挂愿意公开的展示目录", skill)
        self.assertIn("`YYYY-MM-DD-`", skill)
        self.assertIn("新版本不覆盖旧文件", skill)
        # 默认监听 0.0.0.0 且 --bind 仍是必填
        self.assertIn("`--bind` 必填", skill)
        self.assertIn("0.0.0.0", skill)
        # 端口真值与映射端口分开写在文档里
        self.assertIn("`port` 永远是实际监听端口", skill)


if __name__ == "__main__":
    unittest.main()
