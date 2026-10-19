# BR-001 审计复验报告 (round 2, 组 2, 独立验收者)

- 项目: `/tmp/orchestra-04/reverify`
- 目标提交 (HEAD, 未切换): `59069130494139f96994f144c1ba09d3b51876d6` (下称 5906913)
- 修复提交父提交: `cd087542b4610c49ded0a1278fe8065726b62d9d` (下称 cd08754)
- 基线提交: `8438934fc81b67ed518dc4ad2e2f7dbd83b0192a` (下称 8438934)
- 判据: `docs/changes/relay-board/PRODUCT.md` 第 20 行 BR-001 原文
  "本次变更不新增第三方依赖, `deps.txt` 与上一提交逐项一致. (审计)"
- 结论范围: **本报告全部为静态材料核对结果, 不是运行行为结果**. 未运行 serve/status/health/job/report/log/record/append, 未占用端口, 未读写 `runtime/`.

## 会话事实

- 本会话为新开会话, 启动时间 `2026-10-19T22:29:41+08:00` (命令 `date -Is`).
- 本会话未参与该项目实现或修复, 未做任何实现/修复动作.
- 未切换分支/提交 (`git rev-parse HEAD` 仍为目标提交).
- 未修改任何产品文件: 工作区与索引均无已跟踪文件改动 (`git diff --stat`、`git diff --cached --stat` 均为空);
  `git status --porcelain -uall` 只列出 `docs/changes/relay-board/evidence/` 下的未跟踪验收材料.
- 本目录 `audit-BR-001/` 为本次新建; 同目录 `v2-5906913/runtime-AC/` 等为其他组材料, 本次未改动.

## 检查 1: 修复提交 5906913 相对父提交 cd08754 的变更文件清单

命令与原始输出:

```
$ git show --stat --format="%H%n%P%n%an %ad%n%s" 5906913
59069130494139f96994f144c1ba09d3b51876d6
cd087542b4610c49ded0a1278fe8065726b62d9d
luojingyan Mon Oct 19 22:27:25 2026 +0800
fix: report 输出反映实例当前状态 (state=ready), 不再写死 loading

 app.py | 3 ++-
 1 file changed, 2 insertions(+), 1 deletion(-)

$ git diff --name-status cd08754 5906913
M	app.py
```

- 变更文件仅 1 个: `app.py` (修改), 无新增文件, 无删除文件, 无重命名.
- 父提交哈希与任务给定 `cd087542b4610c49ded0a1278fe8065726b62d9d` 一致.
- 实际改动 (行号见 diff, 位于 `app.py` 第 61-63 行附近):

```
$ git diff cd08754 5906913 -- app.py
@@ -59,7 +59,8 @@ class Board:
     def report(self) -> str:
-        return report_line(self.instance, "loading")
+        # report 的状态必须反映实例当前状态, 不能写成固定值.
+        return report_line(self.instance, self.state)
```

- 改动未引入任何 `import` 语句, 未新增依赖.

## 检查 2: deps.txt 差异与 git blob

```
$ for r in 8438934 cd08754 5906913; do echo "$r:$(git rev-parse $r:deps.txt)"; done
8438934:ff2c99947923198db10083beab39cf783c26e9b0
cd08754:ff2c99947923198db10083beab39cf783c26e9b0
5906913:ff2c99947923198db10083beab39cf783c26e9b0

$ git diff cd08754 5906913 -- deps.txt | wc -l
0
$ git diff 8438934 5906913 -- deps.txt | wc -l
0

$ git hash-object deps.txt
ff2c99947923198db10083beab39cf783c26e9b0
```

- `deps.txt` 在三个提交和工作区中 blob 完全一致 (`ff2c9994...`), 逐项一致, 差异为 0 行.
- 文件内容 (`cat -A` 与 `od` 原始输出, 仅 1 行 38 字节, 无隐藏差异):

```
$ cat -A deps.txt
python3 M-fM- M-^GM-eM-^GM-^FM-eM-:M-^S, M-fM-^WM- M-gM-,M-,M-dM-8M-^IM-fM-^VM-9M-dM->M-^]M-hM-5M-^V$

$ od -An -tx1 -c deps.txt
  70  79  74  68  6f  6e  33  20  e6  a0  87  e5  87  86  e5  ba
   p   y   t   h   o   n   3     346 240 207 345 207 206 345 272
  93  2c  20  e6  97  a0  e7  ac  ac  e4  b8  89  e6  96  b9  e4
 223   ,     346 227 240 347 254 254 344 270 211 346 226 271 344
  be  9d  e8  b5  96  0a
 276 235 350 265 226  \n
```

按字节解码即为可读文本 `python3 标准库, 无第三方依赖`, 换行结尾 (`0a`), 无 BOM/无隐藏字符.

## 检查 3: 是否新增依赖声明/锁文件/构建材料

