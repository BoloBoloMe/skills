"""mailbox 取信 CLI 测试 (ISSUE-01, 缺省动作子进程接缝).

TS-004 test_fetch_cli / TS-005 test_auto_ack / TS-006 test_retry_on_network_error.

ISSUE-05 (取信与服务状态显式):
TC-024 test_stale_state_file_reports_unreachable — serve 停但状态文件残留时
       status 先验活, 失活明报信箱不可达 (AC-014).
TC-025 test_fetch_reports_service_down_immediately — 服务未起时取信立即明报
       再退避, 不静默 (AC-015).
TC-026 test_fetch_timeout_exits_and_reports — --timeout 到时无信退出码 0 报无信.
TC-027 test_fetch_count_exits_after_n — --count 取满即退, 末封 pending_ack 不丢.
TC-028 test_status_env_credentials_and_liveness — 仅 env 凭证时 status 报真实
       session/地址/存活 (AC-017).

真实子进程跑 mailbox.py (缺省取信), 真实 serve 子进程做服务端,
凭证走容器式 env 注入 (SWT_MAILBOX_URL + SWT_SESSION_*).
共享接缝层 (serve 启动器/签名/HTTP helper) 在 tests/conftest.py.
"""
from __future__ import annotations

import json
import os
import select
import socket
import subprocess
import sys
import time
from pathlib import Path

from conftest import (SCRIPT, ack_letter, free_port, make_letter, poll,
                      post_letter, register_session, sign)


def cli_env(port, session_id, signing_key, response_key, workdir):
    """容器式 env 凭证; MAILBOX_CONFIG 指向临时目录隔离 state file."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update({
        "SWT_MAILBOX_URL": f"http://127.0.0.1:{port}",
        "SWT_SESSION_ID": session_id,
        "SWT_SESSION_SIGNING_KEY": signing_key,
        "SWT_SESSION_RESPONSE_KEY": response_key,
        "MAILBOX_CONFIG": str(workdir / "mailbox.json"),
        # 同步隔离状态/邻居路径: CLI 入口会跑旧路径迁移, 不能碰真机文件
        "MAILBOX_STATE": str(workdir / "state.json"),
        "MAILBOX_NEIGHBORS": str(workdir / "neighbors.json"),
    })
    return env


def no_credentials_env(workdir):
    """无任何凭证的隔离 env (TS-001: 只剩状态文件可读)."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    for key in ("SWT_MAILBOX_URL", "SWT_SESSION_ID",
                "SWT_SESSION_SIGNING_KEY", "SWT_SESSION_RESPONSE_KEY"):
        env.pop(key, None)
    env.update({
        "MAILBOX_CONFIG": str(workdir / "mailbox.json"),
        "MAILBOX_STATE": str(workdir / "state.json"),
        "MAILBOX_NEIGHBORS": str(workdir / "neighbors.json"),
    })
    return env


