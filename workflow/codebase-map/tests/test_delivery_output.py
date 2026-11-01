"""ISSUE-05 交付输出与地址解析用例: AC-008 三场景, keys 交集, delivery_notes,
交付一致性.

覆盖: TC-008 (AC-008 主用例), TC-05-01 (缺地址阻塞), TC-05-02 (确认后
--address 重新交付), TC-05-03 (keys 交集口径), TC-05-04 (delivery_notes
与换端口报告), TC-05-05 (交付一致性).

隔离纪律: 地址来源 ~/.agents/sandbox-worktree/lan-address 用临时 HOME 替换
(不新增配置源, m14 D011; EXECUTION 文件接缝口径), 运行时目录 CODEMAP_RUNTIME_DIR
指向 tmp_path, 端口 free_port 高位临时端口, 不占 8090; 收尾 stop 加强杀,
不残留进程. 测试地址一律用 RFC 5737 TEST-NET-3 文档地址 (203.0.113.0/24),
不落真实局域网地址 (m25 D010).

BR-027 (serve/stop 不做网络动作) 按任务书走人工核验, 不写自动化用例.
"""
from __future__ import annotations

import ipaddress
import json

import pytest

from codemap_service_helpers import (
    CONFIRMED_ADDR,
    CodemapSrv,
    free_port,
    http_status,
    use_temp_home,
)

ARG_ADDR = "203.0.113.88"

KEY_DEMO = "demo-lib-ab12cd34.cc.json"


@pytest.fixture
def srv(tmp_path):
    controller = CodemapSrv(tmp_path)
    yield controller
    controller.cleanup()


# (use_temp_home 已上移 codemap_service_helpers, 各用例直接导入使用)


def write_cc_copy(serve_root, key, file_count):
    """写一份带指定 File 节点数的伪 cc.json 副本 (供 denominator_note 计数)."""
    payload = {
        "files": [{
            "id": "root", "name": "root", "type": "Directory",
            "children": [
                {"id": f"f{i}", "name": f"F{i}.java", "type": "File"}
                for i in range(file_count)
            ],
        }],
    }
    (serve_root / key).write_text(json.dumps(payload), encoding="utf-8")


def register_keys(srv, *keys):
    """把 serve-root 里已有副本的键登记进 state.json 的 data_keys."""
    srv.write_state(data_keys=[
        {"key": key, "source_cc_json": f"/fake/.codebase-map/{key}",
         "built_at": "2026-01-01T00:00:00+00:00", "bytes": 64}
        for key in keys
    ])


def assert_lan_url(url, addr, port, suffix="/"):
    """URL 形状 (AC-002/BR-019): 局域网地址 + 实际端口, 无回环/主机名/路径."""
    assert url == f"http://{addr}:{port}{suffix}"
    assert "127.0.0.1" not in url and "localhost" not in url and "::1" not in url


