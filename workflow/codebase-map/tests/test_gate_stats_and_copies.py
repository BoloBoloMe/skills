"""ISSUE-03 用例: 门禁判定, 统计分母, 副本分发与 state.json 登记
(TC-005, TC-006, TC-03-01..TC-03-05).

接缝与口径 (m25 EXECUTION 验证策略):
- 容器内 /run/.containerenv 在场, CLI 前置检查第一关就拒绝, 门禁/统计/副本
  无法从真实入口到达, 按内部接缝直接 import codemap_analyze 调 run_build
  (先例 test_analyze_pipeline); "退出码非 0" 由 CLI _emit 的 success -> 0/1
  映射承接, 该形状已由 TC-01-06 固定.
- 进程接缝: stub podman + fixture merge 产物 (CODEMAP_STUB_CC_JSON 注入,
  stub 注入 stub_run 供覆盖断言) 只证明流程接线与归因逻辑, 不构成"分析可用"
  证据; 真实库的门禁数值与分母由 ISSUE-07 在宿主承接.
- 文件接缝: 官方前端 web.zip 伪产物 + 预置 sha256 期望值 (先例 TC-02).
- fixture merge 产物形状 = m23 实测: files 树 + lenses.dependency.nodes 的
  level 与 lenses.dependency.edges.dependencies 的 isCyclic/isPointingUpwards.
"""
from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path

from codemap_helpers import make_target  # 先导入: 它负责把 scripts/ 注入 sys.path

import codemap_common as cmc  # noqa: E402
import codemap_analyze as cma  # noqa: E402

from codemap_stub_helpers import (
    make_merge_fixture,
    make_stub_podman,
    preset_frontend_cache,
    stub_env,
)


# ---------------------------------------------------------------------------
# 共用工具
# ---------------------------------------------------------------------------

# 门禁可通过的最小 merge 产物: 3 个文件节点, level 0/1/2 共 3 种, 3 条边
# (1 条 isCyclic, 1 条 isPointingUpwards)
IN_TREE = ("src/Main.java", "src/Util.java", "src/Helper.java")
LEVELS = {"src/Main.java": 0, "src/Util.java": 1, "src/Helper.java": 2}
EDGES = [
    ("src/Main.java", "src/Util.java", False, False),
    ("src/Util.java", "src/Helper.java", True, False),
    ("src/Helper.java", "src/Main.java", False, True),
]


def make_gate_fixture(tmp_path, *, levels=None, edges=None, name="fixture-cc.json"):
    return make_merge_fixture(
        tmp_path / name,
        in_tree=IN_TREE,
        levels=LEVELS if levels is None else levels,
        edges=EDGES if edges is None else edges,
    )


def make_stats_tree(tmp_path, name="stats-lib"):
    """统计归因用的最小目标树: 每类口径桶至少一份磁盘文件.

    src/Main|Util|Helper.java 进依赖树; src/Dead.java 零声明;
    src/SkipTest.java 命中 TestFileDetector 名字规则 (tool_defaults);
    src/test/Bar.java 测试目录; generated/X.java 自定义排除;
    target/Y.java 与 node_modules/z.js 默认结构性排除; README.md 扩展名
    分析端不支持.
    """
    target = make_target(tmp_path, name=name)
    files = {
        "src/Main.java": "class Main {}\n",
        "src/Util.java": "class Util {}\n",
        "src/Helper.java": "class Helper {}\n",
        "src/Dead.java": "class Dead {}\n",
        "src/SkipTest.java": "class SkipTest {}\n",
        "src/test/Bar.java": "class Bar {}\n",
        "generated/X.java": "class X {}\n",
        "target/Y.java": "class Y {}\n",
        "node_modules/z.js": "// js\n",
        "README.md": "# demo\n",
    }
    for rel, body in files.items():
        path = target / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
    return target


