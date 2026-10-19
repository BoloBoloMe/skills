"""最小复现: 真 seed + 真导出 + 未改动的消费者. 判断不符即非零退出."""
import os
import pathlib
import subprocess
import sys

work = pathlib.Path(__file__).resolve().parents[1]
root = work / "repo"
out = work / "evidence"
out.mkdir(exist_ok=True)
assert sys.implementation.name == "cpython" and sys.version_info >= (3, 11)
sys.path.insert(0, str(root))
import amountlib

assert amountlib.VERSION == "2.4.0"
assert pathlib.Path(amountlib.__file__).resolve() == root / "amountlib/__init__.py"
assert subprocess.check_output(["node", "--version"]).strip() == b"v24.19.0"
env = os.environ | {"UV_CACHE_DIR": str(work / ".uv-cache"), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": ""}
py = ["uv", "run", "--no-project", "--no-managed-python", "--no-python-downloads", "python", "-B"]
for script in ["db/seed.py", "scripts/dump_orders.py"]:
    run = subprocess.run([*py, str(root / script)], cwd=work, env=env, capture_output=True)
    (out / ("repro-" + pathlib.Path(script).stem + ".stdout")).write_bytes(run.stdout)
    (out / ("repro-" + pathlib.Path(script).stem + ".stderr")).write_bytes(run.stderr)
    assert run.returncode == 0, run.stderr
consumer = "/tmp/orchestra-07/orders-consumer/src/run.sh"
run = subprocess.run(["bash", consumer, str(root / "var/orders.export.json")], cwd=work, env=env, capture_output=True)
(out / "repro-ledger.stdout").write_bytes(run.stdout)
(out / "repro-ledger.stderr").write_bytes(run.stderr)
(out / "repro-ledger.exitcode").write_text(str(run.returncode) + "\n")
print(f"consumer_exit_code={run.returncode}", flush=True)
sys.stdout.buffer.write(run.stdout)
sys.stdout.buffer.write(run.stderr)
sys.stdout.buffer.flush()
assert run.returncode == 1 and run.stdout == b""
assert b"TypeError: rows is not iterable" in run.stderr
assert b"ledger.js:6" in run.stderr
print("PASS: 新文件确实使旧消费者非零退出; 证明脚本自身成功退出.")
