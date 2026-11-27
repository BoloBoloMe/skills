"""m07-rev-imp 一次性探测: ac-draft.py / check-ac.py 契约与产物跨版本兼容.

非正式 TC. 只读仓库, 全部写入放 /tmp. 每个断言错即非零退出.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path("/home/bolo/Workspace/improve")
NEW = REPO / "workflow/to-spec"
OLD = Path("/tmp/m07-rev-imp/old")
sys.path.insert(0, str(NEW / "tests"))
from test_ac_draft import BASE, DRAFT  # noqa: E402  (新旧版 tests 常量相同)

failures = []


def run(args, **kw):
    return subprocess.run([sys.executable, *map(str, args)], capture_output=True, text=True, timeout=30, **kw)


def check(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label + ((" | " + detail) if detail else ""))
    if not cond:
        failures.append(label)


print("== 环境 ==")
print("python", sys.version.split()[0])
print("repo HEAD", run(["git", "-C", str(REPO), "rev-parse", "HEAD"]).stdout.strip())
print("new helper", NEW / "ac-draft.py", (NEW / "ac-draft.py").stat().st_mtime)
print("old helper", OLD / "ac-draft.py", "(取自 9e8dd1df)")

root = Path(tempfile.mkdtemp(prefix="m07probe-", dir="/tmp/m07-rev-imp"))
base, draft, out = root / "PRODUCT.base.md", root / "AC.md", root / "PRODUCT.md"
base.write_text(BASE, encoding="utf-8")
draft.write_text(DRAFT, encoding="utf-8")

print("\n== A. 新 preview 输出字段 ==")
r = run([NEW / "ac-draft.py", "preview", base, draft])
js = json.loads(r.stdout)
print("exit", r.returncode, "keys", sorted(js))
check("A1 preview 退出 0", r.returncode == 0, r.stdout + r.stderr)
check("A2 preview JSON 无 review_id", "review_id" not in js)
check("A3 preview 含 preview/draft", {"preview", "draft"} <= set(js))
page = Path(js["preview"]).read_text(encoding="utf-8")
check("A4 页面无审阅版本, 有仅供选看", ("审阅版本" not in page) and ("页面仅供选看" in page))

print("\n== B. 旧 preview 仍返回 review_id (已安装旧版) ==")
r = run([OLD / "ac-draft.py", "preview", base, draft])
ojs = json.loads(r.stdout)
print("exit", r.returncode, "keys", sorted(ojs))
check("B1 旧版 preview 有 review_id", "review_id" in ojs, str(sorted(ojs)))

print("\n== C. stale 保护: 预览后改草稿再转正 ==")
draft.write_text(DRAFT.replace("1 条", "2 条"), encoding="utf-8")
out_new = root / "NEW-PRODUCT.md"
r = run([NEW / "ac-draft.py", "promote", base, draft, out_new])
print("new exit", r.returncode, r.stdout.strip())
check("C1 新版不校验旧预览, 改动后转正成功 (设计已取消该保护)", r.returncode == 0 and out_new.exists())
out_old = root / "OLD-STALE.md"
r = run([OLD / "ac-draft.py", "promote", base, draft, out_old, "--review", ojs["review_id"]])
print("old exit", r.returncode, r.stdout.strip()[:200])
check("C2 旧版改草稿后拒绝转正 (旧保护存在)", r.returncode == 2)
check("C3 旧版拒绝时未写正式文件", not out_old.exists())
draft.write_text(DRAFT, encoding="utf-8")
out_old2 = root / "OLD-OK.md"
r = run([OLD / "ac-draft.py", "promote", base, draft, out_old2, "--review", ojs["review_id"]])
check("C4 旧版字节复原后可转正", r.returncode == 0, r.stdout.strip()[:120])

print("\n== D. --review 参数去处 ==")
out_d = root / "D-PRODUCT.md"
r = run([NEW / "ac-draft.py", "promote", base, draft, out_d, "--review", "x"])
print("exit", r.returncode, "stderr", r.stderr.strip().splitlines()[-1])
check("D1 新版带 --review 退出 2", r.returncode == 2)
check("D2 报 unrecognized arguments", "unrecognized arguments" in r.stderr)
check("D3 未写正式文件", not out_d.exists())

print("\n== E. 产物跨版本兼容 ==")
r = run([NEW / "ac-draft.py", "promote", base, draft, out])
check("E1 新版转正成功", r.returncode == 0, r.stdout + r.stderr)
check("E2 新版产物含固定 v1 标记", "<!-- confirmed-flow: v1 -->" in out.read_text(encoding="utf-8"))
r = run([OLD / "check-ac.py", out])
print("old check exit", r.returncode, r.stderr.strip()[:120])
check("E3 旧 check-ac 仍接受新版产物", r.returncode == 0)
r = run([NEW / "check-ac.py", out])
check("E4 新 check-ac 接受新版产物", r.returncode == 0, r.stderr.strip()[:120])
oldout = root / "OLD-PRODUCT.md"
r = run([OLD / "ac-draft.py", "promote", base, draft, oldout, "--review", ojs["review_id"]])
check("E5 旧版可生成产物", r.returncode == 0, r.stdout + r.stderr)
r = run([NEW / "check-ac.py", oldout])
check("E6 新 check-ac 接受旧版产物 (v1 标记兼容)", r.returncode == 0, r.stderr.strip()[:200])

print("\n== F. check-ac 错误文案变化 (缺标记) ==")
nomark = root / "NOMARK.md"
nomark.write_text(BASE.replace("待确认, 此处暂不写入正式用例.", DRAFT), encoding="utf-8")
rn = run([NEW / "check-ac.py", nomark])
ro = run([OLD / "check-ac.py", nomark])
print("new:", rn.returncode, rn.stderr.strip().splitlines()[0] if rn.stderr.strip() else rn.stdout.strip())
print("old:", ro.returncode, ro.stderr.strip().splitlines()[0] if ro.stderr.strip() else ro.stdout.strip())
check("F1 退出码同为 2", rn.returncode == ro.returncode == 2)
check("F2 文案确有变化", rn.stderr != ro.stderr)

print("\n== G. 草稿带标记时的报错先后变化 ==")
mk = root / "MARKED.md"
mk.write_text("<!-- confirmed-flow: v1 -->\n" + DRAFT + "## 多余节\n", encoding="utf-8")
r = run([NEW / "ac-draft.py", "preview", base, mk])
print("new exit", r.returncode, r.stdout.strip())
check("G1 新版先报标记问题", "草稿不携带确认标记" in r.stdout)
r = run([OLD / "ac-draft.py", "preview", base, mk])
print("old exit", r.returncode, (r.stdout or r.stderr).strip()[:120])
check("G2 旧版先报围栏外的多余内容", "草稿只能包含一个完整的 gherkin 代码块" in (r.stdout + r.stderr))
check("G3 退出码同为 2", r.returncode == 2)

print("\n== H. 无 mock 后仓库内是否仍覆盖转正过程保护 ==")
tests = (NEW / "tests/test_ac_draft.py").read_text(encoding="utf-8")
for needle, label in (("输入在转正过程中已变化", "输入改动中止"),
                      ("正式文件在转正过程中已变化", "正式文件改动中止"),
                      ("validate_product", "正式复检失败路径")):
    check("H " + label + " 在仓库测试中被引用", needle in tests)

print("\n== 结果 ==")
print("failures:", failures)
sys.exit(1 if failures else 0)