def build_with_fixture(monkeypatch, tmp_path, target, fixture, *, user_excludes=()):
    """stub podman (PATH) + fixture merge 产物 (CODEMAP_STUB_CC_JSON) + 隔离
    运行时目录, 直调 codemap_analyze.run_build (内部接缝, 先例 TC-02)."""
    bin_dir = make_stub_podman(tmp_path)
    state = tmp_path / "stub-state"
    for key, value in stub_env(bin_dir, state, image_present=True).items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("CODEMAP_STUB_CC_JSON", str(fixture))
    frontend_sha = preset_frontend_cache(tmp_path / "codemap-rt")
    monkeypatch.setattr(cmc, "FRONTEND_ZIP_SHA256", frontend_sha)
    runtime = (tmp_path / "codemap-rt").resolve()
    result = cma.run_build(Path(target), list(user_excludes), runtime_base=runtime)
    return result, runtime, state


def load_state(runtime: Path) -> dict | None:
    path = runtime / "state.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def assert_stats_complete(stats: dict):
    """stats 字段齐全: 分母, 五类 excluded, 零声明清单, 边计数."""
    assert set(stats) == {"scanned_files", "files_in_tree", "excluded",
                          "zero_declaration", "unsupported_extensions",
                          "cyclic_edges", "upward_edges"}
    assert set(stats["excluded"]) == {"tests", "build_dirs", "custom",
                                      "dot_codebase_map", "tool_defaults"}


def disk_file_count(target: Path) -> int:
    return sum(1 for root, _dirs, names in os.walk(target) for _f in names)


# ---------------------------------------------------------------------------
# TC-005 (AC-005 主用例): 原件在库, 副本进 serve-root, 键与登记
# ---------------------------------------------------------------------------


def test_tc_005_build_delivers_original_copy_key_and_registration(monkeypatch, tmp_path):
    """build (stub + fixture) 后: 目标库出现 .codebase-map/cc.json; serve-root
    副本与 index.html 同目录且文件名 = keys[].key, 内容与原件一致; 键形如
    <清洗后库名>-<8 位十六进制>.cc.json; state.json.data_keys 登记齐全."""
    target = make_target(tmp_path, name="demo-lib")
    fixture = make_gate_fixture(tmp_path)
    result, runtime, state = build_with_fixture(monkeypatch, tmp_path, target, fixture)
    assert result["success"] is True, result

    # 键: 清洗后库名 + 8 位路径哈希 (BR-011/BR-032, m25 D005)
    key = result["key"]
    assert key == cmc.data_key(target)
    assert re.fullmatch(r"[A-Za-z0-9._-]+-[0-9a-f]{8}\.cc\.json", key), key
    assert key.startswith("demo-lib-")

    # 原件: 目标库 .codebase-map/cc.json (BR-010)
    original = Path(result["cc_json_path"])
    assert original == target / ".codebase-map" / "cc.json"
    assert original.is_file()

    # 副本: serve-root/<key>, 与 index.html 同目录, 内容与原件一致 (BR-012)
    serve_root = runtime / "serve-root"
    copy = Path(result["serve_copy_path"])
    assert copy.parent == serve_root
    assert (serve_root / "index.html").is_file(), "副本必须与 index.html 同目录"
    assert copy.name == key
    assert copy.is_file()
    assert copy.read_bytes() == original.read_bytes(), "副本内容必须与原件一致"

    # state.json.data_keys: 恰一条, 字段齐全 (锁内写入, TECHNICAL)
    state_data = load_state(runtime)
    assert state_data is not None
    entries = state_data["data_keys"]
    assert len(entries) == 1
    entry = entries[0]
    assert entry["key"] == key
    assert entry["source_cc_json"] == str(original)
    assert entry["bytes"] == original.stat().st_size
    datetime.datetime.fromisoformat(entry["built_at"])  # UTC ISO8601

    # gate/stats 字段齐备且门禁通过 (fixture: 边 3, 层号 3 种)
    assert result["gate"] == {"passed": True, "edges": 3, "level_kinds": 3}
    assert_stats_complete(result["stats"])
    assert result["initialization"]["performed"] is False  # 前端与镜像已预置


# ---------------------------------------------------------------------------
# TC-006 (AC-006 主用例): 两条门禁退化场景
# ---------------------------------------------------------------------------


