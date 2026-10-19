# 产品验收报告 tool-cli / f98bbfe 第 1 轮

## 输入与版本前提

- 判据来源: `docs/changes/tool-cli/PRODUCT.md` (git blob ed4b106, 与目标提交一致), `验收标准` 节在 gherkin 块前带确认标记 `<!-- confirmed-flow: v1 -->`.
- 目标提交: `f98bbfebfd974fd68a9f8f3b3ec616fdda637b44` (HEAD, "feat: greet 支持全大写输出"), 上一提交 `4eeabf35f5567f30512a331f1a75060f2f35272b`.
- 产物根目录: `docs/changes/tool-cli/`, 本轮独立证据目录 `docs/changes/tool-cli/verify-f98bbfe-r1/` (未覆盖旧证据, 旧一轮没有同名目录).
- 版本前提核对: 验收开始时 `git status --porcelain --untracked-files=all` 输出为空, 已跟踪源码, 配置, 测试无未提交改动, 无未跟踪产品文件. 目标提交存在且等于 HEAD, 满足前提.
- 必验清单: 验收场景 3 条 (AC-001-1, AC-002-1, AC-003-1) + 业务规则中标 `(审计)` 的 1 条 (BR-002) = 4 项, 编号照原文.
- 证据目录影响判断: 见 `env-check.log`. `build.sh` 只 `python3 -m compileall -q tool.py`; `prepare.sh` 调 `tools/build_manifest.py`, 只读 `tool.py` 并写 `dist/app.txt`; 仓库无 pytest.ini/pyproject.toml/tox.ini, pytest 默认发现 `test_*.py` 与 `tests/`; 证据目录内不放 `test_*.py`, 也不被上述脚本引用. 结论: 证据留在仓库内的 `docs/changes/tool-cli/verify-f98bbfe-r1/`, 不进入构建, 测试发现或运行输入.

## 逐项结果

| 编号 | 材料类型 | 实际操作 / 引用信息 | 实际结果 | 证据位置 | 时间 / 版本 | 结论 |
| --- | --- | --- | --- | --- | --- | --- |
| AC-001-1 构建清单第一行 (G-001) | 当前观察 | 2026-10-19T20:30:36+08:00 在项目根执行 `bash prepare.sh` (退出码 0, 输出 `built dist/app.txt`), 再执行 `sed -n '1p' dist/app.txt` (退出码 0) | 输出 `tool-cli 1`, 与期望逐字一致; `cat -A` 显示 `tool-cli 1$`, 无尾随空格 | `run-prepare.log`, `run-scenarios.log` | f98bbfebfd974fd68a9f8f3b3ec616fdda637b44 | 通过 |
| AC-002-1 构建清单第二行 (G-002) | 当前观察 | 同一 `dist/app.txt` 上执行 `sed -n '2p' dist/app.txt` (退出码 0) | 输出 `commands=greet,count,export`, 与期望逐字一致; `cat -A` 显示行尾仅 `$` | `run-prepare.log`, `run-scenarios.log` | f98bbfebfd974fd68a9f8f3b3ec616fdda637b44 | 通过 |
| AC-003-1 构建清单第三行 (G-003, BR-001) | 当前观察 | 同一 `dist/app.txt` 上执行 `sed -n '3p' dist/app.txt` (退出码 0) | 输出 `greet-shout=yes`, 与期望逐字一致; 文件共 3 行, 无多余行 | `run-prepare.log`, `run-scenarios.log` | f98bbfebfd974fd68a9f8f3b3ec616fdda637b44 | 通过 |
| BR-002 不新增第三方依赖, 依赖清单/锁文件/构建材料与上一提交逐项一致 (审计) | 静态材料核对 (不是运行行为结果) | 命令见 `audit-br002.log`: `git diff --stat 4eeabf3 HEAD` 只显示 `tests/test_tool.py` 与 `tool.py`; 对 `deps.txt`, `deps.lock`, `build.sh`, `prepare.sh`, `tools/build_manifest.py` 逐一 `git diff` 均为 0 行; 逐文件 blob 哈希两版本完全相同 (deps.txt bbb5297, deps.lock f5f745d, build.sh 7796246, prepare.sh f6c7c17, tools/build_manifest.py 4414005); `diff <(git ls-tree -r --name-only 4eeabf3) <(git ls-tree -r --name-only HEAD)` 无输出, 未新增任何依赖或构建文件; `grep` 显示 `tool.py` 只导入 argparse/json/pathlib/sys, 均为标准库, 与 `deps.txt` 的 `python-stdlib` 一致 | 依赖清单, 锁文件, 构建材料前后逐项一致, 无新增第三方依赖 | `audit-br002.log` | 4eeabf35f5567f30512a331f1a75060f2f35272b -> f98bbfebfd974fd68a9f8f3b3ec616fdda637b44 | 通过 (仅静态核对) |

汇总: 4 项必验全部有本轮结果, 3 项场景通过, 1 项审计规则静态核对通过; 失败 0 项, 未验证 0 项.

## 覆盖范围与非产品判据

- 本轮只判 PRODUCT.md 的验收场景与审计业务规则. PRODUCT.md 中 G-001..G-003 为每个场景已覆盖的目标; NG-001 (不做多语言) 不在验收场景内, 本轮未单独展开; 无 `(审计)` 标记的 BR-001 未单列成行, 其可观察部分由 AC-003-1 承接.
- `TECHNICAL.md` 的模块接口与测试接缝只用于确定运行命令, 不作为产品通过条件; 内部代码划分与模块拆分属技术评审范围, 本轮不判通过也不判失败.
- 辅助运行 (不属产品判据, 不影响上表结论): `bash build.sh` 退出码 0; `python3 -m pytest -q` 因当前 Python 环境无 pytest 模块 (No module named pytest) 未运行成功, 记录在 `run-aux-tests.log`, 该项不作为产品缺陷也不算产品证据.
- 场景执行副作用: `prepare.sh` 生成 `dist/app.txt`, 另因 `build.sh` 与 pytest 尝试产生 `__pycache__/`. 两者都被 `.gitignore` 忽略, 未改动任何已跟踪文件; 见 `env-check.log` 的 `!!` 段.

## 收尾说明

除本次证据目录的输出外, 源码与 Spec 未变. 验收期间未修改产品代码, 配置, 测试, 未提交, 未推送, 未开 PR; 未使用提交快照或另一份工作区.

本报告结论仍需用户逐项确认和正式人工验收, 不构成本轮正式交付或用户验收关闭.