def test_tc008_confirmed_address_delivers_lan_urls(srv, tmp_path):
    """TC-008 (AC-008 主用例): 临时 HOME 里有已确认地址 + 两份数据副本时,
    serve 输出的 base_url 与每个 keys[].url 用该地址加实际端口拼成,
    ?file=<键> 形状正确, 交付 URL 里没有回环地址/主机名/文件路径."""
    use_temp_home(srv, tmp_path, confirmed=CONFIRMED_ADDR)
    key_other = "other-lib-ef12ab34.cc.json"
    srv.prime(key=KEY_DEMO)
    write_cc_copy(srv.serve_root, KEY_DEMO, 4)
    write_cc_copy(srv.serve_root, key_other, 7)
    register_keys(srv, KEY_DEMO, key_other)

    obj, _ = srv.serve()
    assert obj["success"] is True
    assert obj["address_source"] == "confirmed_record"
    assert_lan_url(obj["url"], CONFIRMED_ADDR, srv.port)
    assert_lan_url(obj["base_url"], CONFIRMED_ADDR, srv.port)
    assert obj["url"] == obj["base_url"]
    by_key = {item["key"]: item for item in obj["keys"]}
    assert set(by_key) == {KEY_DEMO, key_other}
    assert_lan_url(
        by_key[KEY_DEMO]["url"], CONFIRMED_ADDR, srv.port, f"/?file={KEY_DEMO}")
    assert_lan_url(
        by_key[key_other]["url"], CONFIRMED_ADDR, srv.port, f"/?file={key_other}")
    # keys 每项带 built_at/bytes (地址解析成功形态)
    assert by_key[KEY_DEMO]["built_at"] == "2026-01-01T00:00:00+00:00"
    assert by_key[KEY_DEMO]["bytes"] == 64
    # 交付 URL 群里不出现回环地址/主机名/文件路径 (serve_root 是诊断字段, 不算交付 URL)
    delivery_blob = json.dumps(
        {"url": obj["url"], "base_url": obj["base_url"], "keys": obj["keys"]},
        ensure_ascii=False)
    for banned in ("127.0.0.1", "localhost", "::1", str(srv.serve_root), ".cc.json/"):
        assert banned not in delivery_blob, f"交付 URL 群不应含 {banned}: {delivery_blob}"
    # 交付说明三类齐全 (AC-006 交付侧)
    notes = obj["delivery_notes"]
    assert notes["level_hint"] and notes["integrity_note"] and notes["denominator_note"]


def test_tc_05_01_no_address_blocks_delivery_but_starts_service(srv, tmp_path):
    """TC-05-01 (AC-008 缺地址): 临时 HOME 里没有 lan-address 且不传 --address,
    退出码 0, 服务已起 (GET / 200), 无 url/base_url, keys 每项只有 key,
    address_missing.code == no_confirmed_address, candidates 非空且全为 IPv4
    字面量, 人类可读模式首行含 BLOCKED."""
    use_temp_home(srv, tmp_path, confirmed=None)
    srv.prime()
    write_cc_copy(srv.serve_root, KEY_DEMO, 2)

    obj, proc = srv.serve()
    assert proc.returncode == 0, f"缺地址时退出码必须为 0: {obj}"
    assert obj["success"] is True
    assert "url" not in obj and "base_url" not in obj
    assert "address_source" not in obj
    assert obj["address_missing"]["code"] == "no_confirmed_address"
    assert obj["address_missing"]["message"]
    candidates = obj["candidates"]
    assert candidates, "候选地址不应为空"
    for addr in candidates:
        parsed = ipaddress.ip_address(addr)
        assert parsed.version == 4, f"候选应全是 IPv4 字面量: {addr}"
        assert not parsed.is_loopback, f"候选不得含回环地址: {addr}"
    assert obj["keys"] == [{"key": KEY_DEMO}], "缺地址时 keys 每项只给键名"
    # 服务已起: 阻断的是交付不是启动
    status, _ = http_status(srv.port)
    assert status == 200, "缺地址时服务应照常监听"
    # 人类可读模式首行 BLOCKED
    human = srv.cli("serve", timeout=60)
    assert human.returncode == 0
    first_line = human.stdout.splitlines()[0]
    assert first_line.startswith("BLOCKED"), f"首行应含 BLOCKED: {first_line!r}"
    assert "缺已确认局域网地址" in first_line