def test_tc_006_gate_rejects_zero_dependency_edges(monkeypatch, tmp_path):
    """边为 0: run_build 失败 (CLI 映射退出码非 0), error.code == gate_failed,
    gate.reason 含"边为 0"; 原件照写, serve-root 无该库副本, state.json 不登记;
    stats 与 zero_declaration 照常完整输出, 分母不因失败省掉."""
    target = make_stats_tree(tmp_path, name="no-edges-lib")
    fixture = make_gate_fixture(tmp_path, edges=[], name="zero-edges.json")
    result, runtime, _state = build_with_fixture(
        monkeypatch, tmp_path, target, fixture, user_excludes=("generated",))

    assert result["success"] is False
    assert result["error"]["code"] == "gate_failed"
    gate = result["gate"]
    assert gate["passed"] is False and gate["edges"] == 0
    assert "边为 0" in gate["reason"] and "0 条" in gate["reason"]

    # 原件照写供复查 (m25 D001)
    original = target / ".codebase-map" / "cc.json"
    assert original.is_file()
    written = json.loads(original.read_text(encoding="utf-8"))
    assert written["meta"]["projectName"] == "stub-merge"

    # 副本不出现, 清单不登记
    key = result["key"]
    serve_root = runtime / "serve-root"
    assert key not in {p.name for p in serve_root.iterdir()}
    assert load_state(runtime) is None, "门禁失败不得写 state.json/登记 data_keys"
    assert "serve_copy_path" not in result

    # stats 与 initialization 照常完整 (不因失败省掉分母)
    assert_stats_complete(result["stats"])
    assert result["stats"]["files_in_tree"] == 3
    assert result["initialization"]["performed"] is False


def test_tc_006_gate_rejects_too_few_level_kinds(monkeypatch, tmp_path):
    """层号只有 0 与 1 两种: gate.reason 含"2 种, 少于 3 种"; 其余同上:
    原件照写, 无副本, 分母与零声明清单照常输出."""
    target = make_stats_tree(tmp_path, name="flat-lib")
    fixture = make_gate_fixture(
        tmp_path, levels={"src/Main.java": 0, "src/Util.java": 1},
        name="two-levels.json")
    result, runtime, _state = build_with_fixture(
        monkeypatch, tmp_path, target, fixture, user_excludes=("generated",))

    assert result["success"] is False
    assert result["error"]["code"] == "gate_failed"
    gate = result["gate"]
    assert gate["passed"] is False
    assert gate["edges"] == 3, "边数满足时不得误报边为 0"
    assert gate["level_kinds"] == 2
    assert "2 种, 少于 3 种" in gate["reason"]

    assert (target / ".codebase-map" / "cc.json").is_file()
    key = result["key"]
    serve_root = runtime / "serve-root"
    assert key not in {p.name for p in serve_root.iterdir()}
    assert load_state(runtime) is None
    assert "serve_copy_path" not in result

    assert_stats_complete(result["stats"])
    stats = result["stats"]
    assert stats["zero_declaration"] == [{"path": "src/Dead.java", "reason": "零声明"}]
    assert result["initialization"]["performed"] is False


# ---------------------------------------------------------------------------
# TC-03-01: 同库重跑, 同键覆盖, data_keys 无重复
# ---------------------------------------------------------------------------


