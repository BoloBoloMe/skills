"""交付自检: 报告结构/内嵌脚本/原始证据/产品文件未变."""
import hashlib
import json
import pathlib
import re
import subprocess
import sys

assert sys.version_info >= (3, 11)
work = pathlib.Path(__file__).resolve().parents[1]
report = (work / "report.md").read_text()
assert re.findall(r"^## (.+)$", report, re.M) == [
    "1. 做了什么", "2. 关键安全事实与证据级别", "3. 风险", "4. 已排除项", "5. 合并前最便宜的复现",
]
assert re.findall(r"^### (F[1-6])[.]", report, re.M) == ["F1", "F2", "F3", "F4", "F5", "F6"]
assert "不建议按当前提交单独合入" in report
assert all(label in report for label in ["[事实", "[推断", "[未证实]"])
assert report.count("```python\n") == 1
embedded = report.split("```python\n", 1)[1].split("```", 1)[0]
assert embedded == (work / "proofs/repro_file_crash.py").read_text()
assert not any(0x3000 <= ord(c) <= 0x303F or 0xFF00 <= ord(c) <= 0xFF65 for c in report)
out = work / "evidence"
for name in ["proof-all", "search-readers", "repro"]:
    assert (out / f"{name}.exitcode").read_text() == "0\n"
assert (out / "proof-all.attempt1.exitcode").read_text() == "1\n"
assert (out / "head.file-ledger.exitcode").read_text() == "1\n"
assert (out / "head.file-ledger.stdout").read_bytes() == b""
assert "TypeError: rows is not iterable" in (out / "head.file-ledger.stderr").read_text()
for name in ["head.rows-only-ledger", "head.stdout-ledger"]:
    assert (out / f"{name}.exitcode").read_text() == "0\n"
    assert json.loads((out / f"{name}.stdout").read_text()) == {"total": None, "missing": []}
assert "ALL ASSERTIONS PASSED" in (out / "proof-all.raw.log").read_text()
manifest = json.loads((out / "source-manifest.json").read_text())
consumer = pathlib.Path("/tmp/orchestra-07/orders-consumer")
source = pathlib.Path("/tmp/orchestra-07/drill-ts003-wide")
for name, expected in manifest["files"].items():
    path = consumer / name.removeprefix("consumer/") if name.startswith("consumer/") else work / name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
for repo in [source, consumer]:
    assert subprocess.check_output(["git", "-C", str(repo), "status", "--porcelain"]) == b""
print("PASS: 5 部分/F1-F6/三种状态/最小脚本全文/ASCII 标点/证据退出码/产品文件未变.")
