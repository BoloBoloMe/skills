"""pi 身份统一: 容器受限注册, 独立收发, 归属持久化与注销, 失败不退回共用身份.

HTTP/CLI 用真实隔离服务, 不需要 Podman, 不读取真实用户凭据.
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from conftest import ADMIN_TOKEN, SCRIPT, ack_letter, http_json, make_letter, poll, post_letter, register_session, sign


@pytest.fixture
def mailbox():
    spec = importlib.util.spec_from_file_location("mailbox_pi_identity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def child_request(creds, target, *, operation="ensure-session", key=None):
    ts = str(time.time())
    return {"session": creds["id"], "id": target, "sig_ts": ts,
            "sig": sign(key or creds["signing_key"], creds["id"], ts, operation, target)}


def ensure(srv, parent, target, **kwargs):
    return http_json("POST", srv.port, "/mailbox/sessions/ensure", child_request(parent, target, **kwargs))


def container_env(srv, parent, root):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("SWT_SESSION_", "MAILBOX_")) and k != "SWT_MAILBOX_URL"}
    env.update(HOME=str(root), MAILBOX_STATE=str(root / "absent-state.json"),
               SWT_MAILBOX_URL=f"http://127.0.0.1:{srv.port}", SWT_SESSION_ID=parent["id"],
               SWT_SESSION_SIGNING_KEY=parent["signing_key"], SWT_SESSION_RESPONSE_KEY=parent["response_key"])
    return env


def cli(env, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args], env=env,
                          capture_output=True, text=True, timeout=15)


def test_container_pi_configs_are_independent_and_cli_uses_pi_sender(serves, tmp_path):
    srv = serves()
    parent = register_session(srv, "swt-demo-deadbeef")
    peer = register_session(srv, "peer")
    env = container_env(srv, parent, tmp_path / "container")
    configs = {}
    for sid in ("pi-A", "pi-B"):
        result = cli(env, "ensure-session", sid)
        assert result.returncode == 0, result.stderr
        info = json.loads(result.stdout)
        assert info["id"] == sid and info["created"] is True
        cfg = Path(info["config"])
        creds = json.loads(cfg.read_text())
        configs[sid] = (cfg, creds)
        assert creds["session"] == sid
        assert stat.S_IMODE(cfg.stat().st_mode) == 0o600
        assert stat.S_IMODE(cfg.parent.stat().st_mode) == 0o700
        assert creds["signing_key"] not in result.stdout + result.stderr
        assert creds["response_key"] not in result.stdout + result.stderr
        assert parent["signing_key"] not in result.stdout + result.stderr
        # 重复启动复用凭据, 不改其他会话也不清队列.
        again = cli(env, "ensure-session", sid)
        assert again.returncode == 0, again.stderr
        assert json.loads(again.stdout)["created"] is False
        assert json.loads(cfg.read_text()) == creds
    assert configs["pi-A"][1]["signing_key"] != configs["pi-B"][1]["signing_key"]
    for sid, (cfg, creds) in configs.items():
        # bootstrap env 仍在, 显式 pi 配置必须优先, 发件人不能退回容器名.
        result = cli({**env, "MAILBOX_CONFIG": str(cfg)}, "send", "--force", "--to", "peer",
                     "--type", "notify", "--body", sid)
        assert result.returncode == 0, result.stderr
        for _ in range(5):
            code, reply = poll(srv, "peer", peer["signing_key"])
            assert code == 200
            received = reply["payload"]["letter"]
            if not received["from"].startswith("mailbox@"):
                break
            assert ack_letter(srv, "peer", peer["signing_key"], received["id"],
                              reply["payload"]["lease_token"])[0] == 200
        assert received["from"] == sid
        letter = make_letter(letter_id=f"to-{sid}", from_="peer", to=sid, body=sid)
        assert post_letter(srv, "peer", peer["signing_key"], letter)[0] == 200
        fetched = cli({**env, "MAILBOX_CONFIG": str(cfg)})
        assert fetched.returncode == 0, fetched.stderr
        assert f"to-{sid}" in fetched.stdout and sid in fetched.stdout
    assert poll(srv, "pi-A", configs["pi-B"][1]["signing_key"])[0] == 403
    result = cli({**env, "MAILBOX_CONFIG": str(tmp_path / "missing.json")},
                 "send", "--force", "--to", "peer", "--type", "notify", "--body", "不得偷用容器身份")
    assert result.returncode == 3


def test_real_extension_two_pi_sessions_and_new_resume(serves, tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("需支持 TypeScript type stripping 的 Node")
    version = subprocess.run([node, "--version"], capture_output=True, text=True, timeout=5).stdout
    major, minor = (int(part) for part in version.strip().lstrip("v").split(".")[:2])
    if major < 22 or major == 22 and minor < 18:
        pytest.skip("需 Node >=22.18")
    srv = serves()
    parent = register_session(srv, "real-container-deadbeef")
    env = container_env(srv, parent, tmp_path / "container")
    env.update(LISTEN_EXT=str(SCRIPT.parent.parent / "pi-extension" / "index.ts"),
               MAILBOX_PYTHON=sys.executable, SPAWN_LOG=str(tmp_path / "unused-spawn.log"))
    harness = Path(__file__).parent / "pi/mailbox/listen-smoke.mjs"
    result = subprocess.run([node, str(harness), "container-real-isolation"], env=env,
                            capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "真实服务: 两 pi 都收到自己的信" in result.stdout


def test_remote_registration_auth_binding_and_collision_isolation(serves):
    srv = serves()
    parent = register_session(srv, "container-A-deadbeef")
    other = register_session(srv, "container-B-deadbeef")
    host = register_session(srv, "host-pi")
    assert ensure(srv, parent, "pi-A", key="bad-key")[0] == 403
    assert ensure(srv, parent, "pi-A", operation="poll")[0] == 403
    body = child_request(parent, "pi-A")
    body["id"] = "pi-B"  # 签名绑定目标 id.
    assert http_json("POST", srv.port, "/mailbox/sessions/ensure", body)[0] == 403
    for sid in ("../escape", "mailbox@forged", "", "x" * 129):
        assert ensure(srv, parent, sid)[0] == 403
    code, response = ensure(srv, parent, "pi-A")
    assert code == 200
    child = response["payload"]
    assert child["id"] == "pi-A" and child["created"] is True
    assert sign(parent["response_key"], parent["id"], child["nonce"], json.dumps(child, sort_keys=True)) == response["sig"]
    assert ensure(srv, other, "pi-A")[0] == 403
    assert ensure(srv, parent, "host-pi")[0] == 403
    assert ensure(srv, parent, parent["id"])[0] == 403
    assert ensure(srv, {**child, "id": "pi-A"}, "grandchild")[0] == 403
    code, again = ensure(srv, parent, "pi-A")
    assert code == 200 and again["payload"]["created"] is False
    assert again["payload"]["signing_key"] == child["signing_key"]
    assert host["signing_key"] not in json.dumps(again)


def test_concurrent_registration_is_idempotent(serves):
    srv = serves()
    parent = register_session(srv, "container-parent")
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: ensure(srv, parent, "same-pi"), range(4)))
    assert all(code == 200 for code, _ in results)
    assert len({reply["payload"]["signing_key"] for _, reply in results}) == 1
    assert sum(reply["payload"]["created"] for _, reply in results) == 1


def test_parent_revoke_cascades_without_touching_other_sessions(serves):
    srv = serves()
    parent = register_session(srv, "container-parent")
    other = register_session(srv, "other-parent")
    child = ensure(srv, parent, "pi-A")[1]["payload"]
    sibling = ensure(srv, other, "pi-B")[1]["payload"]
    assert http_json("POST", srv.admin_port, "/admin/sessions/revoke", {"id": parent["id"]},
                     headers={"X-Admin-Token": ADMIN_TOKEN})[0] == 200
    assert poll(srv, "pi-A", child["signing_key"])[0] == 403
    assert ensure(srv, parent, "new-pi")[0] == 403
    # 管理员复活接线身份, 不能顺带复活旧 pi 凭据.
    renewed = http_json("POST", srv.admin_port, "/admin/sessions/ensure", {"id": parent["id"]},
                        headers={"X-Admin-Token": ADMIN_TOKEN})[1]
    assert ensure(srv, renewed, "pi-A")[0] == 403
    assert poll(srv, "pi-A", child["signing_key"])[0] == 403
    assert poll(srv, "pi-B", sibling["signing_key"])[0] == 200


def test_owner_survives_restart_and_old_database_migration(mailbox, tmp_path):
    db = tmp_path / "old.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, signing_key TEXT, response_key TEXT, revoked INTEGER, last_poll REAL, created_at REAL)")
        conn.execute("INSERT INTO sessions VALUES ('bootstrap','parent-k','parent-r',0,0,0)")
    box = mailbox.Mailbox(db_path=db)
    ts = str(time.time())
    signature = mailbox.sign("parent-k", "bootstrap", ts, "ensure-session", "pi-A")
    child, created = box.ensure_child_session("bootstrap", "pi-A", ts, signature)
    assert created
    original_key = child.signing_key
    box._db.close()
    restored = mailbox.Mailbox(db_path=db)
    try:
        child, created = restored.ensure_child_session("bootstrap", "pi-A", ts, signature)
        assert not created and child.signing_key == original_key and child.parent_id == "bootstrap"
        restored.revoke_session("bootstrap")
    finally:
        restored._db.close()
    restored = mailbox.Mailbox(db_path=db)
    try:
        assert restored.get_session("pi-A").revoked
        with pytest.raises(mailbox.MailboxError):
            restored._verify("pi-A", ts, mailbox.sign(original_key, "pi-A", ts))
    finally:
        restored._db.close()


def test_pi_pull_window_keeps_parent_container_binding(serves):
    srv = serves()
    parent = register_session(srv, "swt-demo-deadbeef")
    peer = register_session(srv, "peer")
    child = ensure(srv, parent, "pi-A")[1]["payload"]
    for index, container in enumerate(("swt-demo", "pi-A", "somebody-else")):
        body = json.dumps({"tool": "swt.pull-window", "container": container})
        letter = make_letter(letter_id=f"pull-{index}", from_="pi-A", to="peer", type_="exec", body=body)
        assert post_letter(srv, "pi-A", child["signing_key"], letter)[0] == 200
        reply = poll(srv, "peer", peer["signing_key"])[1]["payload"]["letter"]
        assert reply["downgraded"] is (container == "somebody-else")
        assert reply["from"] == "pi-A"


@pytest.mark.parametrize("fault", ["wrong-signature", "wrong-id", "old-server", "unreachable"])
def test_registration_failure_never_writes_config_or_exposes_keys(mailbox, tmp_path, monkeypatch, capsys, fault):
    monkeypatch.setenv("SWT_MAILBOX_URL", "http://127.0.0.1:1")
    monkeypatch.setenv("SWT_SESSION_ID", "bootstrap")
    monkeypatch.setenv("SWT_SESSION_SIGNING_KEY", "bootstrap-secret")
    monkeypatch.setenv("SWT_SESSION_RESPONSE_KEY", "bootstrap-response-secret")
    cfg = tmp_path / "pi.json"
    cfg.write_text("existing-config")

    def fake_post(*args, **kwargs):
        if fault == "old-server":
            raise mailbox.urllib.error.HTTPError(args[0], 404, "old", {}, None)
        if fault == "unreachable":
            raise mailbox.urllib.error.URLError("offline")
        payload = {"ok": True, "id": "pi-A" if fault != "wrong-id" else "other-id", "nonce": "n",
                   "signing_key": "child-secret", "response_key": "child-response-secret", "created": True}
        sig = mailbox.sign("bootstrap-response-secret", "bootstrap", "n", json.dumps(payload, sort_keys=True))
        return {"payload": payload, "sig": "bad" if fault == "wrong-signature" else sig}

    monkeypatch.setattr(mailbox, "http_post", fake_post)
    with pytest.raises(SystemExit) as exc:
        mailbox.cmd_ensure_session("pi-A", config=cfg)
    assert exc.value.code == 3
    assert cfg.read_text() == "existing-config"
    output = capsys.readouterr()
    for secret in ("bootstrap-secret", "bootstrap-response-secret", "child-secret", "child-response-secret"):
        assert secret not in output.out + output.err
