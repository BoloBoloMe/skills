"""非正式 TC: 测成品入口有没有真的走到 800 上限判定.

只在自己进程里包一层计数, 不改 src/svc 任何字节.
判断错 (计数不为 0) 就以非零退出码失败.
"""
import os
import subprocess
import sys

REPO = "/tmp/orchestra-18/drill-green"
sys.path.insert(0, os.path.join(REPO, "src"))

import svc.export as export_mod  # noqa: E402
import svc.gateway as gateway_mod  # noqa: E402
import svc.limits as limits_mod  # noqa: E402

counts = {"export.export": 0, "limits.check_limit": 0}
orig_export = export_mod.export
orig_check = limits_mod.check_limit


def counted_export(rows):
    counts["export.export"] += 1
    return orig_export(rows)


def counted_check(amount):
    counts["limits.check_limit"] += 1
    return orig_check(amount)


export_mod.export = counted_export
limits_mod.check_limit = counted_check

# 同一进程里 gateway 已 import 了 export 模块对象, 因此计数会被看见
assert gateway_mod.export is export_mod, "gateway 引用的不是被测 export 模块"

failures = []
for label, env in (("AUDIT_URL 未设置", None), ("AUDIT_URL 设为假地址", "https://audit.example.invalid")):
    if env is None:
        os.environ.pop("AUDIT_URL", None)
    else:
        os.environ["AUDIT_URL"] = env
    counts["export.export"] = 0
    counts["limits.check_limit"] = 0
    try:
        gateway_mod.request_export([("a-2", 940.0), ("a-1", 120.5)])
        outcome = "返回成功"
    except BaseException as exc:  # noqa: BLE001
        outcome = f"{type(exc).__name__}: {exc}"
    print(f"{label:<22} request_export -> {outcome}")
    print(f"{'':<22} 到达 export.export 次数={counts['export.export']}  "
          f"到达 limits.check_limit 次数={counts['limits.check_limit']}")
    if counts["export.export"] != 0:
        failures.append(f"{label}: export.export 被调用了 {counts['export.export']} 次")
    if counts["limits.check_limit"] != 0:
        failures.append(f"{label}: check_limit 被调用了 {counts['limits.check_limit']} 次")

print("\n800 上限在产品入口的拒绝次数:", counts["limits.check_limit"], "(不可达, 所以是 0)")

dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain"], capture_output=True, text=True).stdout.strip()
print("仓库工作区:", "干净" if not dirty else dirty)
if dirty:
    failures.append("仓库被改动: " + dirty)

print("=== 结果:", "全部断言通过" if not failures else f"失败: {failures}")
sys.exit(0 if not failures else 1)
