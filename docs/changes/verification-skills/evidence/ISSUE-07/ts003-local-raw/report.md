# blast-radius: 2b905d2 (clamp_qty upper 99 -> 50)

调查方式: 单路, 本会话自己做 (调用方指定不开其他模型会话).

## 结论 (先看这段)

- 这次变更**不改变任何运行时输出**. `clamp_qty` 在本仓库和已知消费仓库里零调用者, `app/clamp.py` 从未被任何模块导入.
- 真实入口 `scripts/dump_orders.py` 加下游 Node 消费端, 变更前后输出逐字节相同 (实跑过).
- 合入风险低. 但要清楚: 这个提交也**没有真的限制下单数量**, 因为它调用的地方根本不存在. 如果合入动机是"把大单卡在 50", 现在等于没做.
- 事实来源限制: remote 是本地路径, 没有 PR / issue 可读, 提交动机未知.

## 1. 做了什么

变更本身 (`git show 2b905d2`): 只剩一行, `app/clamp.py:4` 默认参数 `upper=99` -> `upper=50`.

历史定位:

- `git blame -L 1,6 -- app/clamp.py`: 第 4 行来自 2b905d2, 其余来自基线 011ec25.
- `git log --follow --oneline -- app/clamp.py`: 只有 011ec25, 2b905d2 两个提交.
- `git log --all --oneline -S"clamp_qty"`: 只有基线上一次"新增". 也就是说这个符号从引入到现在, 没有任何"新增调用"的提交.
- `git log --oneline origin/master..master`: 只有 2b905d2, 尚未推送.
- `git remote -v`: `origin /tmp/orchestra-07/payout-service` (本地路径), 取不到 PR 正文与讨论. **来源限制**: 提交动机 / 需求背景未知.

读过的位置: `app/clamp.py`, `app/orders.py`, `app/legacy_sync.py`, `app/__init__.py` (空), `amountlib/{__init__,core,legacy}.py`, `db/schema.sql`, `db/seed.py`, `scripts/dump_orders.py`, `README.md`, `pyproject.toml`, `.gitignore`, `db/seed.py` 的样例行; 消费仓库 `/tmp/orchestra-07/orders-consumer/{README.md,package.json,src/run.sh,src/ledger.js}`.

跑过的命令: 见附录脚本, 在 `/tmp/orchestra-07/out/ts003-local-work/` 下运行 (仓库外的临时目录, 未改本仓库任何文件; `git status --porcelain` 仍为空).

没覆盖到的范围:

- 生产 SQLite 里的真实 payload 内容 (本地只有 `db/seed.py` 的 3 行样例; 没有 `var/orders.db`).
- `app/legacy_sync.py` 的归档链路: 本地不可跑 (缺 `ARCHIVE_TOKEN` 与生产网内服务), 只做了静态导入关系检查.
- 本机两个仓库之外是否还有 importer, 没有依据可查 (缺部署 / 依赖方清单).
- 其他分支与 tag: 仓库只有 `master` 与 `origin/master`.

## 2. 关键安全事实与证据级别

证据级别: 2 = 指到真实 file:line, 3 = 走查证明坏路径到不了, 4 = 实际跑过真实代码, 5 = 在生产里复现.

**F1. `clamp_qty` 没有任何调用者. 级别 3 (附带跑过的扫描脚本).**
`grep -rn clamp` 全仓只命中定义处; AST 扫描 (抓 import / 属性访问 / 名字) 覆盖仓库与消费仓库共 18 个文件, 定义文件之外 0 命中; `app/__init__.py` 为空 (无 re-export); 全仓无 `getattr` / `importlib` / `__import__` / `entry_points` 动态取用; `pyproject.toml` 无依赖和 CLI 入口.
停下理由: 覆盖不到仓库外的 importer, 见 R3.

**F2. 真实链路的输出在变更前后完全相同. 级别 4.**
`run_e2e.py` 用 `git archive` 导出 `HEAD~1` 与 `HEAD` 两棵树, 各自 `db/seed.py` 建库, 跑真实入口 `scripts/dump_orders.py`, 再把导出的 JSON 喂给消费仓库真实的 `src/run.sh` (node `ledger.js`). 两边导出与汇总完全相同.

**F3. 唯一的行为差异: 直接调用且不传 `upper` 时, 输入 >= 51 的结果变小; 显式传 `upper` 时完全不变. 级别 4.**
`prove_window.py` 实测: 输入 0/1/50/1000 等边界, 51 起开始出现差异 (51->50, 99->99 变 50, 1000->99 变 50), `clamp_qty(99, upper=99)` 两版都是 99.

**F4. 没有共享格式 / 数据库列 / 线格式携带这个上限. 级别 3.**
表结构只有 `orders(id, payload)` (`db/schema.sql:1-4`); 样例 payload 的键只有 `schema` / `amount` / `amount_str` (`db/seed.py:8-12`); 在下游 `src/ledger.js` 里只做 `Number(row.amount)` 求和, 不读数量; 全仓 grep `qty` / `99` 除定义处只命中金额字符串 `"9.99"`.