```
$ find . -maxdepth 3 -not -path "./.git/*" \( -name "*requirements*" -o -name "*lock*" \
    -o -name "pyproject.toml" -o -name "setup.py" -o -name "setup.cfg" -o -name "Pipfile*" \
    -o -name "poetry.lock" -o -name "environment.yml" -o -name "Dockerfile*" -o -name "Makefile" \) -print
(无输出)
```

- 仓库内不存在 requirements*/lock 文件/pyproject.toml/setup.py/setup.cfg/Pipfile/environment.yml/Dockerfile/Makefile.
- 修复提交未新增任何文件 (检查 1), 因此不可能新增依赖声明或构建材料.
- 头部提交跟踪文件根目录仅 `app.py deps.txt docs .gitignore README.md tests`, 无 vendor/ 或第三方源码目录.

```
$ git ls-tree -r --name-only 5906913
.gitignore
README.md
app.py
deps.txt
docs/changes/relay-board/PRODUCT.md
tests/test_app.py
```

## 检查 4: 累计变更 8438934..5906913 的依赖情况

```
$ git diff --name-status 8438934 5906913
M	app.py
```

- 从基线到目标提交, 跟踪文件层面只有 `app.py` 被修改, 没有新增文件.
- `deps.txt` 差异 0 行 (见检查 2), blob 相同.
- 结论: 累计变更同样未新增第三方依赖.

## 检查 5: app.py (新提交) 全部 import 是否都在 Python 标准库

命令与原始输出:

```
$ git show HEAD:app.py | grep -nE "^\s*(import|from)\s"
3:import argparse
4:import json
5:import sys
6:import time
7:from datetime import datetime, timezone
8:from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
9:from pathlib import Path
10:from urllib.parse import parse_qs, urlparse
127:    import urllib.request
```

AST 解析核对 (`uv run python`, Python 3.14.7):

```
$ uv run python - <<'EOF'
import ast, sys
src = open('app.py', encoding='utf-8').read()
tree = ast.parse(src)
mods = set()
for n in ast.walk(tree):
    if isinstance(n, ast.Import):
        mods.update(a.name.split('.')[0] for a in n.names)
    elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
        mods.add(n.module.split('.')[0])
for m in sorted(mods):
    print(f"{m}: stdlib={m in sys.stdlib_module_names}")
print("non-stdlib:", sorted(m for m in mods if m not in sys.stdlib_module_names))
EOF
argparse: stdlib=True
datetime: stdlib=True
http: stdlib=True
json: stdlib=True
pathlib: stdlib=True
sys: stdlib=True
time: stdlib=True
urllib: stdlib=True
non-stdlib: []
```

- 全部 8 个顶层模块均为标准库, 非标准库列表为空.
- 第 127 行 `import urllib.request` 为函数内局部导入, 仍属标准库 `urllib`.
- 动态导入扫描无第三方痕迹:

```
$ grep -nE "__import__|importlib|pkg_resources|site-packages|pip|venv" app.py
(无输出, 退出码 1)
```

## 逐项结论

| 检查项 | 结果 | 依据 |
|---|---|---|
| 修复提交全部变更文件清单 | 通过 | 仅 `M app.py`, 1 file changed, 2 insertions(+), 1 deletion(-) |
| 修复提交 deps.txt 与父提交逐项一致 | 通过 | blob 均为 `ff2c9994...`, diff 0 行 |
| 修复提交无新增依赖声明/锁文件/构建材料 | 通过 | 无新增文件; find 无匹配; 无相关构建文件 |
| 累计 8438934..5906913 未新增第三方依赖 | 通过 | 仅 `M app.py`; deps.txt blob 不变 |
| app.py 全部 import 属标准库 | 通过 | 8 个模块 AST 核对均 stdlib; non-stdlib 为空 |
| 产品文件未被本次验收改动 | 通过 | `git diff`/`git diff --cached` 为空, 仅证据目录未跟踪 |

## 最终结论

**通过 (PASS)** — 静态材料核对结果: BR-001 在该提交上成立, 修复提交与累计变更均未新增第三方依赖, `deps.txt` 与父提交及基线逐项一致, `app.py` 全部导入均为 Python 标准库.

**限定说明**: 本结论仅来自静态材料核对 (git 对象/diff/文件内容/源码 AST), 不代表任何运行行为 (serve/status/health/job/report/log/record/append) 的验收结果, 本会话未运行产品入口.

## 可复核位置汇总

- 判据: `docs/changes/relay-board/PRODUCT.md:20` (BR-001)
- 提交: `59069130494139f96994f144c1ba09d3b51876d6` (HEAD), 父 `cd087542b4610c49ded0a1278fe8065726b62d9d`, 基线 `8438934fc81b67ed518dc4ad2e2f7dbd83b0192a`
- 变更: `app.py` 第 61-63 行附近 (diff hunk `@@ -59,7 +59,8 @@`)
- 导入: `app.py` 第 3-10 行, 第 127 行
- 依赖声明: `deps.txt` 第 1 行, blob `ff2c99947923198db10083beab39cf783c26e9b0`
- 本报告目录: `docs/changes/relay-board/evidence/v2-5906913/audit-BR-001/`