def test_tc_03_01_rerun_same_key_overwrites_copy_and_entry(monkeypatch, tmp_path):
    target = make_target(tmp_path, name="rerun-lib")
    # 第二次 build 用多一条边的 fixture: 库变了, 产物字节数真实前进
    fixture1 = make_gate_fixture(tmp_path, name="cc-run1.json")
    fixture2 = make_gate_fixture(
        tmp_path,
        edges=[*EDGES, ("src/Main.java", "src/Helper.java", False, False)],
        name="cc-run2.json")
    result1, runtime, _s1 = build_with_fixture(monkeypatch, tmp_path, target, fixture1)
    assert result1["success"] is True
    key = result1["key"]
    copy = Path(result1["serve_copy_path"])
    bytes1 = copy.read_bytes()
    entry1 = load_state(runtime)["data_keys"][0]

    result2, runtime2, _s2 = build_with_fixture(monkeypatch, tmp_path, target, fixture2)
    assert result2["success"] is True
    assert result2["key"] == key, "同库重跑键不变 (m13 D020)"

    copy2 = Path(result2["serve_copy_path"])
    assert copy2 == copy
    bytes2 = copy2.read_bytes()
    assert bytes2 != bytes1, "stub_run 前进, 覆盖而非保留旧副本"
    assert bytes2 == (target / ".codebase-map" / "cc.json").read_bytes()

    entries = load_state(runtime2)["data_keys"]
    assert len(entries) == 1, f"data_keys 不得出现重复条目: {entries}"
    entry2 = entries[0]
    assert entry2["key"] == key
    assert entry2["bytes"] == len(bytes2) and entry2["bytes"] != entry1["bytes"]
    assert entry2["built_at"] >= entry1["built_at"], "built_at 随重跑刷新"


# ---------------------------------------------------------------------------
# TC-03-02: 同名不同路径的两个库, 键不同, 互不覆盖
# ---------------------------------------------------------------------------


def test_tc_03_02_same_name_different_paths_get_distinct_keys(monkeypatch, tmp_path):
    target_a = make_target(tmp_path / "a", name="demo")
    target_b = make_target(tmp_path / "b", name="demo")
    fixture = make_gate_fixture(tmp_path)
    result_a, runtime, _sa = build_with_fixture(monkeypatch, tmp_path, target_a, fixture)
    result_b, runtime_b, _sb = build_with_fixture(monkeypatch, tmp_path, target_b, fixture)
    assert result_a["success"] is True and result_b["success"] is True

    key_a, key_b = result_a["key"], result_b["key"]
    assert key_a != key_b, "同名不同库靠路径哈希区分 (BR-011)"
    assert cmc.data_key(target_a) == key_a and cmc.data_key(target_b) == key_b

    serve_root = runtime / "serve-root"
    copy_a = Path(result_a["serve_copy_path"])
    copy_b = Path(result_b["serve_copy_path"])
    assert copy_a.is_file() and copy_b.is_file()
    assert copy_a.read_bytes() != copy_b.read_bytes()
    assert copy_a.read_bytes() == (target_a / ".codebase-map" / "cc.json").read_bytes(), \
        "后 build 的库不得覆盖先 build 的副本"

    entries = {e["key"] for e in load_state(runtime_b)["data_keys"]}
    assert entries == {key_a, key_b}


# ---------------------------------------------------------------------------
# TC-03-03: build 新库不动其它库副本 (BR-036, m25 D003)
# ---------------------------------------------------------------------------


def test_tc_03_03_building_new_library_leaves_other_copies_alone(monkeypatch, tmp_path):
    fixture = make_gate_fixture(tmp_path)
    lib_a = make_target(tmp_path, name="alpha")
    lib_b = make_target(tmp_path, name="beta")
    result_a, runtime, _sa = build_with_fixture(monkeypatch, tmp_path, lib_a, fixture)
    result_b, runtime_b, _sb = build_with_fixture(monkeypatch, tmp_path, lib_b, fixture)
    assert result_a["success"] is True and result_b["success"] is True
    serve_root = runtime / "serve-root"
    copy_a = Path(result_a["serve_copy_path"])
    copy_b = Path(result_b["serve_copy_path"])
    bytes_a, bytes_b = copy_a.read_bytes(), copy_b.read_bytes()

    lib_c = make_target(tmp_path, name="gamma")
    result_c, runtime_c, _sc = build_with_fixture(monkeypatch, tmp_path, lib_c, fixture)
    assert result_c["success"] is True

    # A 与 B 的副本文件仍在且内容未变; data_keys 仍含它们 (不自动清理)
    assert copy_a.is_file() and copy_a.read_bytes() == bytes_a
    assert copy_b.is_file() and copy_b.read_bytes() == bytes_b
    entries = load_state(runtime_c)["data_keys"]
    assert {e["key"] for e in entries} == {result_a["key"], result_b["key"], result_c["key"]}


