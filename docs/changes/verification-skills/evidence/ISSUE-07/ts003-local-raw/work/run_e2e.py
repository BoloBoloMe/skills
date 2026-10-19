"""跑真实入口, 比较 HEAD~1 与 HEAD 的导出结果.

步骤: 用 git worktree 导出两个版本到临时目录, 各自 seed 出 SQLite, 跑
scripts/dump_orders.py (应用真实入口), 再跑消费仓库的 src/run.sh, 比较输出.
失败条件 (非零退出): 两版导出 JSON 或消费端汇总不一致.
"""
import json
import pathlib
import shutil
import subprocess
import sys

REPO = pathlib.Path("/tmp/orchestra-07/drill-ts003-local")
WORK = pathlib.Path("/tmp/orchestra-07/out/ts003-local-work/trees")
CONSUMER = pathlib.Path("/tmp/orchestra-07/orders-consumer/src/run.sh")


def export(rev, dest):
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    tar = subprocess.run(["git", "-C", str(REPO), "archive", rev], stdout=subprocess.PIPE, check=True)
    subprocess.run(["tar", "-x", "-C", str(dest)], input=tar.stdout, check=True)


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    print(f"$ ({cwd.name}) {' '.join(cmd)}  -> rc={r.returncode}")
    if r.stdout:
        print(r.stdout.rstrip())
    if r.stderr:
        print("STDERR:", r.stderr.rstrip())
    assert r.returncode == 0, f"命令失败: {cmd}"
    return r


def main():
    out = {}
    for rev, name in (("HEAD~1", "base"), ("HEAD", "head")):
        dest = WORK / name
        export(rev, dest)
        run(["uv", "run", "python", "db/seed.py"], dest)
        run(["uv", "run", "python", "scripts/dump_orders.py"], dest)
        exported = (dest / "var" / "orders.export.json").read_text()
        consumer = run(["bash", str(CONSUMER), str(dest / "var" / "orders.export.json")], dest)
        out[name] = {"export": exported, "consumer": consumer.stdout}

    same_export = out["base"]["export"] == out["head"]["export"]
    same_consumer = out["base"]["consumer"] == out["head"]["consumer"]
    print(f"\n导出 JSON 相同: {same_export}")
    print(f"消费端汇总相同: {same_consumer}")
    print(f"HEAD 消费端汇总: {json.dumps(json.loads(out['head']['consumer']), ensure_ascii=False)}")
    assert same_export, "两版导出不同, 需要人工评估"
    assert same_consumer, "两版消费端汇总不同, 需要人工评估"
    print("PASS: 真实入口的输出与下游消费结果在本次变更前后逐字节相同")


if __name__ == "__main__":
    main()
