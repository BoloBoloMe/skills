"""按 to-spec 新版 SKILL.md 第 3 节命令清单实跑 (非正式 TC, 全部在 /tmp)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path("/home/bolo/Workspace/improve")
SK = REPO / "workflow/to-spec"
sys.path.insert(0, str(SK / "tests"))
from test_ac_draft import BASE, DRAFT  # noqa: E402

root = Path(tempfile.mkdtemp(prefix="recipe-", dir="/tmp/m07-rev-imp"))
prod_base = root / "PRODUCT.base.md"
draft = root / "AC.md"
tech_draft = root / "TECHNICAL.md"
outdir = root / "prod"
outdir.mkdir()
prod_base.write_text(BASE, encoding="utf-8")
draft.write_text(DRAFT, encoding="utf-8")
tech_draft.write_bytes((REPO / "docs/changes/to-spec-grilling-and-chinese-ids/TECHNICAL.md").read_bytes())


def run(args, **kw):
    argv = [str(a) for a in args]
    if argv[0].endswith(".py"):
        argv = [sys.executable, *argv]
    r = subprocess.run(argv, capture_output=True, text=True, timeout=60, **kw)
    print("$", " ".join(Path(str(a)).name if "/" in str(a) else str(a) for a in args))
    print("  exit", r.returncode, "|", (r.stdout or r.stderr).strip().splitlines()[:2])
    return r


ok = True


def need(r, code, label):
    global ok
    if r.returncode != code:
        ok = False
        print("  >>> UNEXPECTED", label)


need(run([SK / "check-ac.py", prod_base, "--draft", draft]), 0, "draft check")
need(run([SK / "check-tech.py", tech_draft]), 0, "tech draft check")
r = run([SK / "ac-draft.py", "promote", prod_base, draft, outdir / "PRODUCT.md"])
need(r, 0, "promote")
try:
    need_js = json.loads(r.stdout)
    if not need_js.get("success"):
        ok = False
        print("  >>> promote success false")
except Exception:
    ok = False
    print("  >>> promote stdout not JSON")
need(run(["cp", "--", tech_draft, outdir / "TECHNICAL.md"]), 0, "cp")
need(run(["cmp", "--", tech_draft, outdir / "TECHNICAL.md"]), 0, "cmp")
need(run([SK / "check-ac.py", outdir / "PRODUCT.md"]), 0, "formal product check")
need(run([SK / "check-tech.py", outdir / "TECHNICAL.md"]), 0, "formal tech check")
print("RECIPE OK" if ok else "RECIPE FAILED")
sys.exit(0 if ok else 1)