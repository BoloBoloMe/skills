"""证明脚本: 导出失败被拒后, gateway 有没有写本地失败记录.

不修改仓库代码. 用 sys.addaudithook 监视 request_export 期间的写文件/建连接事件.
判断错时 assert 失败, 退出码非零.
"""

import ast
import os
import subprocess
import sys
import tempfile

REPO = "/tmp/orchestra-18/drill"
GATEWAY = os.path.join(REPO, "src/svc/gateway.py")
sys.path.insert(0, os.path.join(REPO, "src"))

from svc import gateway  # noqa: E402

WRITE_EVENTS = {"open", "os.open", "socket.connect", "socket.__new__"}
state = {"armed": False, "events": []}
CONTROL = os.path.join("/tmp/orchestra-18/red-exp/out", "control_write.txt")


def hook(event, args):
    if not state["armed"]:
        return
    if event in WRITE_EVENTS:
        state["events"].append((event, repr(args)[:200]))
    elif event == "open":
        state["events"].append((event, repr(args)[:200]))


def run_capture(fn):
    state["events"] = []
    state["armed"] = True
    try:
        try:
            return fn(), list(state["events"])
        except BaseException as exc:
            return exc, list(state["events"])
    finally:
        state["armed"] = False


def main():
    assert sys.version_info[:2] == (3, 14), sys.version
    # 被测的就是仓库里这份 gateway.py, 没有副本
    assert os.path.realpath(gateway.__file__) == os.path.realpath(GATEWAY), gateway.__file__

    # 静态结论: gateway.py 里没有任何写文件/记日志/落盘的代码
    src = open(GATEWAY, encoding="utf-8").read()
    tree = ast.parse(src)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    attrs = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
    assert "open" not in names, f"gateway 出现 open(): {names}"
    assert not ({"write", "write_text", "write_bytes", "dump", "open"} & attrs), attrs
    assert "logging" not in src and "logger" not in src and "Path(" not in src
    assert "import os" in src  # 只读环境变量, 不落盘

    # 审计服务打桩: 只为走到 export. 不写仓库, 只在内存里换掉函数
    audit_calls = []
    gateway._audit = lambda event: audit_calls.append(event)

    sys.addaudithook(hook)

    # 正控: 先确认探针真的能看见写文件, 否则 "没有写" 不算证据
    def control():
        with open(CONTROL, "w", encoding="utf-8") as fh:
            fh.write("x")
    _ignored, control_events = run_capture(control)
    print("正控事件:", control_events)
    assert any(e[0] in ("open", "os.open") for e in control_events), "审计钩子没抓到写文件, 探针失效"

    # 真实路径: 940.0 会被 export 拒绝, 看 gateway 在拒绝之后做什么
    err, events = run_capture(lambda: gateway.request_export([("x", 940.0)]))
    print("返回:", err)
    print("拒绝期间的事件:", events)
    print("_audit 调用序列:", audit_calls)
    assert isinstance(err, ValueError) and "金额越界: x" in str(err), err
    assert events == [], f"拒绝期间出现了写文件或建连接: {events}"
    assert audit_calls == ["export_request"], f"拒绝后仍调了审计: {audit_calls}"

    # 成功路径对照: 800.0 通过, 看是否也零写盘
    payload, ok_events = run_capture(lambda: gateway.request_export([("x", 800.0)]))
    print("成功 payload:", repr(payload), "事件:", ok_events, "审计:", audit_calls)
    assert payload.startswith("order_id,amount_usd"), payload
    assert ok_events == [], ok_events
    assert audit_calls == ["export_request", "export_request", "export_done"], audit_calls

    # 工作目录里没有被写出任何东西
    print("\nALL ASSERTIONS PASSED")


if __name__ == "__main__":
    os.makedirs(os.path.join("/tmp/orchestra-18/red-exp/out"), exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        main()
        left = os.listdir(td)
        assert left == [], f"临时工作目录被写入: {left}"
    print("临时工作目录为空, 未落盘")
    st = subprocess.run(["git", "-C", REPO, "status", "--porcelain"], capture_output=True, text=True)
    assert st.stdout == "", f"仓库被改动: {st.stdout}"
    print("仓库 git status 为空")
