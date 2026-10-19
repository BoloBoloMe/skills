"""独立调查入口. 仅在 router-a 写 DB, 导出文件和原始输出.

运行: UV_CACHE_DIR="$PWD/.uv-cache" uv run --no-project --no-managed-python \
    --no-python-downloads python -B proofs/prove_all.py
断言不符时非零退出. 消费者预期失败的子进程退出码会单独保留.
"""
import hashlib
import json
import os
import pathlib
import shlex
import subprocess
import sys

WORK = pathlib.Path(__file__).resolve().parents[1]
SOURCE = pathlib.Path("/tmp/orchestra-07/drill-ts003-wide")
CONSUMER = pathlib.Path("/tmp/orchestra-07/orders-consumer")
OUT = WORK / "evidence"
OUT.mkdir(exist_ok=True)
assert sys.implementation.name == "cpython"
assert sys.version_info >= (3, 11)
assert WORK == pathlib.Path("/tmp/orchestra-07/out/ts003-wide-work/router-a")
ENV = os.environ | {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": "",
    "UV_CACHE_DIR": str(WORK / ".uv-cache"),
    "UV_PYTHON_DOWNLOADS": "never",
}
PY = ["uv", "run", "--no-project", "--no-managed-python", "--no-python-downloads", "python", "-B"]


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], env=ENV)


def run(name, command, expected_rc=0):
    command = list(map(str, command))
    print(f"\n$ {shlex.join(command)}", flush=True)
    result = subprocess.run(command, cwd=WORK, env=ENV, capture_output=True, check=False)
    (OUT / f"{name}.stdout").write_bytes(result.stdout)
    (OUT / f"{name}.stderr").write_bytes(result.stderr)
    (OUT / f"{name}.exitcode").write_text(f"{result.returncode}\n")
    (OUT / f"{name}.command.json").write_text(json.dumps(command, ensure_ascii=False) + "\n")
    print(f"exit_code={result.returncode}", flush=True)
    if result.stdout:
        print("--- stdout ---", flush=True)
        print(result.stdout.decode(), end="", flush=True)
    if result.stderr:
        print("--- stderr ---", flush=True)
        print(result.stderr.decode(), end="", flush=True)
    assert result.returncode == expected_rc, (name, result.returncode, expected_rc)
    return result


head = git(SOURCE, "rev-parse", "HEAD").decode().strip()
base = git(SOURCE, "rev-parse", "HEAD~1").decode().strip()
assert head == "e807b06ca2a9cb88413390a298f55b84d3ac7869"
assert base == "04ddf931fd161baea18b0a0d315da8d41eb7cf7e"
assert git(SOURCE, "status", "--porcelain") == b""
# 消费者版本由 package.json 断言, 同时记录实际 HEAD 和所有已跟踪文件的校验值.
assert git(CONSUMER, "status", "--porcelain") == b""
consumer_commit = git(CONSUMER, "rev-parse", "HEAD").decode().strip()
assert consumer_commit == "a47893d0dea16e39197603ee28b7b8b467efbbee"
pkg = json.loads((CONSUMER / "package.json").read_text())
assert (pkg["name"], pkg["version"], pkg["type"]) == ("orders-consumer", "0.9.2", "module")
manifest = {"source_head": head, "source_base": base, "consumer_head": consumer_commit, "files": {}}
for name, commit in [("repo", head), ("base", base)]:
    paths = git(SOURCE, "ls-tree", "-r", "--name-only", commit).decode().splitlines()
    assert len(paths) == 13
    for path in paths:
        expected = git(SOURCE, "show", f"{commit}:{path}")
        actual = (WORK / name / path).read_bytes()
        assert actual == expected, f"{name}/{path} 与提交不符"
        manifest["files"][f"{name}/{path}"] = hashlib.sha256(actual).hexdigest()
for path in git(CONSUMER, "ls-files").decode().splitlines():
    actual = (CONSUMER / path).read_bytes()
    assert actual == git(CONSUMER, "show", f"HEAD:{path}")
    manifest["files"][f"consumer/{path}"] = hashlib.sha256(actual).hexdigest()
for path in ["amountlib/core.py", "amountlib/legacy.py", "amountlib/__init__.py", "db/seed.py", "db/schema.sql", "pyproject.toml"]:
    assert (WORK / "repo" / path).read_bytes() == (WORK / "base" / path).read_bytes()