def test_tc_05_02_explicit_address_redelivers_without_persisting(srv, tmp_path):
    """TC-05-02 (AC-008 确认后): 缺地址阻塞后, 用户确认候选地址, 重跑
    serve --address <已确认地址>: 输出带完整 URL 且 address_source 标明来自
    本次参数; 断言 state.json 里没有该地址, lan-address 文件未被创建, 且再跑
    不带 --address 的 serve 仍按记录判定为阻塞."""
    use_temp_home(srv, tmp_path, confirmed=None)
    srv.prime()
    write_cc_copy(srv.serve_root, KEY_DEMO, 2)
    blocked, _ = srv.serve()
    assert "url" not in blocked and blocked["address_missing"]["code"] == "no_confirmed_address"

    obj, proc = srv.serve("--address", ARG_ADDR)
    assert proc.returncode == 0
    assert obj["address_source"] == "explicit_argument"
    assert_lan_url(obj["url"], ARG_ADDR, srv.port)
    assert_lan_url(obj["base_url"], ARG_ADDR, srv.port)
    assert obj["keys"][0]["url"] == f"http://{ARG_ADDR}:{srv.port}/?file={KEY_DEMO}"
    # --address 只作用本次: 不写 state.json, 不回写/新建 swt 记录文件
    state_text = srv.state_path.read_text(encoding="utf-8")
    assert ARG_ADDR not in state_text, "--address 的值不得落进 state.json"
    lan_path = srv.home / ".agents" / "sandbox-worktree" / "lan-address"
    assert not lan_path.exists(), "不得新建或回写 lan-address 记录文件"
    # 下次 serve 仍按地址记录判定: 没有 --address 就仍阻塞
    again, _ = srv.serve()
    assert "url" not in again and "base_url" not in again
    assert again["address_missing"]["code"] == "no_confirmed_address"


def test_tc_05_03_keys_is_intersection_with_hints(srv, tmp_path):
    """TC-05-03: keys 交集口径: 记录与磁盘都有的键进 keys; 记录有磁盘缺的键
    不进 keys 且有提示; 磁盘有记录没有的 .cc.json 只提示存在未登记文件,
    不进 keys 且不改 state.json (不收编不删除)."""
    use_temp_home(srv, tmp_path, confirmed=CONFIRMED_ADDR)
    keep = "keep-lib-aa11bb22.cc.json"
    gone = "gone-lib-cc33dd44.cc.json"
    orphan = "orphan-lib-ee55ff66.cc.json"
    srv.prime(key=keep)
    register_keys(srv, keep, gone)
    write_cc_copy(srv.serve_root, keep, 3)
    (srv.serve_root / orphan).write_text('{"files": []}', encoding="utf-8")

    obj, _ = srv.serve()
    assert obj["success"] is True
    assert [item["key"] for item in obj["keys"]] == [keep], "keys 应只含清单与磁盘的交集"
    assert obj["keys"][0]["url"] == f"http://{CONFIRMED_ADDR}:{srv.port}/?file={keep}"
    notes_blob = json.dumps(obj.get("notes") or [], ensure_ascii=False)
    assert gone in notes_blob, "记录有磁盘缺的键应有缺失提示"
    assert orphan in notes_blob, "未登记副本应只提示存在"
    assert "不自动收编" in notes_blob
    # 不收编不删除: state.json 与磁盘原样
    state_after = srv.read_state()
    assert [e["key"] for e in state_after["data_keys"]] == [keep, gone]
    assert (srv.serve_root / orphan).is_file(), "未登记副本不得被删"


def test_tc_05_04_delivery_notes_and_port_change_report(srv, tmp_path):
    """TC-05-04: delivery_notes 三类说明齐全且 denominator_note 里的文件数等于
    最近一次 build 统计的依赖树文件数; 显式换端口时 port_changed == true,
    previous_url 取停机前留痕的交付 URL (不含回环) 且输出写明旧地址已失效,
    不带 --port 时两者不出现."""
    use_temp_home(srv, tmp_path, confirmed=CONFIRMED_ADDR)
    srv.prime()
    write_cc_copy(srv.serve_root, KEY_DEMO, 4)

    first, _ = srv.serve()
    notes = first["delivery_notes"]
    assert set(notes) == {"level_hint", "integrity_note", "denominator_note"}
    assert "依赖视图" in notes["level_hint"]
    assert "未量化" in notes["integrity_note"] and "不能当作分层完全可信" in notes["integrity_note"]
    assert "可信" not in notes["level_hint"], "层号说明不得宣称分层可信"
    assert f"{KEY_DEMO}: 4" in notes["denominator_note"], (
        f"分母文件数应等于副本依赖树文件数: {notes['denominator_note']}")
    assert "零声明文件不进依赖树" in notes["denominator_note"]
    assert "默认不扫" in notes["denominator_note"]
    assert "port_changed" not in first and "previous_url" not in first, (
        "不带 --port 的 serve 不得报换端口")
    assert srv.read_state()["last_url"] == first["url"], (
        "record 来源应把交付 URL 留痕进 last_url")

    # 显式换端口: port_changed + previous_url 取停机前留痕的交付 URL
    srv.stop()
    url_before_stop = srv.read_state()["last_url"]
    assert "127.0.0.1" not in url_before_stop and "localhost" not in url_before_stop
    new_port = free_port()
    changed, _ = srv.serve("--port", str(new_port))
    assert changed["port_changed"] is True
    assert changed["previous_url"] == url_before_stop, "旧地址应取状态留痕的交付 URL"
    assert "127.0.0.1" not in changed["previous_url"] and "localhost" not in changed["previous_url"]
    assert "旧地址已失效" in changed["note"], "换端口输出必须写明旧地址已失效"

    # 不带 --port 沿用 last_port: 两者不出现
    srv.stop()
    again, _ = srv.serve()
    assert "port_changed" not in again and "previous_url" not in again
    assert again["port"] == new_port


