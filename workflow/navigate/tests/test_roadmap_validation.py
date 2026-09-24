"""roadmap.py 守门校验测试 (ISSUE-02: TC-002, TC-003, TC-004, TC-104, TC-105).

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


@pytest.mark.parametrize("missing", ["question", "title", "type"])
def test_new_milestone_missing_required_field(tmp_path, missing):
    """TC-003: 新增里程碑缺必填被拒, 错误列缺失字段名, 文件不变 (AC-003)."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    before = f.read_bytes()
    content = {"title": "新里程碑", "type": "task", "question": "做什么?"}
    del content[missing]
    obj, code, _ = run_cli(
        "save", f, "milestones.milestone-02", json.dumps(content, ensure_ascii=False))
    assert code == 1
    assert obj["success"] is False
    assert missing in obj["error"]
    assert f.read_bytes() == before


def test_new_milestone_defaults_filled(tmp_path):
    """TC-003 变体: 合法新增里程碑填充 status/blocked_by 默认值 (BR-004)."""
    f = tmp_path / "ROADMAP.json"
    write_doc(f, legal_doc())
    obj, code, _ = run_cli(
        "save", f, "milestones.milestone-02",
        json.dumps({"title": "新里程碑", "type": "task", "question": "做什么?"},
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