原始输出:

```
### scan_callers
扫描文件数: 18 (范围: /tmp/orchestra-07/drill-ts003-local, /tmp/orchestra-07/orders-consumer)
定义处: app/clamp.py:4
定义文件之外的引用: 0
PASS: 除定义处, 没有任何代码引用 clamp_qty; app/clamp.py 未被任何模块导入
RC=0

### prove_window
clamp_qty(   0)  base=   1  head=   1  same
clamp_qty(   1)  base=   1  head=   1  same
clamp_qty(  50)  base=  50  head=  50  same
clamp_qty(  51)  base=  51  head=  50  CHANGED
clamp_qty(  60)  base=  60  head=  50  CHANGED
clamp_qty(  99)  base=  99  head=  50  CHANGED
clamp_qty( 100)  base=  99  head=  50  CHANGED
clamp_qty(1000)  base=  99  head=  50  CHANGED
有差异的输入: [51, 60, 99, 100, 1000]
PASS: 差异覆盖所有输入 >= 51 (默认 upper 生效时); 显式传 upper 时两版完全一致
RC=0

### run_e2e (只摘关键行)
$ (base) uv run python scripts/dump_orders.py -> rc=0
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
$ (base) bash .../orders-consumer/src/run.sh .../base/var/orders.export.json -> rc=0
{"total": 22.490000000000002, "missing": [3]}
$ (head) uv run python scripts/dump_orders.py -> rc=0
[{"id": 1, "amount": "12.50"}, {"id": 2, "amount": "9.99"}, {"id": 3, "amount": null}]
$ (head) bash .../orders-consumer/src/run.sh .../head/var/orders.export.json -> rc=0
{"total": 22.490000000000002, "missing": [3]}
导出 JSON 相同: True
消费端汇总相同: True
PASS: 真实入口的输出与下游消费结果在本次变更前后逐字节相同
RC=0
```

## 3. 风险

**R1. 提交是空操作, 却可能被当成已生效的数量限制.**
- 位置: `app/clamp.py:4` 定义, 全仓无调用点.
- 概率: 100% (没有调用者, 运行时效果为零).
- 代价: 若动机是限制大单, 大单照旧入库; 且没人会看到报警, 因为没有任何日志或错误.
- 检查: 跑附录的 `scan_callers.py`; 或在 `dump_orders.py` 里临时打 `assert` 看是否有人读过 `app.clamp`.

**R2. 以后有人把 `clamp_qty` 接上时, 会按错的上限静默改数.**
- 位置: 未来调用点, 现在不存在.
- 概率: 未知, 触发条件明确 (有人 `import app.clamp` 并按 99 的旧习惯设计批量下单).
- 代价: 51..99 的数量被无声截成 50 (`app/clamp.py:6` 的 `min`), 不抛错, 不打日志, 只在结果里少几件.
- 检查: 真正接线的那次提交里, 加覆盖 50 / 51 / 99 / 100 的断言, 或在本提交合入时就把 `upper` 改成必填参数, 逼调用方显式决定.

**R3. 仓库外的 importer 无法排除 (未证实).**
- 位置: `app.clamp` 这个导入路径, 本机两个仓库之外.
- 概率: 低 (`README.md:3-4` 只说另一个仓库的 Node 消费者读 JSON, `pyproject.toml` 无 CLI 入口无依赖).
- 代价: 若存在, 对方会静默拿到 50 而不是 99.
- 缺什么: 缺生产部署清单 / 依赖方清单; 有清单就能一条 grep 收口.

**R4. 代码注释与事实不符 (已确认).**
- 位置: `app/clamp.py:1` "仅本模块内部使用", 提交消息 "内部数量上限".
- 事实: 连模块内部也没有调用者, 这个函数是完全的死代码.
- 代价: 后人按注释误判"这段在用", 或者以为改上限有影响而不敢动.
- 检查: 本报告 F1, 或 `grep -rn clamp_qty`.

## 4. 已排除项

- **导出 JSON 与下游汇总**: 实跑两版并比对, 逐字节相同 (级别 4). 排除"改上限会改金额或改导出"的可能.
- **amountlib 金额解析**: `app/clamp.py` 不 import 任何东西 (`app/clamp.py:1-6` 只有 docstring 和两个内置函数调用), `app/orders.py:4` 也不 import clamp. 上游 `04ddf93` 那次金额改动与本次无关 (已在上游报告覆盖).
- **`legacy_sync.py` 归档链路**: 该文件只 import `os` (`app/legacy_sync.py:5`), 不碰 clamp. 本地虽不可跑, 但导入关系上与本变更无交集.
- **数据库列 / 线格式**: 表只有 `id, payload`; payload 键只有 `schema/amount/amount_str`; 下游只求和 `amount`. 没有哪个字段装"数量上限 99" (级别 3).
- **测试会红**: 仓库内没有任何测试文件 (`find` 无 `test*` / `conftest.py`), 不存在被这次改动打红的用例. 反过来说也没有测试保护这个边界.
- **配置 / feature flag / 环境变量引用**: 全仓 grep `clamp` / `qty` / `99` 无命中 (`99` 只出现在金额 `"9.99"` 里).
- **其他调用历史**: `git log --all -S"clamp_qty"` 只有基线新增那一次, 没有"曾经被调用后删除"的痕迹.

