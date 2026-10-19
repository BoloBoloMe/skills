# 组 B 静态审计报告 (BR-001)

- 验收者身份: 独立验收者, 未参与实现与修复.
- 目标提交: `59069130494139f96994f144c1ba09d3b51876d6` (HEAD).
- 上一提交: `cd087542b4610c49ded0a1278fe8065726b62d9d`. 基线提交: `8438934fc81b67ed518dc4ad2e2f7dbd83b0192a`.
- 判据原文: `docs/changes/relay-board/PRODUCT.md` `业务规则` 节 `BR-001: 本次变更不新增第三方依赖, deps.txt 与上一提交逐项一致. (审计)`.
- 采集时间: 2026-10-19T22:38:24+08:00 至 2026-10-19T22:38:28+08:00.
- 材料类型: **静态材料核对** (git 对象与文件内容), 不是运行行为结果. 本文所有结论均不推断运行时是否真的没有第三方依赖, 只核对仓库材料.

## 1. 变更范围

- 标准编号: BR-001 (变更范围部分)
- 材料类型: 静态材料核对
- 实际操作命令与原始输出 (时间 22:38:24):
  ```
  $ git rev-parse HEAD
  59069130494139f96994f144c1ba09d3b51876d6

  $ git diff --stat cd087542b4610c49ded0a1278fe8065726b62d9d 59069130494139f96994f144c1ba09d3b51876d6
   app.py | 3 ++-
   1 file changed, 2 insertions(+), 1 deletion(-)

  $ git diff --name-status cd08754 5906913
  M	app.py
  ```
- 完整 diff (`git diff cd08754 5906913`) 只改 `app.py` 中 `Board.report()` 的一行实现, 加一行注释, 未新增文件:
  ```diff
  @@ -59,7 +59,8 @@ class Board:
           return self.record_path.read_text(encoding="utf-8")

       def report(self) -> str:
  -        return report_line(self.instance, "loading")
  +        # report 的状态必须反映实例当前状态, 不能写成固定值.
  +        return report_line(self.instance, self.state)
  ```
- 退出码: 三条命令均为 0.
- 证据路径: `01-git-diff-stat.txt`, `02-git-diff-full.txt`.
- 结论: 变更只修改 `app.py`, 无新增文件, 无依赖材料变更. 通过 (静态核对).

## 2. `deps.txt` 与上一提交逐项一致

- 标准编号: BR-001
- 材料类型: 静态材料核对 (git blob 哈希 + 工作区内容)
- 实际操作命令与原始输出 (时间 22:38:28):
  ```
  $ git rev-parse 8438934fc81b67ed518dc4ad2e2f7dbd83b0192a:deps.txt
  ff2c99947923198db10083beab39cf783c26e9b0
  $ git rev-parse cd087542b4610c49ded0a1278fe8065726b62d9d:deps.txt
  ff2c99947923198db10083beab39cf783c26e9b0
  $ git rev-parse 59069130494139f96994f144c1ba09d3b51876d6:deps.txt
  ff2c99947923198db10083beab39cf783c26e9b0
  $ git rev-parse HEAD:deps.txt
  ff2c99947923198db10083beab39cf783c26e9b0
  $ md5sum deps.txt
  99b58cfc58385c367bc855de422b8f5d  deps.txt
  ```
  三个提交 `deps.txt` 内容原文均为:
  ```
  python3 标准库, 无第三方依赖
  ```
- `git diff <commit> -- deps.txt` 三次结果均为空 (8438934, cd08754, 5906913); `git status --porcelain -- deps.txt` 为空, 工作区 `deps.txt` 与 HEAD 一致.
- 退出码: 上述 git 命令均为 0.
- 证据路径: `03-deps-identity.txt`.
- 结论: `deps.txt` 的 blob 哈希 `ff2c9994...` 在基线, 上一提交, 目标提交, HEAD 和工作区完全相同, 逐项一致. 通过 (静态核对).

## 3. 是否新增依赖/构建清单文件