def test_stale_state_file_reports_unreachable(serves, tmp_path):
    """ISSUE-05 TS-001 (TC-024/AC-014): serve 停但状态文件残留时,
    status 读状态文件先验活, 失活明报信箱不可达, 不当成服务在线."""
    srv = serves()
    state_file = tmp_path / "s" / "state.json"
    srv.proc.kill()  # SIGKILL 不走清理路径, 状态文件残留 = 模拟服务停止后残留
    srv.proc.wait()
    assert state_file.exists(), "serve 被杀后状态文件应残留"

    env = no_credentials_env(tmp_path / "cli")
    env["MAILBOX_STATE"] = str(state_file)
    r = subprocess.run([sys.executable, str(SCRIPT), "status"], env=env,
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    assert "不可达" in r.stdout, (
        f"残留状态文件验活失败应明报信箱不可达, 实际输出:\n{r.stdout}")


def test_fetch_reports_service_down_immediately(serves, tmp_path):
    """ISSUE-05 TS-002 (TC-025/AC-015): 服务未起时取信立即输出
    "信箱服务未启动/不可达" 再退避重试, 不静默; 明报行只打一次不刷屏."""
    port = free_port()  # 无 serve 监听 = 服务未起
    env = cli_env(port, "down1", "down-signing-key", "down-response-key",
                  tmp_path / "cli")
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        # 数秒内 stderr 必须出现明报行 (连接拒绝是即时的)
        deadline = time.time() + 5
        saw = False
        while time.time() < deadline:
            r, _, _ = select.select([proc.stderr], [], [], 0.2)
            if r and "信箱服务未启动/不可达" in proc.stderr.readline():
                saw = True
                break
        assert saw, "服务未起时取信应立即明报再退避, 而非静默"
        # 退避持续: 进程不退出, stdout 保持零输出 (BR-005), 明报行不重复
        time.sleep(1.5)
        assert proc.poll() is None, "明报后应退避重试而非退出"
        r, _, _ = select.select([proc.stdout], [], [], 0)
        assert not r, "退避等待期间 stdout 必须零输出"
        r, _, _ = select.select([proc.stderr], [], [], 0)
        assert not r, "明报行只打一次, 退避重试不刷屏"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()


def test_fetch_timeout_exits_and_reports(serves, tmp_path):
    """ISSUE-05 TS-003 (TC-026/AC-016): --timeout <秒> 无信到时
    退出码 0 并报无信, 不再无限阻塞."""
    srv = serves()
    creds = register_session(srv, "tdev")
    env = cli_env(srv.port, "tdev", creds["signing_key"],
                  creds["response_key"], tmp_path / "cli")
    start = time.time()
    r = subprocess.run([sys.executable, str(SCRIPT), "--timeout", "2"],
                       env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, "到时无信应退出码 0"
    assert "无信" in r.stdout, f"到时应报无信, 实际输出:\n{r.stdout}"
    assert time.time() - start < 15, "--timeout 到时须真的退出而非长阻塞"


def test_fetch_count_exits_after_n(serves, tmp_path):
    """ISSUE-05 TS-004 (TC-027/AC-016): --count 2 且队列有 3 封 →
    取满 2 封即退; 末封 pending_ack 留 cli-state 不丢, 第 3 封仍可取."""
    srv = serves()
    creds = register_session(srv, "cdev")
    key = creds["signing_key"]
    for i in (1, 2, 3):
        code, _ = post_letter(srv, "cdev", key,
                              make_letter(letter_id=f"L-c{i}", to="cdev",
                                          body=f"第{i}封信"))
        assert code == 200
    env = cli_env(srv.port, "cdev", key, creds["response_key"],
                  tmp_path / "cli")
    r = subprocess.run([sys.executable, str(SCRIPT), "--count", "2"],
                       env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    assert "第1封信" in r.stdout and "第2封信" in r.stdout
    assert "第3封信" not in r.stdout, "取满 2 封即退, 第 3 封不应取"
    # 末封 pending_ack 留在 cli-state, 下次调用正常回执 (风险提示: 不丢)
    cli_state = json.loads((tmp_path / "cli" / "cli-state.json").read_text())
    assert cli_state["pending_ack"]["letter_id"] == "L-c2"
    # 第 3 封仍在队列可取
    code, resp = poll(srv, "cdev", key)
    assert code == 200
    assert resp["payload"]["letter"]["id"] == "L-c3"


def test_fetch_cli_state_override(serves, tmp_path):
    """ISSUE-07 TS-001 (TC-037 前置/D009/AC-001 底层): --cli-state 指定路径时
    pending_ack/seen_ids 落该文件, 不落缺省 cli-state.json;
    env MAILBOX_CLI_STATE 同义 (per-listener 状态文件修竞态)."""
    srv = serves()
    creds = register_session(srv, "statedev")
    key = creds["signing_key"]
    code, _ = post_letter(srv, "statedev", key,
                          make_letter(letter_id="L-s1", to="statedev",
                                      body="状态归属"))
    assert code == 200
    env = cli_env(srv.port, "statedev", key, creds["response_key"],
                  tmp_path / "cli")
    override = tmp_path / "override" / "listener.json"

    r = subprocess.run([sys.executable, str(SCRIPT),
                        "--cli-state", str(override)],
                       env=env, capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr
    assert "状态归属" in r.stdout
    state = json.loads(override.read_text())
    assert state["pending_ack"]["letter_id"] == "L-s1", \
        "pending_ack 应落 --cli-state 指定文件"
    assert "L-s1" in state["seen_ids"], "seen_ids 应落 --cli-state 指定文件"
    assert not (tmp_path / "cli" / "cli-state.json").exists(), \
        "--cli-state 覆盖后不应再写缺省 cli-state.json"

    # env MAILBOX_CLI_STATE 同义 (D009): 第二封信状态走 env 指定路径
    code, _ = post_letter(srv, "statedev", key,
                          make_letter(letter_id="L-s2", to="statedev",
                                      body="第二封"))
    assert code == 200
    env2 = dict(env)
    env2["MAILBOX_CLI_STATE"] = str(tmp_path / "override" / "env.json")
    r2 = subprocess.run([sys.executable, str(SCRIPT)], env=env2,
                        capture_output=True, text=True, timeout=30)
    assert r2.returncode == 0, r2.stderr
    assert "第二封" in r2.stdout
    state2 = json.loads((tmp_path / "override" / "env.json").read_text())
    assert state2["pending_ack"]["letter_id"] == "L-s2"


def test_status_env_credentials_and_liveness(serves, tmp_path):
    """ISSUE-05 TS-005 (TC-028/AC-017): 容器内仅 env 凭证时, status
    认 env 报真实 session 名/信箱地址/存活, 不再全显 (未设置)."""
    srv = serves()
    creds = register_session(srv, "envdev")
    cli = tmp_path / "cli"
    cli.mkdir(parents=True)  # 无配置文件, 仅 env 凭证
    env = cli_env(srv.port, "envdev", creds["signing_key"],
                  creds["response_key"], cli)
    r = subprocess.run([sys.executable, str(SCRIPT), "status"], env=env,
                       capture_output=True, text=True, timeout=30)
    assert r.returncode == 0
    assert "envdev" in r.stdout, f"应报真实 session, 实际:\n{r.stdout}"
    assert str(srv.port) in r.stdout, f"应报真实信箱地址, 实际:\n{r.stdout}"
    assert "在线" in r.stdout, f"应报服务存活状态, 实际:\n{r.stdout}"


def test_fetch_timeout_beats_long_hold(serves, tmp_path):
    """评审修复: 服务端 hold 长于 --timeout 时, poll 超时按剩余时间收紧,
    --timeout 2 不被 8s hold 拖到长轮询结束才退, 到时即退报无信 (AC-016)."""
    srv = serves(hold="8")  # hold 8s > timeout 2s: 无信时服务端挂住不返
    creds = register_session(srv, "holddev")
    env = cli_env(srv.port, "holddev", creds["signing_key"],
                  creds["response_key"], tmp_path / "cli")
    start = time.time()
    r = subprocess.run([sys.executable, str(SCRIPT), "--timeout", "2"],
                       env=env, capture_output=True, text=True, timeout=30)
    elapsed = time.time() - start
    assert r.returncode == 0, "到时无信应退出码 0"
    assert "无信" in r.stdout
    # 修复前: poll 固定 30s 超时, 须等满服务端 hold 8s 才退 — 超出 2+3 余量
    assert elapsed < 2 + 3, f"--timeout 到时退出不及时, 实际耗时 {elapsed:.1f}s"


def test_poll_client_disconnect_no_traceback(serves, tmp_path):
    """ISSUE-14 TS-001: 取信客户端超时先于服务端 hold 到期挂断 (AC-016 的
    --timeout 场景常态) 后, 服务端 hold 唤醒往断开 socket 写应答不再吐
    BrokenPipeError 堆栈; 随后正常投信/取信不受影响."""
    hold = "2"
    srv = serves(hold=hold)
    creds = register_session(srv, "bpdev")
    # 原始 socket 发合法 poll 请求后立即挂断 = 客户端消失在 hold 期中途
    sig_ts = str(time.time())
    sig = sign(creds["signing_key"], "bpdev", sig_ts)
    body = json.dumps({"session": "bpdev", "sig_ts": sig_ts,
                       "sig": sig}).encode()
    req = (b"POST /mailbox/poll HTTP/1.1\r\n"
           b"Host: 127.0.0.1\r\n"
           b"Content-Type: application/json\r\n"
           + f"Content-Length: {len(body)}\r\n\r\n".encode()
           + body)
    sock = socket.create_connection(("127.0.0.1", srv.port), timeout=5)
    sock.sendall(req)
    sock.close()
    # hold 到期后服务端才尝试写应答, 留 margin 确保写出路径已执行完
    time.sleep(float(hold) + 1.5)
    # 断开事件之后正常投信/取信仍工作
    code, r = post_letter(srv, "bpdev", creds["signing_key"],
                          make_letter("L-bp", to="bpdev"))
    assert code == 200 and r["payload"]["ok"], r
    code, r = poll(srv, "bpdev", creds["signing_key"])
    assert code == 200 and r["payload"]["letter"]["id"] == "L-bp", r
    srv.stop()
    err = srv.proc.stderr.read()
    assert "BrokenPipeError" not in err, f"serve stderr 吐了断开堆栈:\n{err}"
    assert "Traceback" not in err, f"serve stderr 吐了堆栈:\n{err}"


def test_fetch_cli(serves, tmp_path):
    """TS-004: 缺省调用阻塞等信, 信到后 stdout 输出正文+处理指引+继续调用提示."""
    srv = serves()
    creds = register_session(srv, "dev1")
    env = cli_env(srv.port, "dev1", creds["signing_key"],
                  creds["response_key"], tmp_path / "cli")

    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        time.sleep(0.5)  # 让 CLI 先挂上长轮询
        code, _ = post_letter(srv, "dev1", creds["signing_key"],
                              make_letter(to="dev1", body="开会提醒: 15:00"))
        assert code == 200
        out, _ = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "开会提醒: 15:00" in out  # 信件正文
    assert "处理指引" in out          # 处理指引
    assert "不可信" in out            # 不可信输入声明
    assert "继续调用" in out          # 继续调用提示


def test_auto_ack(serves, tmp_path):
    """TS-005: 再次调用取信 CLI 时先自动回执上一条, 再阻塞等新信."""
    srv = serves()
    creds = register_session(srv, "dev1")
    signing_key = creds["signing_key"]
    env = cli_env(srv.port, "dev1", signing_key,
                  creds["response_key"], tmp_path / "cli")

    # 第一次取信: 取到 L1 (持有租约但未回执)
    code, _ = post_letter(srv, "dev1", signing_key,
                          make_letter(letter_id="L-1", to="dev1", body="第一封"))
    assert code == 200
    first = subprocess.run([sys.executable, str(SCRIPT)], env=env,
                           capture_output=True, text=True, timeout=15)
    assert first.returncode == 0
    assert "第一封" in first.stdout
    # L1 仍租出未回执: 错 token ack → 409
    code, _ = ack_letter(srv, "dev1", signing_key, "L-1", "bogus-token")
    assert code == 409

    # 第二次调用: 先自动回执 L1, 再阻塞
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        # 等服务端确认 L1 已处理: 已处理后错 token ack 幂等 200 (未回执则 409)
        deadline = time.time() + 10
        code = 0
        while time.time() < deadline:
            code, _ = ack_letter(srv, "dev1", signing_key, "L-1", "bogus-token")
            if code == 200:
                break
            time.sleep(0.2)
        assert code == 200, "CLI 未自动回执上一条"
        assert proc.poll() is None  # 回执后仍存活 = 阻塞等新信中
        # 服务端侧 L1 不再可取
        code, resp = poll(srv, "dev1", signing_key)
        assert code == 200
        assert resp["payload"]["letter"] is None
        # 投 L2 → CLI 正常返回
        code, _ = post_letter(srv, "dev1", signing_key,
                              make_letter(letter_id="L-2", to="dev1", body="第二封"))
        assert code == 200
        out, _ = proc.communicate(timeout=15)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "第二封" in out


def test_retry_on_network_error(serves, tmp_path):
    """TS-006: serve 未启动时 CLI 静默重试不退出; serve 启动后投信正常返回."""
    port = free_port()
    env = cli_env(port, "retry1", "retry-signing-key", "retry-response-key",
                  tmp_path / "cli")

    # serve 未启动: CLI 应在超时窗口内仍存活且 stdout 零输出 (BR-005)
    proc = subprocess.Popen([sys.executable, str(SCRIPT)], env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            text=True)
    try:
        time.sleep(2.5)
        assert proc.poll() is None, "连接拒绝时 CLI 退出了"
        r, _, _ = select.select([proc.stdout], [], [], 0)
        assert not r, "空闲等待期间 stdout 必须零输出"

        # serve 启动后注册同名 session 并投信, CLI 应正常取到
        srv = serves(port=port)
        assert srv.port == port, "预设端口被抢, 测试环境不干净"
        register_session(srv, "retry1", signing_key="retry-signing-key",
                         response_key="retry-response-key")
        code, _ = post_letter(srv, "retry1", "retry-signing-key",
                              make_letter(to="retry1", body="迟到的信"))
        assert code == 200
        out, _ = proc.communicate(timeout=20)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    assert proc.returncode == 0
    assert "迟到的信" in out
