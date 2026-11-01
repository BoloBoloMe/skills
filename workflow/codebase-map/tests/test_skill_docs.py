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

# 代码里的错误码全集不再手抄: 用 collect_code_error_codes() 静态解析
# scripts/*.py 的 error_result(...) 第 2 个位置参与 _AnalyzeError(...) 第 1
# 个位置参现场收集 (m26 评审 D-1/E-1: 手抄清单会随代码漂移而不变红).


def collect_code_error_codes() -> set:
    """静态解析 scripts/*.py 里错误码产生位置, 收集错误码全集.

    覆盖三种产生位: cmc.error_result(command, code, message, hint) 的第 2 个
    位置参, _AnalyzeError(code, message, hint) 的第 1 个位置参, 与 dict 字面量
    里 key 为 "code" 的字符串值 (REWORK-02 P-6: no_confirmed_address 这类不经
    error_result 产生的码在 codemap_common.py 组装 address_missing 时以 dict
    字面量出现, 不收的话将来把它写进文档表格会假红). 只收字符串字面量; dict
    分支里值为变量/调用的条目 (回放位) 不收, 动态传递处 (startup_error 回放,
    异常透传) 的错误码均已在别处以字面量出现, 不影响全集完整性 (主用例的
    关键码子集断言兼验证此点).
    """
    import ast

    codes: set = set()
    for script in sorted((SKILL_DIR / "scripts").glob("*.py")):
        tree = ast.parse(script.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                # key 为 "code" 的字符串字面量值: 不经 error_result 的产生位
                for key, value in zip(node.keys, node.values):
                    if (isinstance(key, ast.Constant) and key.value == "code"
                            and isinstance(value, ast.Constant)
                            and isinstance(value.value, str)):
                        codes.add(value.value)
                continue
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = (
                func.attr if isinstance(func, ast.Attribute)
                else (func.id if isinstance(func, ast.Name) else None)
            )
            if name == "error_result" and len(node.args) >= 2 \
                    and isinstance(node.args[1], ast.Constant):
                codes.add(node.args[1].value)
            elif name == "_AnalyzeError" and node.args \
                    and isinstance(node.args[0], ast.Constant):
                codes.add(node.args[0].value)
    return codes


def doc_error_codes(text: str) -> set:
    """从文档的失败出口清单表格提取错误码: 表格行首列里反引号包住的 token.

    只认表格第一列整格恰为一个 `snake_case` 反引号片段的行, 不捞正文里的
    普通参数名/字段名; 分隔行与非错误码列跳过. 守卫范围口径 (REWORK-02
    P-6): 只查失败出口清单表格首列, 不是全文 token 扫描, 正文里出现的
    错误码样式 token 不在本守卫观察范围.
    """
    codes = set()
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("|") and stripped.endswith("|")):
            continue
        cells = [cell.strip() for cell in stripped[1:-1].split("|")]
        if len(cells) < 2 or set(cells[0]) <= set("- :"):
            continue  # 分隔行
        match = re.fullmatch(r"`([a-z_]+)`", cells[0])
        if match:
            codes.add(match.group(1))
    return codes


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
    """TC-06-01 附加: 文档失败出口清单里列出的错误码全部在代码错误码全集内.

    全集从 scripts/*.py 现场静态解析 (collect_code_error_codes), 不是手抄
    副本; 文档侧从失败出口清单表格首列提取 (doc_error_codes). 范围口径
    (REWORK-02 P-6): 本守卫只查表格首列, 不扫全文 token; collector 同时收
    no_confirmed_address 这类非 error_result 产生的码 (dict "code" 字面量),
    将来把它写进表格不会假红.
    """
    codes_in_code = collect_code_error_codes()
    assert codes_in_code, "ast 解析应从 scripts/*.py 收集到错误码全集"
    codes_in_doc = doc_error_codes(skill_text())
    assert codes_in_doc, "SKILL.md 失败出口清单应能提取到错误码"
    unknown = codes_in_doc - codes_in_code
    assert not unknown, (
        "失败出口表格首列出现代码错误码全集外的码 "
        "(本守卫只查表格首列, 不扫全文 token, REWORK-02 P-6 口径): "
        f"{unknown}")
    # 关键错误码必须出现 (子集断言, 同时兼验证解析器没退化)
    assert {
        "container_not_supported", "podman_missing", "no_data_keys",
        "port_in_use", "instance_running", "state_mismatch",
    } <= codes_in_doc, "失败出口清单缺关键错误码"


def test_error_code_guard_would_fail_on_fabricated_code():
    """负向自测 (m26 评审 D-1): 证明错误码守卫真的会失败.

    对一段含编造错误码的假清单文本调用与主用例同一套检查函数, 断言
    unknown 非空 (守卫能抓到漂移), 且该编造码不在代码全集内.
    """
    fabricated = "| 错误码 | 下一步动作 |\n| --- | --- |\n| `no_such_error_code` | 编造的下一步. |\n"
    codes_in_doc = doc_error_codes(fabricated)
    assert codes_in_doc == {"no_such_error_code"}, "应从假文档提取到编造码"
    unknown = codes_in_doc - collect_code_error_codes()
    assert unknown, "守卫对编造错误码应报非空 (会失败), 而不是恒真"


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
