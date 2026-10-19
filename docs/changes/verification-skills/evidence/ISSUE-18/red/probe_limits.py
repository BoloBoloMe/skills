"""证明脚本: 对比 cc8c757(基线) 与 c342c22(变更) 的 export()/check_limit 行为.

判断错时 assert 失败, 退出码非零.
只读仓库; 只在 /tmp/orchestra-18/red-exp/ 下写产物.
"""

import json
import math
import os
import subprocess
import sys

REPO = "/tmp/orchestra-18/drill"
RED = "/tmp/orchestra-18/red-exp"
BASE_REV = "cc8c757e936062e6b4a3540756eb9f805d3b5f16"
HEAD_REV = "c342c2230cbfa275941eefd5bd5f7875c86dabae"
OUT = os.path.join(RED, "out")

PROBE = r'''
import csv, json, math
from svc import limits, export

CASES = [
    ("neg_int", -1),
    ("neg_float", -0.01),
    ("zero", 0),
    ("zero_float", 0.0),
    ("min_plus", 0.01),
    ("old_ok_940", 940.0),
    ("exactly_1000", 1000.0),
    ("over_1000", 1000.01),
    ("exactly_800", 800.0),
    ("just_over_800", 800.0001),
    ("nan", float("nan")),
    ("none", None),
    ("str_num", "940.0"),
    ("bool_true", True),
]

def run(fn):
    try:
        return {"kind": "ok", "value": repr(fn())}
    except BaseException as exc:
        return {"kind": "exc", "type": type(exc).__name__, "msg": str(exc)}

result = {
    "MAX_USD": limits.MAX_USD,
    "MIN_USD": limits.MIN_USD,
    "export_module_file": export.__file__,
    "check_limit": {},
    "export_single": {},
    "export_batch_real_csv": None,
}
for label, amount in CASES:
    result["check_limit"][label] = run(lambda: limits.check_limit(amount))
    result["export_single"][label] = run(lambda: export.export([("id-" + label, amount)]))

# 真实运维 csv 的三行, 走 export() 而不是 gateway (gateway 需要审计服务)
rows = []
with open("/tmp/orchestra-18/drill/scripts/orders.csv", newline="", encoding="utf-8") as fh:
    reader = csv.reader(fh)
    next(reader)
    rows = [(r[0], float(r[1])) for r in reader]
result["rows_from_real_csv"] = [(oid, amt) for oid, amt in rows]
result["export_batch_real_csv"] = run(lambda: export.export(rows))
print(json.dumps(result, ensure_ascii=False))
'''


def git(*args):
    return subprocess.run(["git", "-C", REPO, *args], capture_output=True, text=True, check=True).stdout


def probe(tree):
    env = dict(os.environ, PYTHONPATH=os.path.join(RED, "trees", tree, "src"), PYTHONHASHSEED="0")
    proc = subprocess.run([sys.executable, "-c", PROBE], env=env, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"探针失败 tree={tree} rc={proc.returncode}\n{proc.stderr}")
    return json.loads(proc.stdout)


