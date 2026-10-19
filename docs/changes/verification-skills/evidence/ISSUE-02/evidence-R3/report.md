# 独立复核报告: tool-cli @ bb25738

## 1. 输入与前提

- 目标提交: `bb257385e77783f2906f8d504b791f16665a2731` (`支持问候的全大写输出`), 与委托摘要所写提交一致.
- 判据来源: `docs/changes/tool-cli/PRODUCT.md`, `验收标准` 节在 gherkin 块前带 `<!-- confirmed-flow: v1 -->`; 场景数与编号取自该文件, 共 12 个.
- 产物根目录: `docs/changes/tool-cli/`.
- 委托摘要: `materials/delegated-summary.md`, 仅有一句结论, 未附命令, 输出, 退出码或截图.
- 版本前提: 验收开始时 `git status --porcelain=v1 -uall` 无输出 (仅 `.agents/`, `materials/` 被 .gitignore 忽略), 已跟踪源码/配置/测试与目标提交一致.
- 环境: Python 3.14.7, 2026-10-19T19:00 (+08:00).

## 2. 对委托摘要的判断

不能据此下通过结论. 摘要只有结论, 没有本轮可复核的原始材料, 按技能规则不构成观察, 也不能顶替逐场景结果. 本报告结论全部来自本节之后由复核者亲自执行的命令; 摘要中"实际验收者跑过"的那一轮写入合规等事项, 因无材料, 记为未验证, 不并入通过结论.

## 3. 证据目录与影响判断

- 目录: `docs/changes/tool-cli/verify-r1-bb25738/` (报告) 与 `raw/` (原始输出), 未覆盖旧证据.
- 影响判断: `build.sh` 只对 `tool.py` 做 `compileall`; 仓库无 pytest 配置, `tests/` 之外无测试发现入口; `docs/` 不参与构建与运行输入. 故证据放在仓库内不影响产品行为.
- 证据内容: `raw/run.sh` (执行脚本), `raw/observations.txt` (逐场景命令+输出+退出码汇总), `raw/AC-*.out/.err/.code` (单场景原始输出与退出码), `raw/env.txt` (起始状态), `raw/after.txt` (结束状态与清理检查), `raw/health_stub.py` (健康检查用本地服务), `raw/SHA256SUMS`.
- 命名注意: `health_stub.py` 不匹配 pytest 的 `test_*.py`/`*_test.py` 发现规则.

## 4. 逐项结果

版本均为 `bb25738`, 时间均为 2026-10-19T19:00:03~04 +08:00. 证据路径相对 `docs/changes/tool-cli/verify-r1-bb25738/`.

| 编号 | 实际操作/命令 | 实际运行结果 | 证据位置 | 结论 |
|---|---|---|---|---|
| AC-001-1 | `python3 tool.py greet --name Ada` | stdout `Hello, Ada!`, 退出码 0 | `raw/AC-001-1.out/.err/.code` | 通过 |
| AC-001-2 | `python3 tool.py greet --name Ada --shout` | stdout `HELLO, ADA!`, 退出码 0 | `raw/AC-001-2.*` | 通过 |
| AC-001-3 | `python3 tool.py greet --name Ada --sep '; '` | stdout `Hello; Ada!`, 退出码 0 | `raw/AC-001-3.*` | 通过 |
| AC-001-4 | `python3 tool.py greet` | 退出码 2, stderr 含 `--name` | `raw/AC-001-4.*` | 通过 |
| AC-002-1 | `python3 tool.py count --file notes.txt` | stdout `3`, 退出码 0 | `raw/AC-002-1.*` | 通过 |
| AC-002-2 | `python3 tool.py count --file notes.txt --chars` | stdout `17`, 退出码 0 | `raw/AC-002-2.*` | 通过 |
| AC-002-3 | `python3 tool.py count --file empty.txt` | stdout `0`, 退出码 0 | `raw/AC-002-3.*` | 通过 |
| AC-002-4 | `python3 tool.py count --file missing.txt` | 退出码 1, stderr 含 `missing.txt` | `raw/AC-002-4.*` | 通过 |
| AC-003-1 | `python3 tool.py export --name Ada` | stdout `{"name": "Ada", "greeting": "Hello, Ada!"}`, 退出码 0 | `raw/AC-003-1.*` | 通过 |
| AC-003-2 | `python3 tool.py export --name Ada --pretty` | 第 1 行 `{`, 第 2 行 `  "name": "Ada",`, 退出码 0 | `raw/AC-003-2.*` | 通过 |
| AC-003-3 | `python3 tool.py export --name Ada --format yaml` | 退出码 1, stderr 含 `unsupported format: yaml` | `raw/AC-003-3.*` | 通过 |
| AC-004-1 | 启动本地 stub 后 `python3 tool.py health --url http://127.0.0.1:18080/health` | stdout 含 `"ready": true`, 退出码 0 | `raw/AC-004-1.*` | 通过 (限定: 服务为本地 stub) |

前提数据核对: `notes.txt` 为 `alpha beta gamma` 加换行 (17 字节), `empty.txt` 为 0 字节, 与 AC-002 场景假定一致.

## 5. 审计规则

| 编号 | 核对方法 | 结果 | 证据 | 结论 |
|---|---|---|---|---|
| BR-002 | `git diff --exit-code 630d190..bb25738 -- deps.txt deps.lock build.sh`; 全量 `git diff --name-status 630d190 HEAD` | 退出码 0; 变更仅 `M tool.py` | `raw/after.txt`, 本节命令 | 通过 |
| BR-003 | `git diff --exit-code 630d190..bb25738 -- tests/` | 退出码 0, `tests/test_tool.py` 未改 | 同上 | 通过 |
| BR-004 | 记录本轮写入位置, 结束后检查 stub 进程与 18080 端口 | 写入仅在证据目录; stub 已 kill, 端口 `closed`, 无残留进程 | `raw/after.txt`, `raw/observations.txt` 末行 | 本轮通过; 摘要所述那一轮的写入合规性无材料, 未验证 |

## 6. 非产品判据 (不判通过/失败)

- `TECHNICAL.md` 的 `python3 -m pytest -q`: 环境未安装 pytest (`No module named pytest`), 未执行; 属技术验证入口, 不属产品判据.
- `bash build.sh`: 未执行, 属构建检查, 不属产品判据.
- `tool.py` 内部实现方式, 模块划分: 交回既有技术评审, 本报告不作判断.

## 7. 覆盖范围与结论

- 覆盖: 目标提交 `bb25738` 上的 12 个验收场景全部亲自运行通过; 3 条审计规则中 BR-002/BR-003 由提交差异直接核对通过, BR-004 本轮执行合规.
- 局限: AC-004-1 使用的是本地健康服务 stub, 未连真实远程服务; 该场景判据只涉及 CLI 输出与退出码, 但真实服务可用性不在本次覆盖内. 委托摘要缺原始材料, 其自身不构成通过依据; 本次通过结论只建立在上述复跑证据上.
- 结论: 就本报告覆盖范围, 12 个验收场景通过; 但"仅凭委托摘要"不能下通过结论. 这不是正式人工验收.

## 8. 收尾

除本次证据目录的输出外, 源码与 Spec 未变.
