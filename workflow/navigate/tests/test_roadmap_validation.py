"""roadmap.py 守门校验测试 (ISSUE-02: TC-002, TC-003, TC-004, TC-104, TC-105).

m04 新增枚举用例: TC-002 demo 可写入, TC-003 prototype 被拒且文件逐字节不变,
TC-005 poc 可写入; 各用例 docstring 以 "TC-xxx (m04 AC-xxx)" 括注消歧, 编号语义与本文件既有 TC-xxx 不同.

接缝: subprocess 调 CLI + tmp_path (TECHNICAL.md 测试接缝).
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "roadmap.py"


def run_cli(*argv):
    """subprocess 调 CLI, 返回 (stdout 末行 JSON, 退出码, stdout 非空行数)."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *[str(a) for a in argv]],
        capture_output=True,
        text=True,
        timeout=30,
    )
    lines = [l for l in proc.stdout.splitlines() if l.strip()]
    obj = json.loads(lines[-1]) if lines else None
    return obj, proc.returncode, len(lines)


def legal_doc():
    """一份合法 ROADMAP.json 文档 (D005 schema)."""
    return {
        "schema_version": "0.0.1",
        "title": "测试路线图",
        "destination": "终点",
        "notes": [],
        "milestones": {
            "milestone-01": {
                "title": "调研",
                "status": "待处理",
                "type": "research",
                "blocked_by": [],
                "question": "怎么做?",
                "inputs": [],
                "output_dir": "docs/changes/test/",
                "artifacts": [],
                "close_summary": None,
            },
        },
        "unknown_seas": [],
        "off_course": [],
    }


def write_doc(path, doc):
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


@pytest.mark.parametrize("field,value,legal", [
    ("status", "已做完", "待处理"),
    ("type", "coding", "research"),
])
def test_invalid_enum_rejected(tmp_path, field, value, legal):
    """TC-002: 非法枚举被拒, 错误列合法值, 文件不变 (AC-002)."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    before = f.read_bytes()
    obj, code, _ = run_cli("save", f, f"milestones.milestone-01.{field}", value)
    assert code == 1
    assert obj["success"] is False
    assert legal in obj["error"]
    assert f.read_bytes() == before


@pytest.mark.parametrize("missing", ["question", "title", "type", "inputs", "output_dir"])
def test_new_milestone_missing_required_field(tmp_path, missing):
    """TC-003: 新增里程碑缺必填被拒, 错误列缺失字段名, 文件不变 (AC-003)."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    before = f.read_bytes()
    content = {"title": "新里程碑", "type": "task", "question": "做什么?",
               "inputs": [], "output_dir": None}
    del content[missing]
    obj, code, _ = run_cli(
        "save", f, "milestones.milestone-02", json.dumps(content, ensure_ascii=False))
    assert code == 1
    assert obj["success"] is False
    assert missing in obj["error"]
    assert f.read_bytes() == before


def test_acceptance_type_created_and_existing_task_converted(tmp_path):
    """验收为独立枚举; 新建及旧图 task 转验收均能经守门脚本保存."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    obj, code, _ = run_cli(
        "save", f, "milestones.milestone-02",
        json.dumps({"title": "验收", "type": "acceptance", "question": "逐项核对证据",
                    "inputs": [], "output_dir": "docs/changes/test/"},
                   ensure_ascii=False))
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("query", f, "milestones.milestone-02.type")
    assert code == 0 and obj["value"] == "acceptance"

    doc = legal_doc()
    doc["milestones"]["milestone-01"]["type"] = "task"
    write_doc(f, doc)
    obj, code, _ = run_cli("save", f, "milestones.milestone-01.type", '"acceptance"')
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("query", f, "milestones.milestone-01.type")
    assert code == 0 and obj["value"] == "acceptance"


def test_new_milestone_defaults_filled(tmp_path):
    """TC-003 变体: 合法新增里程碑填充 status/blocked_by 默认值 (BR-004)."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    obj, code, _ = run_cli(
        "save", f, "milestones.milestone-02",
        json.dumps({"title": "新里程碑", "type": "task", "question": "做什么?",
                    "inputs": [], "output_dir": None},
                   ensure_ascii=False))
    assert code == 0 and obj["success"] is True
    obj, _, _ = run_cli("query", f, "milestones.milestone-02.status")
    assert obj["value"] == "待处理"
    obj, _, _ = run_cli("query", f, "milestones.milestone-02.blocked_by")
    assert obj["value"] == []


