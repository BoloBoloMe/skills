"""codex skill 元数据守卫测试.

用户调用 skill (frontmatter 带 disable-model-invocation: true) 必须有
agents/openai.yaml 且 policy.allow_implicit_invocation 为 false (布尔值,
不加引号); 模型调用 skill 不得把它设为 false, 不建文件即可. 只用标准库
按行解析这几行, 不引入 pyyaml.
"""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_TREES = ("workflow", "general")
EXPECTED_OPENAI_YAML = "policy:\n  allow_implicit_invocation: false\n"


def has_disable_model_invocation(skill_md: Path) -> bool:
    """按行读 frontmatter, 精确匹配 disable-model-invocation: true."""
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if line.strip() == "disable-model-invocation: true":
            return True
    return False


def allow_implicit_invocation_value(openai_yaml: Path) -> str | None:
    """按行读 openai.yaml, 返回 policy 下 allow_implicit_invocation 的原始值.

    缺 policy 段或缺该键返回 None. 不做完整 YAML 解析.
    """
    in_policy = False
    for line in openai_yaml.read_text(encoding="utf-8").splitlines():
        if line.strip() == "policy:":
            in_policy = True
            continue
        if in_policy:
            if line.startswith(" "):
                stripped = line.strip()
                if stripped.startswith("allow_implicit_invocation:"):
                    return stripped.split(":", 1)[1].strip()
            else:
                break
    return None


class SkillsCodexMetadataTests(unittest.TestCase):
    def test_all_skill_md_files_have_codex_metadata_contract(self):
        checked = 0
        for tree in SKILL_TREES:
            for skill_md in sorted((ROOT / tree).rglob("SKILL.md")):
                hidden = has_disable_model_invocation(skill_md)
                openai_yaml = skill_md.parent / "agents" / "openai.yaml"
                if hidden:
                    self.assertTrue(
                        openai_yaml.is_file(),
                        f"{skill_md}: 用户调用 skill 缺 agents/openai.yaml",
                    )
                    value = allow_implicit_invocation_value(openai_yaml)
                    self.assertEqual(
                        value,
                        "false",
                        f"{openai_yaml}: allow_implicit_invocation 应为不带引号的 false",
                    )
                    self.assertEqual(
                        openai_yaml.read_text(encoding="utf-8"),
                        EXPECTED_OPENAI_YAML,
                        f"{openai_yaml}: 内容应仅为最小 policy 配置",
                    )
                else:
                    if openai_yaml.is_file():
                        value = allow_implicit_invocation_value(openai_yaml)
                        self.assertNotEqual(
                            value,
                            "false",
                            f"{openai_yaml}: 模型调用 skill 不得把"
                            " allow_implicit_invocation 设为 false",
                        )
                checked += 1
        self.assertGreater(checked, 0)


if __name__ == "__main__":
    unittest.main()