- 标准编号: BR-001
- 材料类型: 静态材料核对
- 实际操作命令 (时间 22:38:28):
  ```
  $ git ls-tree -r --name-only HEAD | grep -Ei '(requirements[^/]*|.*\.lock|pyproject\.toml|setup\.py|setup\.cfg|Pipfile|poetry\.lock|uv\.lock|environment\.ya?ml|MANIFEST\.in|build\.py|package\.json|go\.mod|Cargo\.toml)'
  (无匹配)
  $ find . -path ./.git -prune -o -path ./runtime -prune -o -type f \( 同类文件名模式 \) -print
  (无输出)
  $ git ls-tree -r --name-only HEAD
  .gitignore
  README.md
  app.py
  deps.txt
  docs/changes/relay-board/PRODUCT.md
  tests/test_app.py
  ```
- 说明: 项目根目录与仓库内均无 requirements*, lock 文件, pyproject.toml, setup.py, setup.cfg, Pipfile, environment.yml, MANIFEST.in, package.json 等依赖或构建清单; HEAD 只有 6 个文件.
- 退出码: `git ls-tree` 与 `find` 为 0; `grep` 因无匹配返回 1 (无匹配正是结论依据, 并以 `git ls-tree` 全量清单复核).
- 证据路径: `04-dependency-files.txt`.
- 结论: 无新增依赖材料. 通过 (静态核对).

## 4. `app.py` 的 import 是否全为标准库

- 标准编号: BR-001
- 材料类型: 静态材料核对 (Python AST 静态分析, 以 `sys.stdlib_module_names` 判定)
- 实际操作命令: 用本机解释器对该提交的 `app.py` 做 AST 遍历, 列出每个 import 及是否标准库; 分析脚本只读取文件, 未修改产品文件.
- 原始输出 (时间 22:38:28 之后, 解释器 CPython 3.14.7):
  ```
  line=3 kind=import module=argparse is_stdlib=STDLIB
  line=4 kind=import module=json is_stdlib=STDLIB
  line=5 kind=import module=sys is_stdlib=STDLIB
  line=6 kind=import module=time is_stdlib=STDLIB
  line=7 kind=from module=datetime is_stdlib=STDLIB
  line=8 kind=from module=http.server is_stdlib=STDLIB
  line=9 kind=from module=pathlib is_stdlib=STDLIB
  line=10 kind=from module=urllib.parse is_stdlib=STDLIB
  line=127 kind=import module=urllib.request is_stdlib=STDLIB

  import_statements=9 non_stdlib=0
  non_stdlib_list=(none)
  ```
- 退出码: 0.
- 证据路径: `05-imports-ast.txt`, `05-imports-ast.runlog.txt`.
- 结论: `app.py` 的 9 条 import 全部为标准库, 无第三方 import. 通过 (静态核对).

## 5. BR-001 总结

- 标准编号: BR-001
- 材料类型: 静态材料核对, **不是运行行为结果**.
- 五项静态事实:
  1. `git diff cd08754 5906913` 只修改 `app.py` 的 report 状态来源, 无新增文件.
  2. `deps.txt` 在 8438934, cd08754, 5906913, HEAD 与工作区的 blob 哈希均为 `ff2c99947923198db10083beab39cf783c26e9b0`, 逐字节一致.
  3. 仓库无依赖/构建清单文件.
  4. `app.py` 的 import 全为标准库.
  5. 变更未引入任何新的依赖声明材料.
- 结论: **通过 (静态材料核对)**. 本结论只说明仓库材料没有新增第三方依赖, 不代表对运行时环境的动态验证.
- 证据路径: `01-git-diff-stat.txt` 至 `05-imports-ast.txt`, 以及 `../06-post-window-readonly-check.txt` (恢复后只读复核 HEAD 与文件哈希).

## 6. 未验证项与说明

- 未验证: 无 (BR-001 的全部静态检查项均已执行).
- 未运行: 本轮未安装或运行任何依赖解析工具 (如 pip/uv 的依赖解析), 本审计不依赖此类运行结果.
- 未采用: 作者 `PLAN.md` 与 v1/v2 旧证据未作为本轮通过依据.

## 7. 声明

- 除证据目录输出与 `runtime/` 运行数据外, 源码, 配置, 测试与 Spec 未变: 恢复后只读核对 `git hash-object` 与 `git rev-parse HEAD:<file>` 一致, `git diff` / `git diff --cached` 为空 (`../06-post-window-readonly-check.txt`).
- 本报告结论仍需用户确认和正式人工验收.