@pytest.mark.parametrize("blocked_by", [
    ["milestone-09"],  # 引用不存在
    ["milestone-01"],  # 自环
    ["milestone-02"],  # 互环
])
def test_blocked_by_invalid_reference(tmp_path, blocked_by):
    """TC-004: 非法阻塞引用被拒且文件不变 (AC-004)."""
    f = tmp_path / "ROADMAP.json"
    doc = legal_doc()
    doc["milestones"]["milestone-02"] = {
        "title": "实现", "status": "待处理", "type": "task",
        "blocked_by": ["milestone-01"], "question": "做什么?",
        "inputs": [], "output_dir": None,
        "artifacts": [], "close_summary": None,
    }
    write_doc(f, doc)
    before = f.read_bytes()
    obj, code, _ = run_cli(
        "save", f, "milestones.milestone-01.blocked_by", json.dumps(blocked_by))
    assert code == 1
    assert obj["success"] is False
    assert f.read_bytes() == before


def test_unknown_top_level_field_rejected(tmp_path):
    """TC-104: 未知顶层字段拒绝写入 (D006-d)."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    before = f.read_bytes()
    obj, code, _ = run_cli("save", f, "galaxy", "{}")
    assert code == 1
    assert obj["success"] is False
    assert f.read_bytes() == before


def test_full_document_validation_rollback(tmp_path):
    """TC-105: 局部合法 (blocked_by 引用存在) 但整文档非法 (中间节点新建
    里程碑缺必填) -> 兜底校验不落盘, 文件保持原状 (D007)."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    before = f.read_bytes()
    obj, code, _ = run_cli(
        "save", f, "milestones.milestone-03.blocked_by", '["milestone-01"]')
    assert code == 1
    assert obj["success"] is False
    assert f.read_bytes() == before


def _task_fixture(tmp_path):
    """milestone-01.type 为 task 的夹具 (m04 枚举用例共用)."""
    f = tmp_path / "ROADMAP.json"
    doc = legal_doc()
    doc["milestones"]["milestone-01"]["type"] = "task"
    write_doc(f, doc)
    return f


def test_demo_type_accepted(tmp_path):
    """TC-002 (m04 AC-002): demo 成为合法类型, 写入后可读回."""
    f = _task_fixture(tmp_path)
    obj, code, _ = run_cli("save", f, "milestones.milestone-01.type", "demo")
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("query", f, "milestones.milestone-01.type")
    assert code == 0 and obj["value"] == "demo"


def test_prototype_type_rejected(tmp_path):
    """TC-003 (m04 AC-003): prototype 被拒且不留别名, 文件逐字节不变,
    错误列出全部合法值."""
    f = _task_fixture(tmp_path)
    before = f.read_bytes()
    obj, code, _ = run_cli("save", f, "milestones.milestone-01.type", "prototype")
    assert code == 1 and obj["success"] is False
    assert ("合法值: research, deliberate, demo, poc, spec, verification-plan, "
            "execution-plan, implementation, verification, task, acceptance") in obj["error"]
    legal_part = obj["error"].split("合法值: ")[1]
    assert "prototype" not in legal_part
    assert f.read_bytes() == before


def test_poc_type_accepted(tmp_path):
    """TC-005 (m04 AC-005): poc 成为合法类型, 写入后可读回."""
    f = _task_fixture(tmp_path)
    obj, code, _ = run_cli("save", f, "milestones.milestone-01.type", "poc")
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("query", f, "milestones.milestone-01.type")
    assert code == 0 and obj["value"] == "poc"


