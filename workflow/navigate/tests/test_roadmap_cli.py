"""roadmap.py CLI 读写骨架测试 (ISSUE-01: TC-001, TC-005, TC-006, TC-007, TC-101).

接缝: subprocess 调 CLI + tmp_path (TECHNICAL.md 测试接缝).
"""

import json
import subprocess
import sys
from pathlib import Path

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


def make_legal_doc(path):
    """经 CLI 建一份含 milestone-01 的合法 ROADMAP.json."""
    obj, code, _ = run_cli("save", path, "title", "测试路线图")
    assert code == 0 and obj["success"] is True, obj
    obj, code, _ = run_cli(
        "save", path, "milestones.milestone-01",
        json.dumps({"title": "调研", "type": "research", "question": "怎么做?"},
                   ensure_ascii=False),
    )
    assert code == 0 and obj["success"] is True, obj


def test_save_then_query_roundtrip(tmp_path):
    """TC-001: 合法写入可经 query 读回, stdout 单行 JSON, 退出码正确 (AC-001)."""
    f = tmp_path / "ROADMAP.json"
    make_legal_doc(f)
    # 自动初始化的顶层结构可读
    obj, code, _ = run_cli("query", f, "schema_version")
    assert code == 0 and obj["value"] == "0.0.1"

    obj, code, nlines = run_cli("save", f, "milestones.milestone-01.status", "进行中")
    assert nlines == 1
    assert code == 0
    assert obj["success"] is True

    obj, code, nlines = run_cli("query", f, "milestones.milestone-01.status")
    assert nlines == 1
    assert code == 0
    assert obj["success"] is True
    assert obj["value"] == "进行中"


def test_array_index_append_and_out_of_bounds(tmp_path):
    """TC-005: notes 长度 2 时 notes.2 追加成功, notes.5 越界报错且文件不变 (AC-005)."""
    f = tmp_path / "ROADMAP.json"
    make_legal_doc(f)
    run_cli("save", f, "notes.0", "笔记一")
    run_cli("save", f, "notes.1", "笔记二")

    obj, code, _ = run_cli("save", f, "notes.2", "新笔记")
    assert code == 0 and obj["success"] is True
    obj, _, _ = run_cli("query", f, "notes")
    assert obj["value"] == ["笔记一", "笔记二", "新笔记"]

    before = f.read_bytes()
    obj, code, _ = run_cli("save", f, "notes.5", "越界笔记")
    assert code == 1
    assert obj["success"] is False
    assert f.read_bytes() == before


def test_delete_removes_file_then_query_errors(tmp_path):
    """TC-006: delete 后文件消失, 再 query 报文件不存在 (AC-006)."""
    f = tmp_path / "ROADMAP.json"
    make_legal_doc(f)
    obj, code, _ = run_cli("delete", f)
    assert code == 0 and obj["success"] is True
    assert not f.exists()

    obj, code, _ = run_cli("query", f, "title")
    assert code == 1
    assert obj["success"] is False
    assert "文件不存在" in obj["error"]


def test_query_missing_path_errors(tmp_path):
    """TC-007: query 不存在路径报错且指明路径 (AC-007)."""
    f = tmp_path / "ROADMAP.json"
    make_legal_doc(f)
    obj, code, _ = run_cli("query", f, "milestones.milestone-99")
    assert code == 1
    assert obj["success"] is False
    assert "milestones.milestone-99" in obj["error"]


def test_no_md_or_temp_residue(tmp_path):
    """TC-101: save/query/delete 一轮后目录内无 .md 与临时文件残留 (BR-007)."""
    f = tmp_path / "ROADMAP.json"
    make_legal_doc(f)
    run_cli("save", f, "notes.0", "笔记")
    run_cli("query", f, "notes.0")
    assert {p.name for p in tmp_path.iterdir()} == {"ROADMAP.json"}

    run_cli("delete", f)
    assert {p.name for p in tmp_path.iterdir()} == set()
