"""mailbox 拉窗门禁测试 (ISSUE-07, D014, AC-009).

TS-001 waypipe 缺席 skipped / TS-002 同容器 300s 限频 / TS-003 限频跨取信循环生效.

取信 CLI 在进程内驱动 (importlib 加载模块 + monkeypatch waypipe 在场检查,
不依赖真实环境是否装 waypipe); serve 仍跑真实子进程 (共享接缝层 conftest).
skipped 信的 ack 经 spy 捕获 outcome, 并以服务端幂等 ack 佐证已回执.
"""
from __future__ import annotations

import importlib.util
import json
import threading
import time
from pathlib import Path

from conftest import (ROOT, SCRIPT, ack_letter, make_letter, poll, post_letter,
                      register_session)

PULL_WINDOW_BODY = json.dumps({"tool": "swt.pull-window", "container": "c1"})


def load_module():
    """按文件路径重新加载 mailbox 模块 (模拟新 CLI 进程, 无内存状态残留)."""
    spec = importlib.util.spec_from_file_location("mailbox_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def cli_env(monkeypatch, srv, session_id, signing_key, response_key, workdir):
    """容器式 env 凭证注入; MAILBOX_CONFIG 指向临时目录隔离 state file."""
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SWT_MAILBOX_URL", f"http://127.0.0.1:{srv.port}")
    monkeypatch.setenv("SWT_SESSION_ID", session_id)
    monkeypatch.setenv("SWT_SESSION_SIGNING_KEY", signing_key)
    monkeypatch.setenv("SWT_SESSION_RESPONSE_KEY", response_key)
    monkeypatch.setenv("MAILBOX_CONFIG", str(workdir / "mailbox.json"))


def spy_acks(mod, monkeypatch):
    """包裹 mod.ack_letter 记录 outcome, 仍走真实 HTTP 回执."""
    records = []
    orig = mod.ack_letter

    def wrapper(url, sid, skey, letter_id, lease_token, outcome="handled"):
        records.append((letter_id, outcome))
        return orig(url, sid, skey, letter_id, lease_token, outcome=outcome)

    monkeypatch.setattr(mod, "ack_letter", wrapper)
    return records


def wait_processed(srv, session_id, signing_key, letter_id, timeout=10):
    """等服务端确认 letter 已回执: 错 token ack 幂等 200 (未回执则 409)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        code, _ = ack_letter(srv, session_id, signing_key, letter_id, "bogus")
        if code == 200:
            return
        time.sleep(0.2)
    raise AssertionError(f"{letter_id} 未被 CLI 回执")


def test_waypipe_missing_skipped(serves, tmp_path, monkeypatch, capsys):
    """TS-001: waypipe 缺席 → 立即 ack skipped:waypipe-missing,
    stdout 不含信正文, 输出安装提示, 继续 poll."""
    srv = serves()
    creds = register_session(srv, "dev1")
    skey = creds["signing_key"]
    cli_env(monkeypatch, srv, "dev1", skey, creds["response_key"],
            tmp_path / "cli")

    mod = load_module()
    monkeypatch.setattr(mod, "waypipe_present", lambda: False)
    acks = spy_acks(mod, monkeypatch)

    code, _ = post_letter(srv, "dev1", skey,
                          make_letter(letter_id="PW-1", to="dev1",
                                      type_="exec", body=PULL_WINDOW_BODY))
    assert code == 200

    # skipped 后 CLI 继续长轮询不退出 → 守护线程驱动
    t = threading.Thread(target=mod.cmd_fetch, daemon=True)
    t.start()
    wait_processed(srv, "dev1", skey, "PW-1")

    assert ("PW-1", "skipped:waypipe-missing") in acks
    out = capsys.readouterr().out
    assert "swt.pull-window" not in out  # 信正文不呈现给 LLM
    assert "waypipe" in out              # 安装提示 (不断言精确文案)


def test_waypipe_missing_hint_dedup(serves, tmp_path, monkeypatch, capsys):
    """review 修复 (平移旧扩展 waypipeMissingNotified): 同一取信进程内
    waypipe 缺席期连续两封拉窗信, stdout 只含一次安装提示."""
    srv = serves()
    creds = register_session(srv, "dev1")
    skey = creds["signing_key"]
    cli_env(monkeypatch, srv, "dev1", skey, creds["response_key"],
            tmp_path / "cli")

    mod = load_module()
    monkeypatch.setattr(mod, "waypipe_present", lambda: False)
    spy_acks(mod, monkeypatch)

    # 同一 cmd_fetch 进程连续处理两封缺席拉窗信 (skipped 后继续 poll)
    t = threading.Thread(target=mod.cmd_fetch, daemon=True)
    t.start()
    for letter_id in ("PW-1", "PW-2"):
        code, _ = post_letter(srv, "dev1", skey,
                              make_letter(letter_id=letter_id, to="dev1",
                                          type_="exec", body=PULL_WINDOW_BODY))
        assert code == 200
        wait_processed(srv, "dev1", skey, letter_id)

    out = capsys.readouterr().out
    assert out.count("waypipe 未安装") == 1  # 缺席期只提示一次


def test_waypipe_missing_hint_resets_on_restore(serves, tmp_path, monkeypatch,
                                                capsys):
    """review 修复: waypipe 恢复在场后提示标志重置 — 再次缺席时重新提示."""
    srv = serves()
    creds = register_session(srv, "dev1")
    skey = creds["signing_key"]
    cli_env(monkeypatch, srv, "dev1", skey, creds["response_key"],
            tmp_path / "cli")

    mod = load_module()
    present = {"v": False}
    monkeypatch.setattr(mod, "waypipe_present", lambda: present["v"])
    spy_acks(mod, monkeypatch)

    def post(letter_id):
        code, _ = post_letter(srv, "dev1", skey,
                              make_letter(letter_id=letter_id, to="dev1",
                                          type_="exec", body=PULL_WINDOW_BODY))
        assert code == 200

    # 缺席期 1: 提示一次
    t = threading.Thread(target=mod.cmd_fetch, daemon=True)
    t.start()
    post("PW-1")
    wait_processed(srv, "dev1", skey, "PW-1")

    # waypipe 恢复: 过门, cmd_fetch 呈现后返回 (线程退出), 标志重置
    present["v"] = True
    post("PW-2")
    t.join(timeout=15)
    assert not t.is_alive(), "过门后 cmd_fetch 应呈现并返回"

    # 缺席期 2: 再次缺席 → 重新提示一次
    present["v"] = False
    t2 = threading.Thread(target=mod.cmd_fetch, daemon=True)
    t2.start()
    post("PW-3")
    wait_processed(srv, "dev1", skey, "PW-3")

    out = capsys.readouterr().out
    assert out.count("waypipe 未安装") == 2  # 每个缺席期各一次


def test_rate_limit(serves, tmp_path, monkeypatch, capsys):
    """TS-002: waypipe 在场; 第一封正常呈现; 300s 内同容器第二封
    → 自动 ack skipped:rate-limited, 不呈现."""
    srv = serves()
    creds = register_session(srv, "dev1")
    skey = creds["signing_key"]
    cli_env(monkeypatch, srv, "dev1", skey, creds["response_key"],
            tmp_path / "cli")

    mod = load_module()
    monkeypatch.setattr(mod, "waypipe_present", lambda: True)
    acks = spy_acks(mod, monkeypatch)

    # 第一封: 过门, 正常呈现后 cmd_fetch 返回
    code, _ = post_letter(srv, "dev1", skey,
                          make_letter(letter_id="PW-1", to="dev1",
                                      type_="exec", body=PULL_WINDOW_BODY))
    assert code == 200
    mod.cmd_fetch()
    out = capsys.readouterr().out
    assert "swt.pull-window" in out      # 正常呈现信正文
    assert not any(o.startswith("skipped") for _, o in acks)

    # 300s 内第二封 (同容器 c1): skipped:rate-limited, 不呈现, 继续 poll
    code, _ = post_letter(srv, "dev1", skey,
                          make_letter(letter_id="PW-2", to="dev1",
                                      type_="exec", body=PULL_WINDOW_BODY))
    assert code == 200
    t = threading.Thread(target=mod.cmd_fetch, daemon=True)
    t.start()
    wait_processed(srv, "dev1", skey, "PW-2")

    assert ("PW-2", "skipped:rate-limited") in acks
    out = capsys.readouterr().out
    assert "swt.pull-window" not in out  # 限频信不呈现给 LLM


def test_rate_limit_persists(serves, tmp_path, monkeypatch, capsys):
    """TS-003: 限频状态落设备本地文件; 取信循环重启 (全新模块实例,
    模拟新 CLI 进程) 后 300s 内同容器再投 → 仍被限频."""
    srv = serves()
    creds = register_session(srv, "dev1")
    skey = creds["signing_key"]
    cli_env(monkeypatch, srv, "dev1", skey, creds["response_key"],
            tmp_path / "cli")

    # 第一个取信循环: 处理 PW-1 (过门, 记限频时刻)
    mod1 = load_module()
    monkeypatch.setattr(mod1, "waypipe_present", lambda: True)
    code, _ = post_letter(srv, "dev1", skey,
                          make_letter(letter_id="PW-1", to="dev1",
                                      type_="exec", body=PULL_WINDOW_BODY))
    assert code == 200
    mod1.cmd_fetch()
    assert "swt.pull-window" in capsys.readouterr().out

    # 取信循环重启: 重新加载模块 = 无内存状态残留, 只能靠 state file
    mod2 = load_module()
    monkeypatch.setattr(mod2, "waypipe_present", lambda: True)
    acks = spy_acks(mod2, monkeypatch)
    code, _ = post_letter(srv, "dev1", skey,
                          make_letter(letter_id="PW-2", to="dev1",
                                      type_="exec", body=PULL_WINDOW_BODY))
    assert code == 200
    t = threading.Thread(target=mod2.cmd_fetch, daemon=True)
    t.start()
    wait_processed(srv, "dev1", skey, "PW-2")

    assert ("PW-2", "skipped:rate-limited") in acks
    assert "swt.pull-window" not in capsys.readouterr().out


def test_pull_window_url_param(serves, tmp_path, monkeypatch, capsys):
    """ISSUE-09 TS-003 (TC-049, AC-030, E2): 拉窗信可带 url 参数 —
    服务端不因第三键降级 (直批), 设备侧取信输出含该 url (按信拉起不猜端口)."""
    srv = serves()
    dev = register_session(srv, "dev1")
    poster_id = "c1-1a2b3c4d"  # 容器 session 投信 (D010 形态)
    poster = register_session(srv, poster_id)
    url = "http://127.0.0.1:8800/app"
    body = json.dumps({"tool": "swt.pull-window", "container": poster_id,
                       "url": url})

    # 段 1 (指令形状): 带 url 三键信 → poll 到 downgraded=False 直批
    code, _ = post_letter(srv, poster_id, poster["signing_key"],
                          make_letter(letter_id="PW-U1", to="dev1",
                                      type_="exec", body=body))
    assert code == 200
    code, resp = poll(srv, "dev1", dev["signing_key"])
    assert code == 200
    letter = resp["payload"]["letter"]
    assert letter["downgraded"] is False
    assert "指令集命中" in letter["note"]
    assert url in letter["body"]

    # 段 2 (取信呈现): 设备侧 cmd_fetch 输出含信中 url
    cli_env(monkeypatch, srv, "dev1", dev["signing_key"],
            dev["response_key"], tmp_path / "cli")
    mod = load_module()
    monkeypatch.setattr(mod, "waypipe_present", lambda: True)
    code, _ = post_letter(srv, poster_id, poster["signing_key"],
                          make_letter(letter_id="PW-U2", to="dev1",
                                      type_="exec", body=body))
    assert code == 200
    mod.cmd_fetch()
    assert url in capsys.readouterr().out


def test_docs_contain_recipes():
    """ISSUE-09 TS-004 (TC-050, BR-008, D011 E4/B5/E5): 文档批 —
    pull-window.md 含 chromium --user-data-dir 强制与音频 -R 退化写法;
    mailbox.md 含 mesh 前提/反向隧道配方(含标记文件与 ClientAliveInterval)/
    换址联动清单/waypipe 已验证版本组合."""
    pw = (ROOT / "workflow" / "mailbox" / "reference" /
          "pull-window.md").read_text()
    assert "--user-data-dir" in pw      # E4: chromium 单例坑, 强制独立数据目录
    assert "-R" in pw and "退化" in pw   # E4: 音频 socket 转发可选 + 退化写法

    mb = (ROOT / "workflow" / "mailbox" / "reference" / "mailbox.md").read_text()
    for kw in ("至少一个方向可达",   # B5: mesh 前提
               "反向隧道",           # B5: 标准配方
               "标记文件",           # B5: 隧道远端留标记
               "ClientAliveInterval",  # B5: 僵尸 -R 端口提醒
               "防火墙白名单",       # B5: 换址联动清单
               "0.8.4", "0.11.0", "minimal"):  # E5: 已验证版本组合
        assert kw in mb, kw


def test_rate_limit_key_unified(monkeypatch):
    """评审修复 2: 限频键统一 + 新旧键衔接 — 同容器换写法 (session id
    形态与裸容器名) 不互相放行; 归一前的历史旧键记录也拦得住新写法."""
    mod = load_module()
    monkeypatch.setattr(mod, "waypipe_present", lambda: True)

    # 换写法不绕限频: 旧写法 (session id 形态) 过门后, 新写法 (裸容器名) 仍被限频
    state = {}
    assert mod.gate_pull_window("c1-1a2b3c4d", state) is None
    assert mod.gate_pull_window("c1", state) == "skipped:rate-limited"

    # 新旧键衔接: 旧版本按 container 字段原样记的键, 新写法查询同样命中
    state = {"lastPullWindowAt": {"c1-1a2b3c4d": time.time()}}
    assert mod.gate_pull_window("c1", state) == "skipped:rate-limited"


def test_swt_pull_window_doc_points_to_mailbox():
    """ISSUE-12 TS-001 (D019, 拉窗文档单源化): swt 侧 pull-window.md 的
    设备侧模板内容改为指针 — 含指向 mailbox skill 参考文档的指针
    (部署后两个 skill 目录同在 ~/.agents/skills/ 下), 且不复述
    --user-data-dir 等模板细节 (权威源在 mailbox 侧, ISSUE-09 落笔)."""
    swt_pw = (ROOT / "workflow" / "use-sandbox-worktree" / "reference" /
              "pull-window.md").read_text()

    # 指针在场: 指向 mailbox skill 的 pull-window 参考文档
    assert "mailbox/reference/pull-window.md" in swt_pw

    # 不复述模板细节: chromium 单例坑参数与完整拉起命令只留在 mailbox 侧
    assert "--user-data-dir" not in swt_pw
    assert "nohup waypipe ssh" not in swt_pw

    # swt 独有内容无损: 三态选路 / 容器侧编排 / STATE 代换 / 残尸纪律
    for kw in ("三态", "容器侧编排", "代换", "残尸"):
        assert kw in swt_pw, kw


def test_non_pullwindow_exec_bypasses_gate(serves, tmp_path, monkeypatch,
                                           capsys):
    """验收标准 4: 非 pull-window 的 exec 信不走本门禁 (白名单属 ISSUE-03) —
    waypipe 缺席也不影响, 正常呈现且不产生 skipped 回执."""
    srv = serves()
    creds = register_session(srv, "dev1")
    skey = creds["signing_key"]
    cli_env(monkeypatch, srv, "dev1", skey, creds["response_key"],
            tmp_path / "cli")

    mod = load_module()
    monkeypatch.setattr(mod, "waypipe_present", lambda: False)
    acks = spy_acks(mod, monkeypatch)

    body = json.dumps({"tool": "swt.screenshot", "args": []})
    code, _ = post_letter(srv, "dev1", skey,
                          make_letter(letter_id="EX-1", to="dev1",
                                      type_="exec", body=body))
    assert code == 200
    mod.cmd_fetch()
    out = capsys.readouterr().out
    assert "swt.screenshot" in out       # 正常呈现
    assert not any(o.startswith("skipped") for _, o in acks)