def main():
    assert sys.version_info[:2] == (3, 14), f"环境不符: {sys.version}"
    head = git("rev-parse", "HEAD").strip()
    assert head == HEAD_REV, f"仓库 HEAD 不是变更提交: {head}"
    assert git("rev-parse", "HEAD~0").strip() != BASE_REV

    # 树里的代码必须与 git 对象逐字节相同, 否则测的不是这两个提交
    import hashlib
    for rev, tree in ((BASE_REV, "base"), (HEAD_REV, "head")):
        for name in ("limits.py", "export.py"):
            want = git("show", f"{rev}:src/svc/{name}")
            with open(os.path.join(RED, "trees", tree, "src", "svc", name), encoding="utf-8") as fh:
                got = fh.read()
            assert got == want, f"tree {tree} {name} 与 {rev} 不一致"

    base = probe("base")
    head = probe("head")

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "probe_base.json"), "w", encoding="utf-8") as fh:
        json.dump(base, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "probe_head.json"), "w", encoding="utf-8") as fh:
        json.dump(head, fh, ensure_ascii=False, indent=1)

    print("python", sys.version.split()[0], "| base", BASE_REV[:7], "| head", HEAD_REV[:7])
    print(f"{'case':16} {'check_limit base->head':44} {'export base->head'}")
    for label in base["check_limit"]:
        def fmt(r):
            if r["kind"] == "exc":
                return r["type"] + ":" + r["msg"]
            return "return=" + r["value"]
        print(f"{label:16} {fmt(base['check_limit'][label]):20} -> {fmt(head['check_limit'][label]):20} "
              f"{fmt(base['export_single'][label]):24} -> {fmt(head['export_single'][label])}")

    assert base["MAX_USD"] == 1000 and head["MAX_USD"] == 800, "上限常量没按提交变化"

    # 事实 1: 真实运维 csv 的行 (含 940.0) 在基线可导出, 在变更后整批失败
    print("\nreal csv rows:", base["rows_from_real_csv"])
    print("base export_batch_real_csv:", base["export_batch_real_csv"])
    print("head export_batch_real_csv:", head["export_batch_real_csv"])
    assert base["export_batch_real_csv"]["kind"] == "ok", "基线本应能导出真实 csv"
    assert "a-2" in base["export_batch_real_csv"]["value"]
    assert head["export_batch_real_csv"]["kind"] == "exc", "变更后本应整批失败"
    assert head["export_batch_real_csv"]["msg"].endswith("a-2"), "失败行不是 a-2"

    # 事实 2: 800 < amount <= 1000 的行从通过变成失败; 800 本身仍通过
    for label in ("old_ok_940", "exactly_1000"):
        assert base["export_single"][label]["kind"] == "ok", f"基线 {label} 应通过"
        assert head["export_single"][label]["kind"] == "exc", f"变更后 {label} 应失败"
    assert head["export_single"]["exactly_800"]["kind"] == "ok", "800 应通过"
    assert head["export_single"]["just_over_800"]["kind"] == "exc", "800.0001 应失败"

    # 事实 3: 负数在基线已被拒 (同一 ValueError), 变更只改了异常消息
    for label in ("neg_int", "neg_float"):
        assert base["export_single"][label]["kind"] == "exc"
        assert base["export_single"][label]["type"] == "ValueError"
        assert head["export_single"][label]["type"] == "ValueError"
    assert "金额越界" in base["export_single"]["neg_int"]["msg"], base["export_single"]["neg_int"]
    assert "金额为负" in head["export_single"]["neg_int"]["msg"], head["export_single"]["neg_int"]

    # 事实 4: 0 在基线与变更后都被拒 (MIN_USD < amount 是严格大于), 不是本次变更造成的
    assert base["export_single"]["zero"]["kind"] == "exc"
    assert head["export_single"]["zero"]["kind"] == "exc"
    assert "金额越界" in head["export_single"]["zero"]["msg"]

    # 事实 5: None 输入的异常类型从 ValueError 变成 TypeError
    assert base["export_single"]["none"]["type"] == "ValueError", base["export_single"]["none"]
    assert head["export_single"]["none"]["type"] == "TypeError", head["export_single"]["none"]
    assert base["check_limit"]["none"]["value"] == "False"

    # 事实 6: nan 两版都拒, 无变化
    assert base["export_single"]["nan"]["kind"] == "exc"
    assert head["export_single"]["nan"]["kind"] == "exc"

    # 事实 7: config/app.toml 里的 enforce_limits / max_rows 没有任何代码读取
    src_hits = subprocess.run(
        ["grep", "-rn", "-e", "app.toml", "-e", "toml", "-e", "enforce_limits", "-e", "max_rows",
         os.path.join(REPO, "src"), os.path.join(REPO, "scripts")],
        capture_output=True, text=True)
    assert src_hits.returncode == 1 and src_hits.stdout == "", f"配置被读取了: {src_hits.stdout}"

    print("\nALL ASSERTIONS PASSED")


if __name__ == "__main__":
    main()