base_orders = (WORK / "base/app/orders.py").read_text()
head_orders = (WORK / "repo/app/orders.py").read_text()
assert base_orders.replace('"amount": None', '"amount_value": None') == head_orders
base_dump = (WORK / "base/scripts/dump_orders.py").read_text()
head_dump = (WORK / "repo/scripts/dump_orders.py").read_text()
assert base_dump.replace(
    'OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2))',
    'OUT.write_text(json.dumps({"schema": "orders-export/2", "rows": rows}, ensure_ascii=False, indent=2))',
) == head_dump
sys.path.insert(0, str(WORK / "repo"))
import amountlib

assert amountlib.VERSION == "2.4.0"
assert pathlib.Path(amountlib.__file__).resolve() == WORK / "repo/amountlib/__init__.py"
node_version = run("node-version", ["node", "--version"]).stdout.decode().strip()
assert node_version == "v24.19.0"
manifest["python"] = sys.version
manifest["node"] = node_version
(OUT / "source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("snapshot source/consumer source/runtime assertions: PASS", flush=True)

rows_by_snapshot = {}
for name in ["base", "repo"]:
    label = "head" if name == "repo" else "base"
    root = WORK / name
    run(f"{label}.seed", [*PY, root / "db/seed.py"])
    dump = run(f"{label}.dump", [*PY, root / "scripts/dump_orders.py"])
    document = json.loads((root / "var/orders.export.json").read_text())
    stdout_rows = json.loads(dump.stdout)
    if name == "base":
        assert isinstance(document, list)
        assert document == stdout_rows
        rows = document
    else:
        assert set(document) == {"schema", "rows"}
        assert document["schema"] == "orders-export/2"
        assert isinstance(document["rows"], list)
        assert document["rows"] == stdout_rows
        assert document != stdout_rows
        rows = document["rows"]
    key = "amount_value" if name == "repo" else "amount"
    assert rows == [{"id": 1, key: "12.50"}, {"id": 2, key: "9.99"}, {"id": 3, key: None}]
    rows_by_snapshot[label] = rows
    (OUT / f"{label}.file.json").write_bytes((root / "var/orders.export.json").read_bytes())
    run(f"{label}.amounts", [*PY, WORK / "proofs/check_amounts.py", root])
assert [{"id": r["id"], "value": r["amount"]} for r in rows_by_snapshot["base"]] == [
    {"id": r["id"], "value": r["amount_value"]} for r in rows_by_snapshot["head"]
]

ledger = CONSUMER / "src/run.sh"
base_ledger = run("base.file-ledger", ["bash", ledger, OUT / "base.file.json"])
# 旧账本用二进制浮点数相加, 原始结果是 22.490000000000002, 不是精确小数.
assert json.loads(base_ledger.stdout) == {"total": 12.5 + 9.99, "missing": [3]}
head_ledger = run("head.file-ledger", ["bash", ledger, OUT / "head.file.json"], expected_rc=1)
assert b"TypeError: rows is not iterable" in head_ledger.stderr
assert b"ledger.js:6" in head_ledger.stderr
assert head_ledger.stdout == b""
rows_path = OUT / "head.rows-only.json"
rows_path.write_text(json.dumps(rows_by_snapshot["head"]) + "\n")
partial_ledger = run("head.rows-only-ledger", ["bash", ledger, rows_path])
assert json.loads(partial_ledger.stdout) == {"total": None, "missing": []}
run("head.rows-semantics", ["node", WORK / "proofs/rows_only.mjs", OUT / "head.file.json"])
stdout_base = run("base.stdout-ledger", ["bash", ledger, OUT / "base.dump.stdout"])
assert json.loads(stdout_base.stdout) == {"total": 12.5 + 9.99, "missing": [3]}
stdout_head = run("head.stdout-ledger", ["bash", ledger, OUT / "head.dump.stdout"])
assert json.loads(stdout_head.stdout) == {"total": None, "missing": []}
assert stdout_head.stdout == partial_ledger.stdout
assert git(SOURCE, "status", "--porcelain") == b""
assert git(CONSUMER, "status", "--porcelain") == b""
for key, expected_hash in manifest["files"].items():
    path = CONSUMER / key.removeprefix("consumer/") if key.startswith("consumer/") else WORK / key
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected_hash, f"调查改写了 {key}"
print("\nALL ASSERTIONS PASSED: F1/F2/F3/F4/F6 本地证明通过; 生产范围未证明.", flush=True)
