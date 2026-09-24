"""mailbox 无感自组网测试 (ISSUE-10, AC-031..AC-035/AC-037/BR-009).

TS-001 test_beacon_auto_neighbor (AC-031): 双实例互信标 → 舰队密钥 hello
互证 → 自动互建邻居可互投互取.
TS-002 test_hello_rejects_without_fleet_key (AC-032): 无/错舰队密钥握手被拒,
邻居表不变.
TS-003 test_signed_address_update (AC-033): 旧链路密钥签名的换址宣告被接受,
邻居地址更新, 投递恢复.
TS-004 test_forged_address_update_rejected_and_logged (AC-034/AC-037):
伪造换址宣告被拒且打 UTC 日志行.
TS-005 test_join_fleet_pulls_key_over_ssh (AC-035): join-fleet 经 ssh 拉取
舰队密钥, 本地 fleet.key 就位 0600.
TS-006 test_fleet_key_0600_ssh_only (BR-009): fleet.key 落盘 0600,
join-fleet 仅经 ssh 传输, 信标载荷不带密钥材料.

接缝: 信标 socket 注入 (回环 UDP 单播, 测试注入 env MAILBOX_BEACON_*/不改
生产语义) + hello/换址宣告 HTTP + 假 ssh 适配器 + 临时 fleet.key + 源码扫描.
握手/换址签名公式 spec 未逐字钉死, 本文件按独立实现的协议契约计算 (conftest
先例: 期望值不从实现抄). 共享接缝层在 tests/conftest.py;
双实例互联先例 test_mailbox_mesh.py; 时间窗 ±5min 沿用协议常量.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from conftest import (ADMIN_TOKEN, Serve, free_port, http_json,
                      make_letter, poll, post_letter, register_session)

# 协议契约 (与 mailbox.py 实现同式的独立重写): hello 证明 = HMAC-SHA256(
# fleet_key, "mailbox-hello" \n 发起方指纹 \n str(ts)); 指纹 = sha256(
# hostname\naddress) (与身份字段绑定, 评审修复 1); 换址宣告签名 =
# HMAC-SHA256(旧链路密钥, "mailbox-address-update" \n hostname \n 新地址 \n str(ts))
HELLO_PROOF_LABEL = "mailbox-hello"
ADDR_UPDATE_LABEL = "mailbox-address-update"
FLEET_KEY_VALUE = "test-fleet-key-1"  # fleet_key_file fixture 同源常量


def _sign(key, *parts):
    return hmac.new(key.encode(), "\n".join(parts).encode(),
                    hashlib.sha256).hexdigest()


def _fingerprint(hostname, address):
    return hashlib.sha256(f"{hostname}\n{address}".encode()).hexdigest()


@pytest.fixture
def fleet_key_file(tmp_path):
    """临时舰队密钥 (隔离真机 ~/.agents/mailbox/fleet.key)."""
    path = tmp_path / "fleet.key"
    path.write_text(FLEET_KEY_VALUE + "\n")
    return path


@pytest.fixture
def mesh_auto_serves(tmp_path):
    """双实例自组网拓扑: 信标回环单播互指 (注入 env, 不开真广播)."""
    created = []

    def _serve(name, fleet_path=None, beacon_port=None, beacon_dest=None,
               advertise_port=None, port=None, retry="0.2", interval="0.2"):
        workdir = tmp_path / name
        workdir.mkdir(parents=True, exist_ok=True)
        # 信标口与目的全部回环注入: 杜绝任何真 UDP 广播 (真机操作禁止)
        env = {"MAILBOX_NEIGHBORS": str(workdir / "neighbors.json"),
               "MAILBOX_RETRY_SECONDS": retry,
               "MAILBOX_BEACON_INTERVAL": interval,
               "MAILBOX_BEACON_PORT": str(beacon_port or free_port()),
               "MAILBOX_BEACON_DEST": beacon_dest
               or f"127.0.0.1:{free_port()}"}  # 缺省死端回环
        if fleet_path is not None:
            env["MAILBOX_FLEET_KEY"] = str(fleet_path)
        if beacon_port is not None:
            env["MAILBOX_BEACON_PORT"] = str(beacon_port)
        if beacon_dest is not None:
            env["MAILBOX_BEACON_DEST"] = beacon_dest
        if advertise_port is not None:
            env["MAILBOX_ADVERTISE_ADDR"] = f"127.0.0.1:{advertise_port}"
        srv = Serve(workdir, port=port, extra_env=env)
        created.append(srv)
        return srv

    yield _serve
    for srv in created:
        srv.stop()


def wait_for_neighbor(srv, address, deadline=15.0):
    """轮询 admin 邻居表直到出现指定地址的邻居; 超时返回 None."""
    end = time.time() + deadline
    while time.time() < end:
        code, resp = http_json("GET", srv.admin_port, "/admin/neighbors",
                               headers={"X-Admin-Token": ADMIN_TOKEN})
        assert code == 200, resp
        if any(n["address"] == address for n in resp["neighbors"]):
            return resp["neighbors"]
        time.sleep(0.2)
    return None


def poll_body(srv, session_id, signing_key, body, timeout=10):
    """循环 poll 直到取到 body 命中的信 (跳过回执信), 超时 None."""
    end = time.time() + timeout
    while time.time() < end:
        code, resp = poll(srv, session_id, signing_key)
        assert code == 200
        letter = resp["payload"]["letter"]
        if letter is not None and letter["body"] == body:
            return letter
    return None


def test_beacon_auto_neighbor(fleet_key_file, mesh_auto_serves):
    """TS-001/TC-051 (AC-031): 同网段两台已入群设备各自 serve, 信标互达后
    自动互建邻居并可互投互取, 全程无人工邻居配置."""
    http_a, http_b = free_port(), free_port()
    beacon_a, beacon_b = free_port(), free_port()
    srv_a = mesh_auto_serves("a", fleet_path=fleet_key_file,
                             beacon_port=beacon_a,
                             beacon_dest=f"127.0.0.1:{beacon_b}",
                             advertise_port=http_a, port=http_a)
    srv_b = mesh_auto_serves("b", fleet_path=fleet_key_file,
                             beacon_port=beacon_b,
                             beacon_dest=f"127.0.0.1:{beacon_a}",
                             advertise_port=http_b, port=http_b)
    assert srv_a.port == http_a and srv_b.port == http_b, \
        "预设端口被抢, 测试环境不干净"

    neighbors_a = wait_for_neighbor(srv_a, f"127.0.0.1:{http_b}")
    neighbors_b = wait_for_neighbor(srv_b, f"127.0.0.1:{http_a}")
    assert neighbors_a is not None, "A 未经信标自动发现 B"
    assert neighbors_b is not None, "B 未经信标自动发现 A"
    assert all(n["name"] for n in neighbors_a + neighbors_b), \
        "自动建的邻居应带 name (hostname, 同名 upsert 依据)"

    creds_a = register_session(srv_a, "a-host")
    creds_b = register_session(srv_b, "b-dev")
    code, _ = post_letter(srv_a, "a-host", creds_a["signing_key"],
                          make_letter(letter_id="A-1", to="b-dev",
                                      body="自组网互投", from_="a-host"))
    assert code == 200
    letter = poll_body(srv_b, "b-dev", creds_b["signing_key"], "自组网互投")
    assert letter is not None, "自动建邻居后 A→B 投递未通"

    code, _ = post_letter(srv_b, "b-dev", creds_b["signing_key"],
                          make_letter(letter_id="B-1", to="a-host",
                                      body="反向互投", from_="b-dev"))
    assert code == 200
    letter = poll_body(srv_a, "a-host", creds_a["signing_key"], "反向互投")
    assert letter is not None, "自动建邻居后 B→A 投递未通"


def test_hello_rejects_without_fleet_key(fleet_key_file, mesh_auto_serves,
                                          tmp_path):
    """TS-002/TC-052 (AC-032): 错舰队密钥的握手被拒 (无法证明持有
    fleet key), 不进邻居表; 无舰队密钥的设备发起/应答握手一律被拒且不发
    信标 (零确认入群 NG-009 不做)."""
    member = mesh_auto_serves("member", fleet_path=fleet_key_file)
    rogue_addr = f"127.0.0.1:{free_port()}"
    fp = _fingerprint("rogue", rogue_addr)  # 指纹与身份绑定, 逼走证明校验分支
    ts = time.time()
    wrong_proof = _sign("not-the-fleet-key", HELLO_PROOF_LABEL, fp, str(ts))
    code, resp = http_json("POST", member.port, "/mailbox/hello",
                           {"fingerprint": fp, "hostname": "rogue",
                            "address": rogue_addr,
                            "ts": ts, "proof": wrong_proof})
    assert code == 403, resp
    assert "舰队密钥" in resp.get("error", ""), resp
    code, resp = http_json("GET", member.admin_port, "/admin/neighbors",
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200 and resp["neighbors"] == [], \
        "被拒的握手不得进邻居表"

    # 无舰队密钥的设备: 纵有正确证明材料也拒 (本机无密钥无法验), 且不发信标
    import socket as _socket
    ear = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
    ear.bind(("127.0.0.1", 0))
    ear.settimeout(1.5)
    keyless = mesh_auto_serves(
        "keyless", fleet_path=tmp_path / "absent-fleet.key",
        beacon_dest=f"127.0.0.1:{ear.getsockname()[1]}", interval="0.1")
    ts2 = time.time()
    fp2 = _fingerprint("outsider", f"127.0.0.1:{free_port()}")
    right_proof = _sign(FLEET_KEY_VALUE, HELLO_PROOF_LABEL, fp2, str(ts2))
    code, resp = http_json("POST", keyless.port, "/mailbox/hello",
                           {"fingerprint": fp2, "hostname": "outsider",
                            "address": f"127.0.0.1:{free_port()}",
                            "ts": ts2, "proof": right_proof})
    assert code == 403, resp
    assert "舰队密钥" in resp.get("error", ""), resp
    beacon_heard = True
    try:
        ear.recvfrom(65535)
    except _socket.timeout:
        beacon_heard = False
    finally:
        ear.close()
    assert not beacon_heard, "无舰队密钥的设备不应发信标参与组网"


def test_hello_fingerprint_bound_to_identity(fleet_key_file,
                                              mesh_auto_serves):
    """评审修复 1 (安全从严): hello 指纹必须与 (hostname, address) 绑定
    (fp = sha256(hostname\naddress)) — 持舰队密钥者不得冒任意身份发起
    hello 借同名 upsert 覆盖受害邻居条目 (投递劫持); 合法 hello 不受影响."""
    import re
    import select
    member = mesh_auto_serves("member2", fleet_path=fleet_key_file)
    hostname = "victim-host"
    address = f"127.0.0.1:{free_port()}"
    ts = time.time()

    # 冒名 hello: proof 用正确舰队密钥按公式签, 但指纹与身份字段不绑定
    fake_fp = "ab" * 32
    proof = _sign(FLEET_KEY_VALUE, HELLO_PROOF_LABEL, fake_fp, str(ts))
    code, resp = http_json("POST", member.port, "/mailbox/hello",
                           {"fingerprint": fake_fp, "hostname": hostname,
                            "address": address, "ts": ts, "proof": proof})
    assert code == 403, resp
    assert "不绑定" in resp.get("error", ""), resp
    code, resp = http_json("GET", member.admin_port, "/admin/neighbors",
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200 and resp["neighbors"] == [], \
        "冒名 hello 不得进邻居表"
    utc_ts = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z")
    hit = ""
    deadline = time.time() + 10
    while time.time() < deadline and not hit:
        ready, _, _ = select.select([member.proc.stderr], [], [], 1.0)
        if not ready:
            continue
        line = member.proc.stderr.readline()
        if "hello-rejected" in line and "fingerprint-mismatch" in line:
            hit = line
    assert hit, "冒名 hello 拒绝应打 UTC 日志行"
    assert utc_ts.search(hit), f"日志行须带 UTC 时间戳: {hit!r}"

    # 合法 hello (指纹按公式与身份绑定) 不受影响: 200 + 建邻居
    good_fp = _fingerprint(hostname, address)
    ts2 = time.time()
    proof2 = _sign(FLEET_KEY_VALUE, HELLO_PROOF_LABEL, good_fp, str(ts2))
    code, resp = http_json("POST", member.port, "/mailbox/hello",
                           {"fingerprint": good_fp, "hostname": hostname,
                            "address": address, "ts": ts2, "proof": proof2})
    assert code == 200, resp
    code, resp = http_json("GET", member.admin_port, "/admin/neighbors",
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    entry = next((n for n in resp["neighbors"]
                  if n["name"] == hostname), None)
    assert entry is not None and entry["address"] == address, \
        "合法 hello 应正常建邻居"


def test_signed_address_update(mesh_auto_serves, tmp_path):
    """TS-003/TC-053 (AC-033): 邻居 c-host 换址后用旧链路密钥签名宣告新
   地址, b 验签通过即更新邻居地址, 滞留信自动重投 (投递恢复), 新信直达."""
    srv_b = mesh_auto_serves("b")
    dead_port = free_port()
    code, resp = http_json("POST", srv_b.admin_port, "/admin/neighbors",
                           {"address": f"127.0.0.1:{dead_port}",
                            "shared_key": "k-link", "name": "c-host"},
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200, resp

    # 换址后的 c: 新地址起真实 serve, 与 b 互持旧链路密钥 k-link
    http_c = free_port()
    workdir_c = tmp_path / "c"
    workdir_c.mkdir(parents=True, exist_ok=True)
    (workdir_c / "neighbors.json").write_text(json.dumps(
        [{"address": f"127.0.0.1:{srv_b.port}",
          "shared_key": "k-link", "name": "b-host"}]))
    srv_c = mesh_auto_serves("c", port=http_c)
    assert srv_c.port == http_c, "预设端口被抢, 测试环境不干净"
    creds_b = register_session(srv_b, "b-host")
    creds_c = register_session(srv_c, "c-dev")

    # 换址前: 投信滞留 (旧地址死口)
    code, resp = post_letter(srv_b, "b-host", creds_b["signing_key"],
                             make_letter(letter_id="H-0", to="c-dev",
                                         body="换址前的滞留信",
                                         from_="b-host"))
    assert code == 200 and resp["payload"]["route"] == "staged_pending"

    # 旧链路密钥签名的换址宣告 (±5min 窗内时间戳)
    new_address = f"127.0.0.1:{http_c}"
    ts = time.time()
    sig = _sign("k-link", ADDR_UPDATE_LABEL, "c-host", new_address, str(ts))
    code, resp = http_json("POST", srv_b.port, "/mailbox/address-update",
                           {"hostname": "c-host", "new_address": new_address,
                            "ts": ts, "sig": sig})
    assert code == 200, resp

    # 邻居表已更新到新地址
    code, resp = http_json("GET", srv_b.admin_port, "/admin/neighbors",
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200
    entry = next(n for n in resp["neighbors"] if n["name"] == "c-host")
    assert entry["address"] == new_address, "换址宣告后邻居地址未更新"

    # 投递恢复: 滞留信自动重投到新地址 + 新信直达
    letter = poll_body(srv_c, "c-dev", creds_c["signing_key"],
                       "换址前的滞留信", timeout=15)
    assert letter is not None, "换址后滞留信未恢复投递"
    code, resp = post_letter(srv_b, "b-host", creds_b["signing_key"],
                             make_letter(letter_id="H-1", to="c-dev",
                                         body="换址后的新信", from_="b-host"))
    assert code == 200 and resp["payload"]["route"] == "forwarded"
    letter = poll_body(srv_c, "c-dev", creds_c["signing_key"], "换址后的新信")
    assert letter is not None, "换址后新信未直达"


def test_forged_address_update_rejected_and_logged(mesh_auto_serves):
    """TS-004/TC-054 (AC-034/AC-037 邻居换址行): 签名无效的换址宣告被拒
    (不更新地址) 且 serve 打带 UTC 时间戳的拒绝日志行."""
    import re
    import select
    srv_b = mesh_auto_serves("b")
    dead_port, forged_port = free_port(), free_port()
    old_address = f"127.0.0.1:{dead_port}"
    code, resp = http_json("POST", srv_b.admin_port, "/admin/neighbors",
                           {"address": old_address,
                            "shared_key": "k-link", "name": "c-host"},
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200, resp

    # 伪造宣告: 签名用错误密钥计算
    new_address = f"127.0.0.1:{forged_port}"
    ts = time.time()
    forged = _sign("wrong-link-key", ADDR_UPDATE_LABEL, "c-host",
                   new_address, str(ts))
    code, resp = http_json("POST", srv_b.port, "/mailbox/address-update",
                           {"hostname": "c-host", "new_address": new_address,
                            "ts": ts, "sig": forged})
    assert code == 403, resp
    assert "签名无效" in resp.get("error", ""), resp

    # 邻居地址不变 (伪造被拒, 不更新)
    code, resp = http_json("GET", srv_b.admin_port, "/admin/neighbors",
                           headers={"X-Admin-Token": ADMIN_TOKEN})
    assert code == 200
    entry = next(n for n in resp["neighbors"] if n["name"] == "c-host")
    assert entry["address"] == old_address, "伪造宣告不应更新邻居地址"

    # UTC 日志行 (AC-037 换址行): [UTC 时间戳] address-update-rejected ...
    utc_ts = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z")
    hit = ""
    deadline = time.time() + 10
    while time.time() < deadline and not hit:
        ready, _, _ = select.select([srv_b.proc.stderr], [], [], 1.0)
        if not ready:
            continue
        line = srv_b.proc.stderr.readline()
        if "address-update-rejected" in line:
            hit = line
    assert hit, "拒绝换址宣告应打关键事件日志行"
    assert utc_ts.search(hit), f"日志行须带 UTC 时间戳: {hit!r}"
    assert "c-host" in hit, f"日志行应含邻居名: {hit!r}"


def test_join_fleet_pulls_key_over_ssh(tmp_path):
    """TS-005/TC-055 (AC-035): join-fleet 经 ssh 从老设备拉取舰队密钥,
    本地 fleet.key 就位 0600 — 新设备入群唯一人工动作."""
    import os
    import stat
    import subprocess
    import sys
    from conftest import SCRIPT
    home = tmp_path / "home"  # 临时 HOME: 隔离真机 ~/.agents/mailbox
    bindir = tmp_path / "bin"
    bindir.mkdir()
    args_file = tmp_path / "ssh-args.txt"
    ssh = bindir / "ssh"  # 假 ssh 适配器: 记录参数, 吐罐头密钥
    ssh.write_text(
        f"#!/bin/sh\necho \"$@\" > {args_file}\n"
        "echo fake-fleet-key-0123456789abcdef\n")
    ssh.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k != "MAILBOX_FLEET_KEY"}
    env["HOME"] = str(home)
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "join-fleet", "oldbox.local"],
        env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    key_path = home / ".agents" / "mailbox" / "fleet.key"
    assert key_path.exists(), "join-fleet 后本地 fleet.key 未就位"
    assert key_path.read_text().strip() == "fake-fleet-key-0123456789abcdef"
    assert stat.S_IMODE(key_path.stat().st_mode) == 0o600, \
        "fleet.key 落盘须 0600 (BR-009)"
    assert args_file.read_text().strip() == \
        "oldbox.local cat ~/.agents/mailbox/fleet.key", \
        "join-fleet 应主动 ssh 到老设备拉取密钥"


def test_fleet_key_0600_ssh_only(fleet_key_file, mesh_auto_serves, tmp_path):
    """TS-006/TC-056 (BR-009 审计): fleet.key 落盘 0600; join-fleet 实现
    仅经 ssh 传输 (源码扫描); 信标载荷只含 address/hostname/fingerprint,
    密钥材料不上 wire."""
    import ast
    import socket as _socket
    import stat
    import subprocess
    import sys
    from conftest import SCRIPT

    # 信标载荷字段集 = {address, hostname, fingerprint}, 不含舰队密钥
    ear = _socket.socket(_socket.AF_INET, _socket.SOCK_DGRAM)
    ear.bind(("127.0.0.1", 0))
    ear.settimeout(10)
    srv = mesh_auto_serves("audit", fleet_path=fleet_key_file,
                           beacon_dest=f"127.0.0.1:{ear.getsockname()[1]}",
                           interval="0.2")
    data, _ = ear.recvfrom(65535)
    ear.close()
    payload = json.loads(data)
    assert set(payload) == {"address", "hostname", "fingerprint"}, payload
    assert payload["address"] and payload["hostname"] \
        and payload["fingerprint"]
    assert fleet_key_file.read_text().strip() not in data.decode(), \
        "舰队密钥材料不得出现在信标 wire 上"

    # join-fleet 仅经 ssh: AST 定位 cmd_join_fleet, 传输通道唯一 = ssh
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "cmd_join_fleet")
    src = ast.unparse(fn)
    assert "ssh" in src and "subprocess" in src, \
        "join-fleet 应经 subprocess ssh 拉取"
    assert "cat" in src and "fleet.key" in src, \
        "join-fleet 的 ssh 远端命令应 cat 老设备 fleet.key"
    for banned in ("urllib", "http://", "https://", "ftp://",
                   "scp", "curl", "wget"):
        assert banned not in src, f"join-fleet 传输通道应仅 ssh: 发现 {banned}"

    # 0600 落盘 (BR-009): 假 ssh 适配器真跑一次 join-fleet
    import os
    home = tmp_path / "home6"
    bindir = tmp_path / "bin6"
    bindir.mkdir()
    ssh = bindir / "ssh"
    ssh.write_text("#!/bin/sh\necho audit-fleet-key\n")
    ssh.chmod(0o755)
    env = {k: v for k, v in os.environ.items() if k != "MAILBOX_FLEET_KEY"}
    env["HOME"] = str(home)
    env["PATH"] = f"{bindir}:{env.get('PATH', '')}"
    result = subprocess.run([sys.executable, str(SCRIPT), "join-fleet",
                             "auditbox"], env=env, capture_output=True,
                            text=True, timeout=30)
    assert result.returncode == 0, result.stderr
    key_path = home / ".agents" / "mailbox" / "fleet.key"
    assert stat.S_IMODE(key_path.stat().st_mode) == 0o600