@pytest.mark.parametrize("kind", [
    "spec", "verification-plan", "execution-plan", "implementation", "verification",
])
def test_workflow_types_roundtrip(tmp_path, kind):
    """五个专门类型均可通过 CLI 创建, 并保存显式输入与共享产物目录."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    inputs = [{"content": "产品判据", "source": "docs/changes/test/PRODUCT.md#验收标准"}]
    content = {"title": "专门环节", "type": kind, "question": "交付什么?",
               "inputs": inputs, "output_dir": "docs/changes/test/"}
    obj, code, _ = run_cli("save", f, "milestones.milestone-02", json.dumps(content))
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("query", f, "milestones.milestone-02")
    assert code == 0
    assert obj["value"]["type"] == kind
    assert obj["value"]["inputs"] == inputs
    assert obj["value"]["output_dir"] == "docs/changes/test/"


@pytest.mark.parametrize("field,value", [
    ("inputs", "产品判据"),
    ("inputs", ["PRODUCT.md"]),
    ("inputs", [{}]),
    ("inputs", [{"content": "  "}]),
    ("inputs", [{"content": 7}]),
    ("inputs", [{"content": "产品判据", "source": None}]),
    ("inputs", [{"content": "产品判据", "source": ""}]),
    ("inputs", [{"content": "产品判据", "source": 7}]),
    ("inputs", [{"content": "产品判据", "path": "PRODUCT.md"}]),
    ("output_dir", []),
    ("output_dir", 7),
    ("output_dir", ""),
    ("output_dir", "  "),
])
def test_invalid_io_rejected_without_changing_file(tmp_path, field, value):
    """坏输入对象和坏目录被整文档校验拒绝, 原文件逐字节不变."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    before = f.read_bytes()
    obj, code, _ = run_cli("save", f, f"milestones.milestone-01.{field}", json.dumps(value))
    assert code == 1 and obj["success"] is False
    assert field in obj["error"]
    assert f.read_bytes() == before


def test_inputs_can_be_appended_and_updated_by_path(tmp_path):
    """输入清单沿既有 path 语法增改, 无来源的说明与 null 输出目录都可显式保存."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    obj, code, _ = run_cli("save", f, "milestones.milestone-01.inputs.0",
                          json.dumps({"content": "讨论所需背景"}))
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("save", f, "milestones.milestone-01.inputs.0.source", "notes.md")
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("query", f, "milestones.milestone-01.inputs")
    assert code == 0 and obj["value"] == [{"content": "讨论所需背景", "source": "notes.md"}]
    obj, code, _ = run_cli("save", f, "milestones.milestone-01.output_dir", "null")
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("query", f, "milestones.milestone-01.output_dir")
    assert code == 0 and obj["value"] is None


def test_bulk_creation_cannot_omit_io(tmp_path):
    """整体替换 milestones 也不能绕过新节点的输入/输出必填检查."""
    f = tmp_path / "ROADMAP.json"
    doc = legal_doc()
    write_doc(f, doc)
    before = f.read_bytes()
    node = dict(doc["milestones"]["milestone-01"])
    del node["inputs"]
    del node["output_dir"]
    doc["milestones"]["milestone-02"] = node
    obj, code, _ = run_cli("save", f, "milestones", json.dumps(doc["milestones"]))
    assert code == 1 and obj["success"] is False
    assert "inputs" in obj["error"] and "output_dir" in obj["error"]
    assert f.read_bytes() == before


@pytest.mark.parametrize("field", ["inputs", "output_dir"])
def test_existing_io_cannot_be_erased_by_replacement(tmp_path, field):
    """已经声明输入/输出的节点整体替换时, 也不能删除已必填字段."""
    f = tmp_path / "ROADMAP.json"
    doc = legal_doc()
    write_doc(f, doc)
    before = f.read_bytes()
    node = dict(doc["milestones"]["milestone-01"])
    del node[field]
    obj, code, _ = run_cli("save", f, "milestones.milestone-01", json.dumps(node))
    assert code == 1 and obj["success"] is False
    assert field in obj["error"]
    assert f.read_bytes() == before


def test_legacy_io_can_be_completed_without_guessing_defaults(tmp_path):
    """旧图可照常读写并逐项补输入/输出, 脚本不替历史节点猜来源和目录."""
    f = tmp_path / "ROADMAP.json"
    doc = legal_doc()
    del doc["milestones"]["milestone-01"]["inputs"]
    del doc["milestones"]["milestone-01"]["output_dir"]
    write_doc(f, doc)
    obj, code, _ = run_cli("save", f, "title", "旧图")
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("query", f, "milestones.milestone-01")
    assert code == 0
    assert "inputs" not in obj["value"] and "output_dir" not in obj["value"]
    obj, code, _ = run_cli("save", f, "milestones.milestone-01.inputs", "[]")
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("save", f, "milestones.milestone-01.output_dir", "docs/changes/test/")
    assert code == 0 and obj["success"] is True
    obj, code, _ = run_cli("query", f, "milestones.milestone-01.output_dir")
    assert code == 0 and obj["value"] == "docs/changes/test/"
