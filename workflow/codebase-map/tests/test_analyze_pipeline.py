"""ISSUE-02 用例: build 的首次初始化与三步分析流水线 (TC-02-01..TC-02-09).

接缝与口径 (m25 EXECUTION 验证策略, 任务书 测试接缝):
- 进程接缝: 本地 stub podman 脚本只存在于用例的 tmp_path, 经 PATH 注入; 它
  记录完整 argv 供断言 (BR-017 的观察点), stub 产物不是"分析可用"证据, 真实
  分析由 ISSUE-07 在宿主承接.
- 容器内 /run/.containerenv 在场, CLI 入口的前置检查第一关就拒绝, 因此本组
  用例按内部接缝直接 import codemap_analyze 调 run_build, 注入临时运行时目录.
- 文件接缝: 官方前端 web.zip 本地可替换; 需要"校验通过"的用例按 m25 EXECUTION
  ("测试可放伪产物并预置 sha256 期望值") monkeypatch codemap_common 的期望
  常量为伪产物真实哈希, 生产路径没有任何旁路; 需要校验失败的用例 (TC-02-07)
  不打补丁, 用真常量自然失配.
- 容器内没有出网: 下载与 pull 的真实网络路径不造替身, 记未验证归 ISSUE-07.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from codemap_helpers import make_target  # 先导入: 它负责把 scripts/ 注入 sys.path

import codemap_common as cmc  # noqa: E402
import codemap_analyze as cma  # noqa: E402

from codemap_stub_helpers import (
    ccsh_part,
    make_real_zip_bytes,
    preset_frontend_cache,
    pseudo_sha,
    stub_calls,
    stub_env,
    stub_run_argv,
    make_stub_podman,
)


# ---------------------------------------------------------------------------
# 共用工具
# ---------------------------------------------------------------------------


def make_java_target(tmp_path, name="demo-lib"):
    """造一个带少量源码的目标库 (TC-02-05 的完整性比对用)."""
    target = make_target(tmp_path, name=name)
    (target / "src").mkdir()
    (target / "src" / "Main.java").write_text("public class Main {}\n", encoding="utf-8")
    (target / "lib").mkdir()
    (target / "lib" / "Util.java").write_text("public class Util {}\n", encoding="utf-8")
    (target / "README.md").write_text("demo\n", encoding="utf-8")
    return target


def build_with_stub(monkeypatch, tmp_path, target, *, user_excludes=(), image_present=True,
                    repo_digests=None, frontend_sha=None):
    """注入 stub podman (PATH) 与隔离运行时目录后直调 codemap_analyze.run_build.

    frontend_sha 不为 None 时把它预置为 web.zip 期望哈希 (m25 EXECUTION 文件
    接缝); 为 None 时期望值保持 codemap_common 常量 (校验失败用例).
    """
    bin_dir = make_stub_podman(tmp_path)
    state = tmp_path / "stub-state"
    for key, value in stub_env(bin_dir, state, image_present=image_present,
                               repo_digests=repo_digests).items():
        monkeypatch.setenv(key, value)
    if frontend_sha is not None:
        monkeypatch.setattr(cmc, "FRONTEND_ZIP_SHA256", frontend_sha)
    runtime = tmp_path / "codemap-rt"
    result = cma.run_build(Path(target), list(user_excludes), runtime_base=runtime)
    return result, Path(runtime).resolve(), state


def snapshot_files(target: Path) -> dict:
    """目标库全量文件名 -> 内容 sha256 (TC-02-05)."""
    return {
        str(p.relative_to(target)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(target.rglob("*")) if p.is_file()
    }


def assert_full_build_fields(result: dict, target: Path):
    """build 成功结果的任务书字段: 本 issue 只有 initialization/duration/cc_json_path/target/key."""
    assert result["success"] is True
    assert result["command"] == "build"
    assert result["target"] == str(Path(target).resolve())
    assert result["key"] == cmc.data_key(target)
    assert result["cc_json_path"] == str(Path(target).resolve() / ".codebase-map" / "cc.json")
    assert isinstance(result["duration_seconds"], (int, float)) and result["duration_seconds"] >= 0
    # ISSUE-03 的字段不得提前出现, 也不写假值
    for forbidden in ("gate", "stats", "serve_copy_path"):
        assert forbidden not in result, f"门禁/统计/副本字段 {forbidden} 归 ISSUE-03, 不应出现"


# ---------------------------------------------------------------------------
# TC-02-01 (BR-017 观察点): 三次 podman run 的隔离参数
# ---------------------------------------------------------------------------


def test_tc_02_01_podman_run_isolation_contract(monkeypatch, tmp_path):
    """三次 podman run 都带 --rm/--network=none/--userns=keep-id, 源码挂 :ro,
    出目录挂 cache/work; 没有 --privileged/docker socket/-p/--publish.

    stub 不是分析可用证据; 这里只核对参数构造与流程接线.
    """
    target = make_java_target(tmp_path, name="iso-lib")
    frontend_sha = preset_frontend_cache(tmp_path / "codemap-rt")
    result, runtime, state = build_with_stub(
        monkeypatch, tmp_path, target, frontend_sha=frontend_sha)
    assert_full_build_fields(result, target)

    runs = stub_run_argv(state)
    assert len(runs) == 3, f"应恰好三次 podman run: {json.dumps(runs, ensure_ascii=False)}"
    work_dir = runtime / "cache" / "work"
    for argv in runs:
        assert "--rm" in argv
        assert "--network=none" in argv
        assert "--userns=keep-id" in argv
        specs = [argv[i + 1] for i, arg in enumerate(argv) if arg == "-v"]
        assert f"{Path(target).resolve()}:/proj:ro" in specs, f"源码必须只读挂载: {specs}"
        assert f"{work_dir}:/out" in specs, f"出目录必须挂 cache/work: {specs}"
        assert "--privileged" not in argv
        assert not any("docker.sock" in arg for arg in argv), "不得挂 docker socket"
        assert "-p" not in argv and "--publish" not in argv, "不得映射端口"
        assert argv[argv.index(cmc.IMAGE_TAG) + 1] == "ccsh"
    # 三步依次是 dependencyparser / unifiedparser / merge
    steps = [argv[argv.index(cmc.IMAGE_TAG) + 2] for argv in runs]
    assert steps == ["dependencyparser", "unifiedparser", "merge"]


# ---------------------------------------------------------------------------
# TC-02-02: 三步 ccsh 参数, 排除正则, 中间产物与覆盖
# ---------------------------------------------------------------------------


def test_tc_02_02_three_ccsh_steps_params_regex_and_workdir(monkeypatch, tmp_path):
    """第一步带 -e <排除正则> (与 collect_excludes 同源, 逐条转义), 第二步
    unifiedparser -o, 第三步 merge metrics 在前 deps 在后; 中间产物落
    cache/work/ 且第二次运行覆盖."""
    target = make_target(tmp_path, name="params-lib")
    user_excludes = ("gen*ated",)
    frontend_sha = preset_frontend_cache(tmp_path / "codemap-rt")
    result, runtime, state = build_with_stub(
        monkeypatch, tmp_path, target, user_excludes=user_excludes, frontend_sha=frontend_sha)
    assert result["success"] is True

    runs = stub_run_argv(state)
    assert len(runs) == 3
    expected_step1 = ["ccsh", "dependencyparser", "/proj", "-o", "/out/deps.cc.json", "-nc",
                      *(item for regex in cmc.excluded_regexes(user_excludes)
                        for item in ("-e", regex))]
    assert ccsh_part(runs[0]) == expected_step1
    # -e 逐条出现且与同一份排除数据一致 (BR-015/D019), 用户 glob 逐字转义
    e_values = [runs[0][i + 1] for i, arg in enumerate(runs[0]) if arg == "-e"]
    assert e_values == list(cmc.excluded_regexes(user_excludes))
    assert "gen\\*ated" in e_values  # glob 元字符 * 被转义, 不当正则交给 ccsh
    assert ccsh_part(runs[1]) == ["ccsh", "unifiedparser", "/proj", "-nc", "-o", "/out/metrics.cc.json"]
    assert ccsh_part(runs[2]) == ["ccsh", "merge", "/out/metrics.cc.json", "/out/deps.cc.json",
                                  "-o", "/out/cc.json", "-nc"]

    # 每步各自一份日志, 里面有完整 argv
    logs = sorted((runtime / "logs").glob("analyze-step*.log"))
    assert [p.name for p in logs] == [
        "analyze-step1-dependencyparser.log",
        "analyze-step2-unifiedparser.log",
        "analyze-step3-merge.log",
    ]
    for log in logs:
        text = log.read_text(encoding="utf-8")
        assert "argv: [" in text and "exit: 0" in text
    assert len(result["analysis_logs"]) == 3

    # 中间产物落在 cache/work/
    work = runtime / "cache" / "work"
    assert {p.name for p in work.iterdir()} == {"deps.cc.json", "metrics.cc.json", "cc.json"}

    # 第二次运行覆盖: stub 的 run 序号前进, 产物内容被替换而不是追加
    result2, runtime2, state2 = build_with_stub(
        monkeypatch, tmp_path, target, user_excludes=user_excludes, frontend_sha=frontend_sha)
    assert result2["success"] is True
    runs2 = stub_run_argv(state2)
    assert len(runs2) == 6
    first_cc = json.loads((work / "cc.json").read_text(encoding="utf-8"))
    assert first_cc == {"stub": "cc.json", "run": 6}, "第二次 merge 产物应覆盖第一次 (run 序号 6)"


# ---------------------------------------------------------------------------
# TC-02-03: 本地镜像与前端产物齐备时不进初始化 (BR-027/BR-028)
# ---------------------------------------------------------------------------


def test_tc_02_03_complete_environment_skips_initialization(monkeypatch, tmp_path):
    """镜像在场 (stub inspect 即成功) 且前端产物齐备 -> performed=false, 无
    notice, steps 空, 无 pull; cache.json 字段齐全且版本/镜像值为给定常量."""
    target = make_target(tmp_path, name="ready-lib")
    runtime = tmp_path / "codemap-rt"
    frontend_sha = preset_frontend_cache(runtime)  # zip+unpacked+cache.json 版本记录+serve-root
    result, runtime_resolved, state = build_with_stub(
        monkeypatch, tmp_path, target, frontend_sha=frontend_sha)
    assert_full_build_fields(result, target)

    init = result["initialization"]
    assert init["performed"] is False
    assert init["steps"] == []
    assert "notice" not in init
    assert not any(entry["argv"][:1] == ["pull"] for entry in stub_calls(state)), \
        "本地已有镜像时不得 pull"

    cache = json.loads((runtime_resolved / "cache" / "cache.json").read_text(encoding="utf-8"))
    assert set(cache) == {"image", "frontend", "excluded_globs", "written_at"}
    assert cache["image"]["tag"] == cmc.IMAGE_TAG
    assert cache["image"]["single_arch_digest"] == cmc.IMAGE_SINGLE_ARCH_DIGEST
    assert cache["image"]["multi_arch_digest"] == cmc.IMAGE_MULTI_ARCH_DIGEST
    assert cache["image"]["verified_at"]
    assert cache["frontend"]["version"] == "vis-2.9.1"
    assert cache["frontend"]["zip_sha256"] == frontend_sha
    assert cache["frontend"]["unpacked_at"]
    assert cache["excluded_globs"] == list(cmc.collect_excludes([]))
    assert cache["written_at"]


# ---------------------------------------------------------------------------
# TC-02-04: 同库重跑覆盖同一路径, 不留历史版本
# ---------------------------------------------------------------------------


def test_tc_02_04_rerun_overwrites_same_path_and_key(monkeypatch, tmp_path):
    target = make_target(tmp_path, name="rerun-lib")
    frontend_sha = preset_frontend_cache(tmp_path / "codemap-rt")
    result1, runtime, state1 = build_with_stub(monkeypatch, tmp_path, target, frontend_sha=frontend_sha)
    assert result1["success"] is True
    dest1 = Path(result1["cc_json_path"])
    key1 = result1["key"]
    bytes1 = dest1.read_bytes()

    # 模拟上次运行残留的历史文件: 下次运行必须被清掉 (cache/work 覆盖式复用)
    work = runtime / "cache" / "work"
    (work / "legacy-cc-history.json").write_text("STALE HISTORY", encoding="utf-8")

    result2, runtime2, state2 = build_with_stub(monkeypatch, tmp_path, target, frontend_sha=frontend_sha)
    assert result2["success"] is True
    dest2 = Path(result2["cc_json_path"])
    assert dest2 == dest1, "同库重跑必须覆盖同一路径"
    assert result2["key"] == key1, "同库重跑键不变"
    bytes2 = dest2.read_bytes()
    assert bytes2 != bytes1, "第二次 merge 产物内容应前进 (run 序号), 证明是覆盖"
    assert bytes2 == (work / "cc.json").read_bytes()
    assert {p.name for p in work.iterdir()} == {"deps.cc.json", "metrics.cc.json", "cc.json"}, \
        "cache/work/ 不得出现历史版本文件"


# ---------------------------------------------------------------------------
# TC-02-05: 跑完整 build (stub) 后目标库只多 .codebase-map/cc.json (BR-031)
# ---------------------------------------------------------------------------


def test_tc_02_05_target_library_only_gains_cc_json(monkeypatch, tmp_path):
    """stub 跑完整 build 后全量文件名与内容哈希比对: 只多出 .codebase-map/cc.json,
    其它文件未变; 原件与 merge 产物逐字节一致 (不解包改写)."""
    target = make_java_target(tmp_path, name="intact-lib")
    before = snapshot_files(target)
    frontend_sha = preset_frontend_cache(tmp_path / "codemap-rt")
    result, runtime, state = build_with_stub(monkeypatch, tmp_path, target, frontend_sha=frontend_sha)
    assert_full_build_fields(result, target)

    after = snapshot_files(target)
    added = set(after) - set(before)
    assert added == {".codebase-map/cc.json"}, f"目标库只应多出原件, 实际: {sorted(added)}"
    removed = set(before) - set(after)
    assert removed == set()
    changed = {k for k in before if k in after and before[k] != after[k]}
    assert changed == set(), f"既有文件不得被改动: {sorted(changed)}"

    dest = Path(result["cc_json_path"])
    assert dest.read_bytes() == (runtime / "cache" / "work" / "cc.json").read_bytes(), \
        "目标库原件必须与 merge 产物逐字节一致"


# ---------------------------------------------------------------------------
# TC-02-06: digest 口径 (m25 D013/D016)
# ---------------------------------------------------------------------------


def test_tc_02_06_digest_gate_pure_function_and_wiring(monkeypatch, tmp_path):
    """RepoDigests 含单架构 digest 通过; 只含多架构 digest 阻断并返回
    image_digest_mismatch; 两者都含通过且多架构值只进 cache.json."""
    single = f"docker.io/codecharta/codecharta-analysis@{cmc.IMAGE_SINGLE_ARCH_DIGEST}"
    multi = f"docker.io/codecharta/codecharta-analysis@{cmc.IMAGE_MULTI_ARCH_DIGEST}"
    assert cma.check_image_digests([single, multi]) == (True, True)
    assert cma.check_image_digests([multi]) == (False, True)
    assert cma.check_image_digests([single]) == (True, False)
    assert cma.check_image_digests([]) == (False, False)

    # 接线: stub 只报多架构 digest -> 阻断, 不写目标库, 不进分析
    target = make_target(tmp_path, name="digest-lib")
    result, runtime, state = build_with_stub(
        monkeypatch, tmp_path, target, repo_digests=[multi])
    assert result["success"] is False
    assert result["error"]["code"] == "image_digest_mismatch"
    assert cmc.IMAGE_SINGLE_ARCH_DIGEST in result["error"]["message"]
    assert not (Path(target) / ".codebase-map").exists(), "digest 阻断时不得写目标库"
    assert stub_run_argv(state) == [], "digest 阻断时不得进分析三步"

    # 两者都含时通过且多架构值只进 cache.json (build 输出不携带, 不阻断)
    frontend_sha = preset_frontend_cache(tmp_path / "codemap-rt")
    result2, runtime2, state2 = build_with_stub(
        monkeypatch, tmp_path, target, frontend_sha=frontend_sha)
    assert result2["success"] is True
    cache = json.loads((runtime2 / "cache" / "cache.json").read_text(encoding="utf-8"))
    assert cache["image"]["multi_arch_digest"] == cmc.IMAGE_MULTI_ARCH_DIGEST
    flat = json.dumps(result2, ensure_ascii=False)
    assert cmc.IMAGE_MULTI_ARCH_DIGEST not in flat, "多架构 digest 只记录进 cache.json, 不进输出"


# ---------------------------------------------------------------------------
# TC-02-07: 预置伪前端产物 sha256 与常量不符 -> frontend_hash_mismatch 且停下
# ---------------------------------------------------------------------------


def test_tc_02_07_frontend_hash_mismatch_stops(monkeypatch, tmp_path):
    """伪 web.zip 的 sha256 与常量不符 (不打补丁, 真常量自然失配): 阻断,
    不写目标库, 不把旧产物复制进 serve-root, 不进分析三步."""
    target = make_java_target(tmp_path, name="hash-lib")
    fake_zip = b"attacker supplied pseudo web.zip"
    assert pseudo_sha(fake_zip) != cmc.FRONTEND_ZIP_SHA256, "伪产物哈希必须与常量不同"
    runtime = tmp_path / "codemap-rt"
    frontend_dir = runtime / "cache" / "frontend" / cmc.FRONTEND_VERSION
    frontend_dir.mkdir(parents=True)
    (frontend_dir / "web.zip").write_bytes(fake_zip)  # 只预置伪 zip, 不预置其它

    result, runtime_resolved, state = build_with_stub(
        monkeypatch, tmp_path, target, frontend_sha=None)  # 期望值保持真常量
    assert result["success"] is False
    assert result["error"]["code"] == "frontend_hash_mismatch"
    assert not (Path(target) / ".codebase-map").exists(), "校验不过不得写目标库"
    serve_root = runtime_resolved / "serve-root"
    assert not (serve_root / "index.html").exists(), "不得把旧产物复制进 serve-root"
    assert list(serve_root.iterdir()) == [] if serve_root.is_dir() else True
    assert stub_run_argv(state) == [], "校验不过不得进分析三步"


# ---------------------------------------------------------------------------
# TC-02-08: 版本升级整体替换 serve-root, 不叠加旧产物
# ---------------------------------------------------------------------------


def test_tc_02_08_version_upgrade_replaces_serve_root_wholesale(monkeypatch, tmp_path):
    """cache.json 记录旧版本 (vis-2.8.0 残留) -> 重新解包并整体同步 serve-root:
    旧版专属文件消失, 新版文件就位, 其它库的数据副本 (*.cc.json) 保留."""
    target = make_target(tmp_path, name="upgrade-lib")
    runtime = tmp_path / "codemap-rt"
    new_zip = make_real_zip_bytes({
        "index.html": b"<html>vis-2.9.1 new</html>",
        "app.js": b"// v2",
        "v2-only.js": b"// only in v2",
    })
    frontend_sha = preset_frontend_cache(
        runtime,
        zip_bytes=new_zip,
        unpacked_entries={"index.html": b"<html>v1 junk</html>", "v1-only-unpacked.js": b"v1"},
        frontend_version="vis-2.8.0",  # 伪造旧版本残留
        populate_serve_root=False,
    )
    serve_root = runtime / "serve-root"
    serve_root.mkdir(parents=True)
    (serve_root / "index.html").write_bytes(b"<html>v1 old</html>")
    (serve_root / "v1-only.js").write_bytes(b"// only in v1")
    (serve_root / "other-lib-abcdef01.cc.json").write_text("{}", encoding="utf-8")  # 别库数据副本

    result, runtime_resolved, state = build_with_stub(
        monkeypatch, tmp_path, target, frontend_sha=frontend_sha)
    assert result["success"] is True
    init = result["initialization"]
    assert init["performed"] is True
    assert any("解包" in step for step in init["steps"])
    assert any("同步" in step and "serve-root" in step for step in init["steps"])
    assert "notice" in init

    # 整体替换: 新版就位, 旧版专属文件消失, 不叠加
    assert (serve_root / "index.html").read_bytes() == b"<html>vis-2.9.1 new</html>"
    assert (serve_root / "v2-only.js").read_bytes() == b"// only in v2"
    assert not (serve_root / "v1-only.js").exists(), "旧版本文件必须被整体替换掉, 不叠加"
    assert (serve_root / "other-lib-abcdef01.cc.json").exists(), "别库数据副本不得被同步删除"
    # 解包目录也整体重做: 旧解包垃圾消失
    unpacked = runtime_resolved / "cache" / "frontend" / cmc.FRONTEND_VERSION / "unpacked"
    assert not (unpacked / "v1-only-unpacked.js").exists()


# ---------------------------------------------------------------------------
# TC-02-09: 本地无镜像时 pull, performed=true 且 notice 说明慢操作
# ---------------------------------------------------------------------------


def test_tc_02_09_missing_image_pulls_and_notice_documents_slow_init(monkeypatch, tmp_path):
    """stub 场景: 首次 inspect 失败 -> podman pull -> 复检通过; performed=true,
    notice 存在且说明拉镜像与取官方前端属首次初始化的慢操作; steps 记录 pull.

    注意: pull 与前端下载的"真实网络"部分容器内不可造替身, 真实首次初始化
    证据归 ISSUE-07; 本用例只覆盖流程接线与固定字段.
    """
    target = make_target(tmp_path, name="pull-lib")
    frontend_sha = preset_frontend_cache(tmp_path / "codemap-rt")  # 前端齐备, 只缺镜像
    result, runtime, state = build_with_stub(
        monkeypatch, tmp_path, target, image_present=False, frontend_sha=frontend_sha)
    assert_full_build_fields(result, target)

    init = result["initialization"]
    assert init["performed"] is True
    assert len(init["steps"]) == 1 and "podman pull" in init["steps"][0]
    assert "慢操作" in init["notice"], "notice 必须说明首次初始化是慢操作"
    assert "拉" in init["notice"] and "前端" in init["notice"]
    assert any(entry["argv"][:1] == ["pull"] for entry in stub_calls(state))
    assert len(stub_run_argv(state)) == 3, "pull 之后照常进三步分析"
    assert (Path(result["cc_json_path"])).is_file()