def test_port_change_reports_record_delivery_url_as_previous(srv, tmp_path):
    """C-1 (record 来源): last_url 留痕写成交付 URL; 换端口时 previous_url
    取该留痕, 不含 127.0.0.1/localhost (BR-019 不给回环地址), 输出写明旧地址
    已失效 (m25 D018 真实旧地址)."""
    use_temp_home(srv, tmp_path, confirmed=CONFIRMED_ADDR)
    srv.prime()
    first, _ = srv.serve()
    state = srv.read_state()
    assert state["last_url"] == first["url"], "record 来源应把交付 URL 留痕进 last_url"
    assert "127.0.0.1" not in state["last_url"] and "localhost" not in state["last_url"]

    srv.stop()
    new_port = free_port()
    changed, _ = srv.serve("--port", str(new_port))
    assert changed["port_changed"] is True
    previous = changed["previous_url"]
    assert previous == first["url"], "旧地址应取留痕的交付 URL, 不是回环地址"
    assert "127.0.0.1" not in previous and "localhost" not in previous
    assert "旧地址已失效" in changed["note"]


def test_tc_05_05_delivery_consistency_three_way_port_and_keys(srv, tmp_path):
    """TC-05-05 (交付一致性): url 端口 == state.json.port == 实际监听端口;
    keys[].key == serve_root 里实际文件名; keys[].url 的键与地址与 base_url
    同源; 键 URL 指向的副本经本机同路径真实可开 (?file= 命中)."""
    use_temp_home(srv, tmp_path, confirmed=CONFIRMED_ADDR)
    key_a = "alpha-lib-11aa22bb.cc.json"
    key_b = "beta-lib-33cc44dd.cc.json"
    srv.prime(key=key_a)
    write_cc_copy(srv.serve_root, key_a, 5)
    write_cc_copy(srv.serve_root, key_b, 6)
    register_keys(srv, key_a, key_b)

    obj, _ = srv.serve()
    state = srv.read_state()
    assert obj["port"] == state["port"] == srv.port, "输出端口与状态记录与实际端口三方一致"
    status, _ = http_status(srv.port)
    assert status == 200, "实际监听端口应可访问"
    disk_names = {
        p.name for p in srv.serve_root.iterdir() if p.name.endswith(".cc.json")}
    assert {item["key"] for item in obj["keys"]} == disk_names, "keys[].key 应等于实际文件名"
    for item in obj["keys"]:
        assert item["url"].startswith(obj["base_url"]), "keys[].url 应与 base_url 同址同源"
        assert item["url"] == f"http://{CONFIRMED_ADDR}:{srv.port}/?file={item['key']}"
        assert item["url"].split("?file=")[1] == item["key"], "URL 里的键应与 keys[].key 一致"
        # 同一文件经本机回环取同路径可开: 副本真实存在且可被 HTTP 面服务
        status, _ = http_status(srv.port, f"/?file={item['key']}")
        assert status == 200, f"键 {item['key']} 应能经 HTTP 取到"
