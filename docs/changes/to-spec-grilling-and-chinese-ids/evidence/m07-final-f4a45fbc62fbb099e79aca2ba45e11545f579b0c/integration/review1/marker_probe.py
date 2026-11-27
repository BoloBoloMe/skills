"""标记版本兼容探测: 文档称固定 v1, 实机是否接受 vN."""
import subprocess, sys, tempfile
from pathlib import Path
REPO = Path("/home/bolo/Workspace/improve"); SK = REPO / "workflow/to-spec"
sys.path.insert(0, str(SK / "tests"))
from test_ac_draft import BASE, DRAFT
root = Path(tempfile.mkdtemp(prefix="marker-", dir="/tmp/m07-rev-imp"))
b, d, o = root / "BASE.md", root / "AC.md", root / "P.md"
b.write_text(BASE); d.write_text(DRAFT)
r = subprocess.run([sys.executable, str(SK / "ac-draft.py"), "promote", str(b), str(d), str(o)],
                   capture_output=True, text=True)
print("promote exit", r.returncode, r.stdout.strip())
text = o.read_text()
for ver in ("v1", "v2", "v9"):
    p = root / f"P-{ver}.md"
    p.write_text(text.replace("<!-- confirmed-flow: v1 -->", f"<!-- confirmed-flow: {ver} -->"))
    rr = subprocess.run([sys.executable, str(SK / "check-ac.py"), str(p)], capture_output=True, text=True)
    print(ver, "check-ac exit", rr.returncode, "|", (rr.stdout or rr.stderr).strip()[:80])