## 5. 合并前最便宜的复现

一条命令就能抓住最要紧的问题 (这是个空操作):

```bash
cd /tmp/orchestra-07/out/ts003-local-work && uv run python scan_callers.py
```

退出码 0 = 零调用者 (当前结果); 若哪天有人接线, 脚本会打印命中的文件行号并以非零退出.

想同时确认"真实链路不变", 再跑:

```bash
cd /tmp/orchestra-07/out/ts003-local-work && uv run python run_e2e.py && uv run python prove_window.py
```

## 6. 单路声明与缺口

- 按调用方选择, 只做了单路调查, 没有多模型同题核对. 技能要求的多模型合并缺口在此明写.
- 已实跑证明的事实 (F2, F3) 保持级别 4, 不因单路而降级.
- 后续可加查的点: R3 (生产依赖方清单), R1 的真实动机 (提交没有 PR 可读), 生产 `orders.payload` 实际键分布.

## 附录: 脚本全文 (在 `/tmp/orchestra-07/out/ts003-local-work/`)

### scan_callers.py

```python
"""证明 clamp_qty 在仓库内外都没有调用者.

失败条件 (非零退出): 在扫描范围内找到定义文件之外的任何引用.
扫描方式: 文本检索 + AST (抓 import/属性访问), 避免漏掉别名导入.
"""
import ast
import pathlib
import sys

REPO = pathlib.Path("/tmp/orchestra-07/drill-ts003-local")
CONSUMER = pathlib.Path("/tmp/orchestra-07/orders-consumer")
NEEDLE = "clamp_qty"
SKIP_DIRS = {".git", ".agents", "__pycache__", ".venv", "node_modules"}


def files(root):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not (set(p.parts) & SKIP_DIRS):
            yield p


def main():
    hits = []
    scanned = 0
    for root in (REPO, CONSUMER):
        for p in files(root):
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            scanned += 1
            if NEEDLE in text and "app/clamp.py" not in str(p):
                hits.append((p, "text"))
            if p.suffix == ".py":
                tree = ast.parse(text, filename=str(p))
                for node in ast.walk(tree):
                    names = []
                    if isinstance(node, ast.ImportFrom):
                        names = [a.name for a in node.names] + [node.module or ""]
                    elif isinstance(node, ast.Import):
                        names = [a.name for a in node.names]
                    elif isinstance(node, ast.Attribute):
                        names = [node.attr]
                    elif isinstance(node, ast.Name):
                        names = [node.id]
                    if any(NEEDLE == n or n.endswith("." + NEEDLE) for n in names):
                        if "app/clamp.py" not in str(p):
                            hits.append((p, f"ast:{type(node).__name__}:{getattr(node, 'lineno', '?')}"))

    print(f"扫描文件数: {scanned} (范围: {REPO}, {CONSUMER})")
    print(f"定义处: app/clamp.py:4")
    print(f"定义文件之外的引用: {len(hits)}")
    for p, how in hits:
        print(f"  {p} [{how}]")

    assert hits == [], f"发现调用者, 需要人工评估: {hits}"
    print("PASS: 除定义处, 没有任何代码引用 clamp_qty; app/clamp.py 未被任何模块导入")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### prove_window.py

```python
"""证明本次变更只改了一个窗口内的返回值, 且该窗口只能由直接调用触达."""
import importlib.util
import sys
from pathlib import Path

WORK = Path("/tmp/orchestra-07/out/ts003-local-work/trees")


def load(name):
    path = WORK / name / "app" / "clamp.py"
    spec = importlib.util.spec_from_file_location(f"clamp_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base, head = load("base"), load("head")
rows = []
for q in (0, 1, 50, 51, 60, 99, 100, 1000):
    b, h = base.clamp_qty(q), head.clamp_qty(q)
    rows.append((q, b, h, b == h))
for q, b, h, same in rows:
    print(f"clamp_qty({q:>4})  base={b:>4}  head={h:>4}  {'same' if same else 'CHANGED'}")

changed = [q for q, b, h, same in rows if not same]
print(f"\n有差异的输入: {changed}")
assert changed == [51, 60, 99, 100, 1000], f"差异窗口与预期不符: {changed}"

# 显式传入 upper 时, 默认值不参与, 行为完全不变
assert base.clamp_qty(99, upper=99) == head.clamp_qty(99, upper=99) == 99
print("PASS: 差异覆盖所有输入 >= 51 (默认 upper 生效时); 显式传 upper 时两版完全一致")
```

### run_e2e.py

```python
"""跑真实入口, 比较 HEAD~1 与 HEAD 的导出结果.

步骤: 用 git archive 导出两个版本的树到临时目录, 各自 seed 出 SQLite, 跑
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
    subprocess.run(["git", "-C", str(REPO), "archive", rev], stdout=subprocess.PIPE, check=True)
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
```