# ---------------------------------------------------------------------------
# TC-03-04 (BR-024, 口径归因): 统计等式与逐类归因
# ---------------------------------------------------------------------------


def test_tc_03_04_stats_equation_and_per_bucket_attribution(monkeypatch, tmp_path):
    """统计等式 (compute_stats 函数头写明, 本用例固定):
    files_in_tree + 五类 excluded + len(zero_declaration) == 磁盘文件总数;
    tool_defaults 与 custom 分列, 逐桶数值可解释."""
    target = make_stats_tree(tmp_path, name="attribution-lib")
    fixture = make_gate_fixture(tmp_path)
    result, _runtime, _s = build_with_fixture(
        monkeypatch, tmp_path, target, fixture, user_excludes=("generated",))
    assert result["success"] is True, result
    stats = result["stats"]
    assert_stats_complete(stats)

    # 统计等式: 每份磁盘文件恰好归入一项
    excluded = stats["excluded"]
    total = (stats["files_in_tree"] + sum(excluded.values())
             + len(stats["zero_declaration"]))
    assert total == disk_file_count(target), \
        f"等式不平: {total} != 磁盘 {disk_file_count(target)}"

    # 逐桶归因 (fixture 每类至少一份文件, 数值全部可解释)
    assert stats["files_in_tree"] == 3
    assert excluded["dot_codebase_map"] == 1  # 本次写出的 .codebase-map/cc.json
    assert excluded["build_dirs"] == 2  # target/Y.java, node_modules/z.js
    assert excluded["custom"] == 1  # generated/X.java (--exclude generated)
    assert excluded["tests"] == 1  # src/test/Bar.java
    assert excluded["tool_defaults"] == 2  # src/SkipTest.java, README.md
    assert stats["zero_declaration"] == [{"path": "src/Dead.java", "reason": "零声明"}]
    assert stats["scanned_files"] == 5  # Main/Util/Helper/Dead/SkipTest
    # scanned 分母口径: 依赖树文件数 + 零声明 + 工具默认过滤里受支持扩展名部分
    unsupported_total = sum(item["count"] for item in stats["unsupported_extensions"])
    assert stats["scanned_files"] == (
        stats["files_in_tree"] + len(stats["zero_declaration"])
        + excluded["tool_defaults"] - unsupported_total)
    # tool_defaults 与 custom 分列不相加串味: 两类各自成立, 不混算
    assert (excluded["tool_defaults"], excluded["custom"]) == (2, 1)
    assert stats["cyclic_edges"] == 1 and stats["upward_edges"] == 1


# ---------------------------------------------------------------------------
# TC-03-05 (BR-025): 扩展名维度只汇总不支持的扩展名
# ---------------------------------------------------------------------------


def test_tc_03_05_unsupported_extensions_summary_is_isolated(monkeypatch, tmp_path):
    target = make_stats_tree(tmp_path, name="ext-lib")
    fixture = make_gate_fixture(tmp_path)
    result, _runtime, _s = build_with_fixture(
        monkeypatch, tmp_path, target, fixture, user_excludes=("generated",))
    assert result["success"] is True, result
    stats = result["stats"]

    # 只有 .md (无任何同名扩展文件进树) 进 unsupported_extensions
    assert stats["unsupported_extensions"] == [{"ext": ".md", "count": 1}]
    # 零声明文件与被排除规则命中的文件按类别给计数与清单, 不混进扩展名维度
    listed_paths = {item["path"] for item in stats["zero_declaration"]}
    assert listed_paths == {"src/Dead.java"}
    assert "src/Dead.java" not in json.dumps(stats["unsupported_extensions"])
    assert "src/test/Bar.java" not in json.dumps(stats["unsupported_extensions"])
    assert "generated/X.java" not in json.dumps(stats["unsupported_extensions"])
    assert not any(item["ext"] == ".java" for item in stats["unsupported_extensions"]), \
        ".java 有文件进树, 属受支持扩展名, 不得汇总"
    assert not any(item["ext"] == ".cc.json" for item in stats["unsupported_extensions"]), \
        ".codebase-map 下的数据文件是排除类, 不进扩展名维度"
