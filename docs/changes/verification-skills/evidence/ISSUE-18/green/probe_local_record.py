"""非正式 TC: 拒绝之后 gateway / export 有没有写本地失败记录.

只在测量进程内包 builtins.open / os.open / os.write / logging, 不改 src/svc 任何字节.
判断错 (出现写文件或日志调用) 就以非零退出码失败.
"""
import builtins
import io
import logging
import os
import sys

REPO = "/tmp/orchestra-18/drill-green"
sys.path.insert(0, os.path.join(REPO, "src"))

import svc.export as export_mod  # noqa: E402
import svc.gateway as gateway_mod  # noqa: E402
import svc.limits as limits_mod  # noqa: E402

writes = []   # (调用点, 参数)
logs = []
failures = []


def snapshot(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
        for name in filenames:
            p = os.path.join(dirpath, name)
            try:
                out[p] = os.stat(p).st_mtime_ns
            except OSError:
                out[p] = -1
    return out


def is_write_mode(mode):
    return any(ch in str(mode) for ch in ("w", "a", "x", "+"))


real_open = builtins.open
real_os_open = os.open
real_write = os.write
real_log = logging.Logger._log


def spy_open(file, mode="r", *a, **kw):
    if is_write_mode(mode):
        writes.append(("builtins.open", str(file), mode))
    return real_open(file, mode, *a, **kw)


def spy_os_open(path, flags, *a, **kw):
    if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND):
        writes.append(("os.open", str(path), flags))
    return real_os_open(path, flags, *a, **kw)


def spy_os_write(fd, data):
    writes.append(("os.write", f"fd={fd}", repr(data[:60])))
    return real_write(fd, data)


def spy_log(self, level, msg, *a, **kw):
    logs.append((self.name, level, str(msg)[:80]))
    return real_log(self, level, msg, *a, **kw)


builtins.open = spy_open
os.open = spy_os_open
os.write = spy_os_write
logging.Logger._log = spy_log

try:
    print("--- A. 成品入口路径 (审计失败) ---")
    for label, env in (("AUDIT_URL 未设置", None), ("AUDIT_URL 假地址", "https://audit.example.invalid")):
        if env is None:
            os.environ.pop("AUDIT_URL", None)
        else:
            os.environ["AUDIT_URL"] = env
        before = snapshot(REPO)
        writes.clear()
        logs.clear()
        try:
            gateway_mod.request_export([("a-2", 940.0), ("a-1", 120.5)])
            outcome = "返回成功"
        except BaseException as exc:  # noqa: BLE001
            outcome = f"{type(exc).__name__}: {exc}"
        after = snapshot(REPO)
        print(f"{label}: request_export -> {outcome}")
        print(f"{'':<22} 写文件调用={writes}  日志调用={logs}")
        new_files = set(after) - set(before)
        changed = {p for p in set(after) & set(before) if after[p] != before[p]}
        print(f"{'':<22} 仓库新增文件={sorted(new_files)}  仓库被改文件={sorted(changed)}")
        if writes:
            failures.append(f"{label}: 出现写文件调用 {writes}")
        if logs:
            failures.append(f"{label}: 出现日志调用 {logs}")
        if new_files or changed:
            failures.append(f"{label}: 仓库文件变化 {new_files | changed}")

    print("\n--- B. 导出拒绝路径 (内部函数, 上限真的拦住 940) ---")
    writes.clear()
    logs.clear()
    try:
        export_mod.export([("a-2", 940.0)])
        outcome = "返回成功"
    except BaseException as exc:  # noqa: BLE001
        outcome = f"{type(exc).__name__}: {exc}"
    print("export.export([('a-2',940.0)]) ->", outcome)
    print("写文件调用=", writes, " 日志调用=", logs)
    if not outcome.startswith("ValueError"):
        failures.append("940 没有被上限拒绝, 用例前提不成立")
    if writes:
        failures.append(f"导出拒绝路径出现写文件调用 {writes}")
    if logs:
        failures.append(f"导出拒绝路径出现日志调用 {logs}")
finally:
    builtins.open = real_open
    os.open = real_os_open
    os.write = real_write
    logging.Logger._log = real_log

print("\n--- C. gateway 源码里有没有写记录的入口 ---")
src = real_open(os.path.join(REPO, "src/svc/gateway.py"), encoding="utf-8").read()
suspect = [tok for tok in ("open(", "write", "logging", "json.dump", "sqlite", "tempfile", "Path(") if tok in src]
print("gateway.py 中可疑 I/O 记号:", suspect if suspect else "无")
if suspect:
    failures.append(f"gateway.py 含 I/O 记号 {suspect}")

print("\n=== 结果:", "全部断言通过" if not failures else f"失败: {failures}")
sys.exit(0 if not failures else 1)
