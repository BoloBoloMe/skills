"""非正式 TC: 对比 5d83230 前后 svc.export / svc.limits 的行为差异.

判断错就以非零退出码失败. 用法:
  uv run python /tmp/orchestra-18/green-exp/probe_export_change.py
"""
import csv
import hashlib
import importlib
import io
import os
import subprocess
import sys

REPO = "/tmp/orchestra-18/drill-green"
EXP = "/tmp/orchestra-18/green-exp"
OLD = os.path.join(EXP, "out/trees/old")
NEW = os.path.join(EXP, "out/trees/new")
WANT_COMMIT = "5d832302339a7ae5db7cbe9a7c4c05439bceeaed"

failures = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("  | " + detail if detail else ""))
    if not cond:
        failures.append(name)


def load(root):
    """按给定目录加载独立的 svc 包, 互不干扰."""
    for mod in [m for m in sys.modules if m == "svc" or m.startswith("svc.")]:
        del sys.modules[mod]
    sys.path.insert(0, root)
    try:
        pkg = importlib.import_module("svc")
        limits = importlib.import_module("svc.limits")
        export = importlib.import_module("svc.export")
    finally:
        sys.path.remove(root)
    assert pkg.__file__.startswith(root), pkg.__file__
    return limits, export


def sha(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def outcome(export_mod, rows):
    """返回 ('ok', csv 文本) 或 ('raise', 异常类型, 消息)."""
    try:
        return ("ok", export_mod.export(rows))
    except BaseException as exc:  # noqa: BLE001
        return ("raise", type(exc).__name__, str(exc))


# --- 0. 环境与目标身份 -------------------------------------------------------
head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
print("python:", sys.version.replace("\n", " "), "| executable:", sys.executable)
print("repo HEAD:", head, "| 工作区:", "干净" if not dirty else "有改动: " + dirty)
check("运行环境是 CPython 3.14", sys.version_info[:2] == (3, 14), sys.version.split()[0])
check("被测仓库停在本次变更提交", head == WANT_COMMIT, head)
check("仓库工作区干净 (未改产品源码)", not dirty, dirty)
for f in ("limits.py", "export.py"):
    same = sha(os.path.join(REPO, "src/svc", f)) == sha(os.path.join(NEW, "svc", f))
    check(f"被加载的新代码与仓库同字节: {f}", same)

old_limits, old_export = load(OLD)
old_max, old_ver = old_limits.MAX_USD, old_limits.check_limit
new_limits, new_export = load(NEW)
new_max, new_ver = new_limits.MAX_USD, new_limits.check_limit
check("旧树 MAX_USD == 1000", old_max == 1000, str(old_max))
check("新树 MAX_USD == 800", new_max == 900, str(new_max))
print("旧 check_limit 源码对象:", old_ver.__code__.co_filename, "| 新:", new_ver.__code__.co_filename)
check("旧树来自基线提交 (路径在 out/trees/old)", old_limits.__file__.startswith(OLD), old_limits.__file__)
check("新树来自仓库 (路径在 out/trees/new)", new_limits.__file__.startswith(NEW), new_limits.__file__)

# --- 1. 负数: 新旧是否做同一个接受/拒绝决定 ---------------------------------
print("\n--- 用例矩阵 (单行) ---")
cases = [
    ("负数 -1", [("o", -1)]),
    ("负数 -0.01", [("o", -0.01)]),
    ("负数 -1e9", [("o", -1e9)]),
    ("零 0", [("o", 0)]),
    ("零 -0.0", [("o", -0.0)]),
    ("正 0.01", [("o", 0.01)]),
    ("边界 800", [("o", 800)]),
    ("边界 800.0001", [("o", 800.0001)]),
    ("中间 940", [("o", 940)]),
    ("旧上界 1000", [("o", 1000)]),
    ("超旧上界 1000.01", [("o", 1000.01)]),
    ("nan", [("o", float("nan"))]),
    ("inf", [("o", float("inf"))]),
    ("None", [("o", None)]),
    ("字符串 '900'", [("o", "900")]),
]
decisions = {}
for label, rows in cases:
    o, n = outcome(old_export, rows), outcome(new_export, rows)
    decisions[label] = (o, n)
    print(f"{label:<16} 旧={o[0]}:{o[1:] if o[0]=='raise' else 'ok'}  新={n[0]}:{n[1:] if n[0]=='raise' else 'ok'}")

numeric_negatives = [lbl for lbl, rows in cases if lbl.startswith("负数")]
for lbl in numeric_negatives:
    o, n = decisions[lbl]
    check(f"旧版已拒绝负数 ({lbl})", o[0] == "raise" and o[1] == "ValueError", str(o))
    check(f"新版也拒绝负数 ({lbl})", n[0] == "raise" and n[1] == "ValueError", str(n))
    check(f"负数判定未变, 只是异常消息变了 ({lbl})", o[1] == n[1] == "ValueError" and o[2] != n[2], f"{o[2]} -> {n[2]}")

same_decision = all(
    (decisions[l][0][0] == "ok") == (decisions[l][1][0] == "ok")
    for l, _ in cases
    if l not in ("中间 940", "旧上界 1000", "边界 800.0001")
)
check("除 800~1000 区间与 None 外, 其余输入接受/拒绝决定不变", same_decision)

# --- 2. None: 异常类型改变 ---------------------------------------------------
o, n = decisions["None"]
check("旧版把 None 当越界, 抛 ValueError", o[0] == "raise" and o[1] == "ValueError", str(o))
check("新版对 None 抛 TypeError (非 ValueError)", n[0] == "raise" and n[1] == "TypeError", str(n))

# --- 3. 边界移动 -------------------------------------------------------------
check("新版接受 800", decisions["边界 800"][1][0] == "ok", str(decisions["边界 800"][1]))
check("新版拒绝 800.0001", decisions["边界 800.0001"][1][0] == "raise", str(decisions["边界 800.0001"][1]))
check("旧版接受 940, 新版拒绝", decisions["中间 940"][0][0] == "ok" and decisions["中间 940"][1][0] == "raise")
check("旧版接受 1000, 新版拒绝", decisions["旧上界 1000"][0][0] == "ok" and decisions["旧上界 1000"][1][0] == "raise")

# --- 4. 仓库自带数据 scripts/orders.csv -------------------------------------
csv_path = os.path.join(REPO, "scripts/orders.csv")
with open(csv_path, newline="", encoding="utf-8") as fh:
    reader = csv.reader(fh)
    header = next(reader)
    rows = [(r[0], float(r[1])) for r in reader]
print("\n--- 仓库自带数据", csv_path, "---")
print("表头:", header, "| 行:", rows)
over = [r for r in rows if r[1] > 800]
check("仓库自带数据里确实有超过 800 的行", bool(over), str(over))
o = outcome(old_export, rows)
n = outcome(new_export, rows)
print("旧版导出结果:", o[0], "| 数据行数:", o[1].count("\n") - 2 if o[0] == "ok" else None)
print("新版导出结果:", n)
check("旧版能导出这份文件", o[0] == "ok", str(o))
check("新版对这份文件整体失败", n[0] == "raise" and n[1] == "ValueError", str(n))
check("失败点在 940.0 那一行", n[0] == "raise" and "a-2" in n[2], str(n))
if n[0] == "ok":
    check("新版不会静默丢行", n[1].count("\n") == o[1].count("\n"))
else:
    losing = [r for r in rows if r[1] <= 800]
    print("连累的合规行:", losing)
    check("整批拒绝会连累 <=800 的合规行", len(losing) + len(over) == len(rows) and bool(losing))

# 单行 940 也失败, 证明不是位置问题
check("单行 940 新版同样拒绝", outcome(new_export, [("a-2", 940.0)])[0] == "raise")
check("合规单行 120.5 新版仍可导出", outcome(new_export, [("a-1", 120.5)])[0] == "ok")

# --- 5. check_limit 自身语义 -------------------------------------------------
print("\n--- check_limit 直接调用 ---")
for v in (-1, 0, 799.99, 800, 800.5, 940, 1000, None):
    print(f"check_limit({v!r}) 旧={old_limits.check_limit(v)} 新={new_limits.check_limit(v)}")
check("旧 check_limit(-1) 已是 False (负数上一版就被拒)", old_limits.check_limit(-1) is False)
check("新 check_limit(-1) 仍 False", new_limits.check_limit(-1) is False)
check("check_limit(None) 新旧都返回 False", old_limits.check_limit(None) is False and new_limits.check_limit(None) is False)

print("\n=== 结果:", "全部断言通过" if not failures else f"{len(failures)} 条断言失败: {failures}")
sys.exit(0 if not failures else 1)
