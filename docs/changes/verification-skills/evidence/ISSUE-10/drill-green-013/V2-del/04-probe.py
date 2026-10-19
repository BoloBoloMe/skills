#!/usr/bin/env python3
"""V2-del 证明脚本: 只读调查 purge 后能否再读到 r1 数据.

断言对象:
  F1 purge 路径不做网络/伙伴交互 (AST 静态断言, 失败即非零退出).
  F2 data-dir 与 runtime/ 里 purge 后不含 r1 正文 alpha, outbox purge 行不含正文 (文件实读).
  F3 仓外副本状态: 本机无入口, 只报告缺口, 不判任何结果.

用法: python3 probe.py <repo> <data_dir>
"""
import ast
import json
import pathlib
import sys

repo = pathlib.Path(sys.argv[1]).resolve()
data = (repo / sys.argv[2]).resolve()
app = repo / "app.py"
fail = []


# ---- F1: purge 路径的静态断言 ----
src = app.read_text(encoding="utf-8")
tree = ast.parse(src)

imported = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imported |= {a.name.split(".")[0] for a in node.names}
    elif isinstance(node, ast.ImportFrom) and node.module:
        imported.add(node.module.split(".")[0])
net_mods = {"socket", "http", "urllib", "requests", "ftplib", "telnetlib", "smtplib", "ssl", "asyncio", "subprocess"}
bad = imported & net_mods
print(f"[F1] app.py imports = {sorted(imported)}")
if bad:
    fail.append(f"F1 失败: app.py 导入网络/子进程模块 {sorted(bad)}")
else:
    print("[F1] OK: 无网络/子进程模块导入")

purge_fn = next(
    (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "cmd_record_purge"), None
)
if purge_fn is None:
    fail.append("F1 失败: 找不到 cmd_record_purge")
else:
    called = {n.func.id for n in ast.walk(purge_fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)}
    print(f"[F1] cmd_record_purge 调用的本模块函数 = {sorted(called)}")
    allowed = {"load_records", "write_records", "log_outbox", "print", "len"}
    extra = called - allowed
    if extra:
        fail.append(f"F1 失败: purge 调用了预期外的函数 {sorted(extra)}")
    else:
        print("[F1] OK: purge 只碰本地记录文件与 outbox")
    # 确认 purge 从不读 PARTNER_URL, 也不设置 delivered=True
    seg = ast.get_source_segment(src, purge_fn)
    if "PARTNER_URL" in seg:
        fail.append("F1 失败: purge 路径读取 PARTNER_URL")
    else:
        print("[F1] OK: purge 不读 PARTNER_URL")
    if '"delivered": True' in seg or "'delivered': True" in seg:
        fail.append("F1 失败: purge 自报 delivered=True")
    else:
        print("[F1] OK: purge 未自报 delivered=True")


# ---- F2: purge 后的本地残留 ----
records = data / "records.jsonl"
outbox = data / "outbox" / "replication-log.jsonl"
print(f"[F2] records.jsonl exists={records.exists()}")
rtext = records.read_text(encoding="utf-8")
print(f"[F2] records.jsonl 内容 = {rtext!r}")
if '"r1"' in rtext or "alpha" in rtext:
    fail.append("F2 失败: records.jsonl 仍含 r1 或 alpha")
else:
    print("[F2] OK: records.jsonl 无 r1/alpha")

hit = []
for p in list(data.rglob("*")) + list((repo / "runtime").rglob("*")):
    if p.is_file():
        try:
            if b"alpha" in p.read_bytes():
                try:
                    hit.append(str(p.relative_to(repo)))
                except ValueError:
                    hit.append(str(p))
        except OSError as exc:
            hit.append(f"{p}: {exc}")
print(f"[F2] runtime/ 与 data-dir 中含 alpha 的文件 = {hit}")
if hit:
    fail.append(f"F2 失败: 本地仍存有 r1 正文: {hit}")
else:
    print("[F2] OK: 本地无 r1 正文残留")

lines = [json.loads(x) for x in outbox.read_text(encoding="utf-8").splitlines() if x]
purge_rows = [x for x in lines if x.get("id") == "r1" and x.get("action") == "purge"]
print(f"[F2] outbox 中 r1 purge 行 = {purge_rows}")
if len(purge_rows) != 1:
    fail.append(f"F2 失败: r1 purge 行数量异常 {len(purge_rows)}")
elif purge_rows[0].get("delivered") is not False:
    fail.append(f"F2 失败: purge 行 delivered 非 False: {purge_rows[0]}")
elif "text" in purge_rows[0]:
    fail.append(f"F2 失败: purge 行携带正文: {purge_rows[0]}")
else:
    print("[F2] OK: purge 行 delivered=false 且不含正文")


# ---- F3: 仓外副本可读性 ----
print("[F3] UNPROVEN: 本机没有伙伴服务地址/凭据, 也没有读取仓外存储的入口; 仓外副本是否已删除无法观测.")


print()
if fail:
    print("RESULT: FAIL")
    for item in fail:
        print(" -", item)
    sys.exit(1)
print("RESULT: PASS (F1,F2 已证; F3 未证实, 见报告)")
sys.exit(0)
