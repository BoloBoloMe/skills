"""ISSUE-06 SKILL.md 与元数据文本契约: TC-009, TC-06-01, TC-06-02.

只做文本判定, 不触 podman 与网络; SKILL.md 与 README.md 路径按本测试树
相对仓库根解析. 断言粒度按 ISSUE-06 任务书的用例描述, 关键短语与代码中
的错误码/参数名逐一核对过 (核对清单见 ISSUE-06 交付证据).
"""
from __future__ import annotations

import re
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL_MD = SKILL_DIR / "SKILL.md"
OPENAI_YAML = SKILL_DIR / "agents" / "openai.yaml"
README_MD = SKILL_DIR.parents[1] / "README.md"

CALL_FORM = "python3 <skill 目录>/scripts/codebase-map.py"

# TC-06-01 断言的 serve 输出三类说明与版本口径关键短语
DELIVERY_NOTES_PHRASES = (
    "层号/环/向上依赖在官方依赖视图里看",
    "依赖抽取完整性未量化",
    "分母口径",
)

# 代码里的错误码全集 (codebase-map.py / codemap_analyze.py / codemap_service.py
# 的 error_result 与 _AnalyzeError 调用逐个核对所得); SKILL.md 里出现的
# 错误码样 token 必须都在其中
KNOWN_ERROR_CODES = {
    "container_not_supported",
    "target_missing",
    "podman_missing",
    "image_unavailable",
    "image_digest_mismatch",
    "frontend_unavailable",
    "frontend_hash_mismatch",
    "gate_failed",
    "no_data_keys",
    "port_in_use",
    "instance_running",
    "state_mismatch",
    "stop_failed",
    "internal_error",
    "no_confirmed_address",
}


def skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def frontmatter_fields(text: str) -> dict[str, str]:
    lines = text.splitlines()
    assert lines[0] == "---", "SKILL.md 缺 frontmatter 开头"
    end = lines.index("---", 1)
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([a-z-]+):\s*(.*)$", line)
        if match:
            fields[match.group(1)] = match.group(2).strip()
    return fields


def readme_codebase_map_line() -> str:
    for line in README_MD.read_text(encoding="utf-8").splitlines():
        if "workflow/codebase-map/SKILL.md" in line and line.lstrip().startswith("|"):
            return line
    raise AssertionError("README.md 技能表没有指向 workflow/codebase-map/SKILL.md 的行")


def test_tc009_three_subcommand_roles_and_call_form():
    """TC-009: 三子命令职责, 调用式, 不合并与 stop 语义 (AC-009 主用例)."""
    text = skill_text()
    assert CALL_FORM in text, "缺调用式 python3 <skill 目录>/scripts/codebase-map.py"
    assert "uv run python" in text and "等价" in text, "缺 uv run 等价说明"
    assert "三者不合并" in text
    # 职责句: build 只分析并产出; serve 起或复用并交付局域网 URL; stop 停整个服务
    assert "只分析并产出数据" in text and "不起服务" in text
    assert re.search(r"起或复用常驻服务并交付局域网 URL", text)
    assert "停整个服务" in text
    assert "没有\"只停某一个库\"的语义" in text
    # 内部入口不列成对外子命令
    assert "_serve-daemon" not in text
    # 三子命令三个标题段落都在
    for command in ("build", "serve", "stop"):
        assert re.search(rf"`{command}[ `(|]", text), f"缺子命令 {command} 的用法"


def test_tc009_flags_and_defaults_documented():
    """TC-009 附加: 参数面与默认值说明."""
    text = skill_text()
    assert "--exclude <glob>" in text and "--json" in text
    assert "--port <N>" in text and "--address <IP>" in text
    assert "只在没有存活实例时生效" in text
    assert "先 `stop` 再换端口" in text
    assert "只作用于本次调用" in text and "不落盘" in text


def test_tc0601_delivery_discipline():
    """TC-06-01: 交付纪律与三类说明原样转述."""
    text = skill_text()
    assert "每个数据键的完整 URL" in text
    assert "?file=<键>" in text, "缺完整 URL 形态"
    assert "不给 loopback 地址" in text
    for phrase in DELIVERY_NOTES_PHRASES:
        assert phrase in text, f"缺三类说明之一: {phrase}"
    assert "原样转述" in text and "不改写" in text
    assert "不说分层完全可信" in text


def test_tc0601_cleanup_entry_and_no_auto_delete():
    """TC-06-01: 清理入口与不自动删除."""
    text = skill_text()
    assert "serve-root" in text and ".cc.json" in text
    assert "手动删" in text, "缺清理入口"
    assert "不会自动删除任何库的副本" in text
    assert "只留最近一个" in text, "缺没有只留最近一个清理的说明"


def test_tc0601_recovery_steps():
    """TC-06-01: 删运行时目录的复原步骤."""
    text = skill_text()
    assert "~/.agents/codebase-map/" in text
    assert "放弃当前实例" in text
    assert "重新执行 `serve`" in text and "原地复用" in text
    assert "重新执行 `build`" in text


def test_tc0601_version_statements():
    """TC-06-01: 版本口径 (镜像 tag/digest 核对, 前端 vis-2.9.1 英文原版)."""
    text = skill_text()
    assert "codecharta/codecharta-analysis:2.3.0" in text
    assert "单架构清单 digest" in text and "只记录" in text
    assert "vis-2.9.1" in text and "英文原版" in text
    assert "tools/stage.py frontend" in text, "缺汉化界面重新铺设入口"


def test_tc0601_every_error_code_token_exists_in_code():
    """TC-06-01 附加: 文档错误码样 token 全部在代码错误码全集内."""
    text = skill_text()
    tokens = set(re.findall(r"[a-z]+(?:_[a-z]+)+", text))
    unknown = tokens & {
        "container_not_supported", "target_missing", "podman_missing",
        "image_unavailable", "image_digest_mismatch", "frontend_unavailable",
        "frontend_hash_mismatch", "gate_failed", "no_data_keys",
        "port_in_use", "instance_running", "state_mismatch",
        "stop_failed", "internal_error",
    } - KNOWN_ERROR_CODES
    assert not unknown, f"出现未知错误码样 token: {unknown}"
    codes_in_doc = tokens & KNOWN_ERROR_CODES
    assert {
        "container_not_supported", "podman_missing", "no_data_keys",
        "port_in_use", "instance_running", "state_mismatch",
    } <= codes_in_doc, "失败出口清单缺关键错误码"


def test_tc0602_frontmatter_contract():
    """TC-06-02: frontmatter name 等于目录名, disable-model-invocation 为 true."""
    text = skill_text()
    fields = frontmatter_fields(text)
    assert fields.get("name") == SKILL_DIR.name, "name 必须等于目录名"
    assert fields.get("disable-model-invocation") == "true"
    assert fields.get("description"), "description 必须非空单行"


def test_tc0602_openai_yaml_verbatim():
    """TC-06-02: agents/openai.yaml 逐字等于两行最小配置."""
    assert OPENAI_YAML.read_text(encoding="utf-8") == (
        "policy:\n  allow_implicit_invocation: false\n"
    )


def test_tc0602_readme_row_reflects_v1():
    """TC-06-02: README 技能表行指向本 skill 且反映 v1 描述."""
    line = readme_codebase_map_line()
    assert "[`codebase-map`]" in line
    assert "代码库结构与依赖可视化" in line
    assert "常驻服务" in line and "手动" in line
