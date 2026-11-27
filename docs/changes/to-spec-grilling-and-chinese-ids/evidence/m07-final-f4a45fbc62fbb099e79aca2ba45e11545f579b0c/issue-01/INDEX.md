# ISSUE-01 证据索引 (to-spec 盘问流程与 CLI)

- 证据根: `/home/bolo/evidence/to-spec-grilling-and-chinese-ids/issue-01/` (决策41 登记根之下的本 issue 子目录).
- 代码提交: `fd26618`, `8ce78be`; 交付证据提交 `3229525`, `1e64e6c` (后两者只改工单). 分支 `issue/01` 顶端 `1e64e6c`, 未推送 (按派工). 绑定记录 `run5/final-commit.txt`.
- 对象: 本索引登记的全部原件均由本分支真实 CLI 进程, 真实 gherkin-official 解析器与隔离文件产生; 无 mock 内部协作者, 未触真实规格或已安装技能.
- 清单与摘要: `manifest.sha256` (1118 行, 覆盖 run1-run5 全部非缓存原件; `sha256sum -c` 通过).
- 复跑: 各 run 目录内 `probe.py` (check-tech 基线/候选矩阵), `target.py` (CLI 矩阵), `trace.py` (并发时序), 自包含于 `TMPDIR=<run>/tmp` 重跑; 新轮次建新目录, 不覆盖旧原件.

## 轮次

| 轮次 | 内容 | 状态 |
| --- | --- | --- |
| run1 | 首次环境摸底与 CLI 帮助/基线 pytest; 发现 AC-024 例7 报错被前置检查抢先 | 中间轮, 保留 (失败记录) |
| run2 | 修复标记检查顺序后的完整 CLI 矩阵 (未含最终 trace) | 中间轮, 保留 |
| run3 | 首次并发取证尝试: 解释器路径取错 (`uv run` 内 `sys.executable`), 子进程 125 退出 | 失败记录, 保留 |
| run4 | 提交 fd26618 上的完整轮: 环境, 依赖, check-tech 基线/候选矩阵, check-ac 用例23/24, preview/promote, trace 四例, pytest, check_skill, 范围搜索 | 保留 |
| run5 | 最终绑定轮 (提交 8ce78be): 同 run4 全项重跑 + `text-mapping.md` 定稿, 全部结论一致 | **本 issue 的结论依据** |

## 验证入口 → 原件

| 验证入口 | 原件 (相对证据根) | 结论 |
| --- | --- | --- |
| 1 条文逐条 (AC-001..024, 026..030 每个场景) | `run5/text-mapping.md` | 42 行逐场景通过, 无遗留缺口 |
| 2 与 grilling/handoff/opposing-viewpoint/领域维护组合 | `run5/text-mapping.md` 第 3 节; `run5/logs/capability-files.*` (exit 0, 无差异); `run5/logs/changed-files.*` | 通过, 未改既有能力与 deliberate |
| 3 preview | `run5/logs/target-preview.{cmd,stdout,stderr,exit}`; `run5/files/ac/valid/review/*.html`; `run5/files/ac/valid/page-nodes.json` (2 张卡片, 原文与草稿逐字一致, 无 form/input/button/on* 属性, 原文件链接指向草稿); 两输入未变 | 通过 |
| 3 promote | `run5/logs/target-workspace.*`; `run5/logs/target-promote-removed-option.*` (`--review` 退出 2); `run5/logs/target-promote-bad-input.*` (退出 1, 原稿字节不变); `run5/logs/trace-atomic*` (内容逐字, v1 标记, 一次 rename, 原文件不变) | 通过 |
| 3 用例22 输入/目标并发 | `run5/logs/trace-{base,draft,output}.{events.jsonl,cmd,stdout,stderr,exit}`; `run5/files/trace/{case}/{input-before.bin,external-intended.bin,external-after.bin,PRODUCT.md,PRODUCT.base.md,acceptance.md}` | 通过 (ptrace 在指定窗口暂停, 外部 cp 进程改动后才恢复) |
| 4 check-ac 用例23/24 七例 | `run5/logs/target-ac-{valid,missing-goal,audit-rule,duplicate-goal,keyword,multiple-ac,free-tag,marker}.*` 与 `run5/files/ac/<case>/` | 全部达到预期退出码与报错 |
| 5 check-tech 子项 | `run5/logs/{base,target}-tech-{required,conditional,missing-1..4,typo-1..7,order}.*`; `run5/files/tech/*.md`; `run5/logs/base-tech-matrix.*` (基线与候选逐字节一致) | 通过 |
| 6 技术稿机械复制 | `run5/logs/target-tech-{copy,compare,formal}.*`; `run5/files/tech/{conditional.md,TECHNICAL.md}` | cp/cmp/正式机检均 0 |
| 7 milestone-01 编号复用 | `run5/logs/target-ac-valid.*`, `target-ac-duplicate-goal.*`; `run5/logs/changed-files.*` (编号逻辑未改) | 通过; 全仓范围审计属父级 |
| 8 pytest | `run5/logs/pytest.{cmd,stdout,stderr,exit}`; `run5/logs/pytest-collect.*`; `run5/logs/deps.*` (Python 3.11.2, gherkin-official 43.0.0, pytest 9.1.1) | 39 passed + 39 subtests, exit 0 |
| 9 check_skill.py (改动 SKILL.md) | `run5/logs/check-skill.*`, 及绑定最终提交的 `run5/logs/final-check-skill.*` | `workflow/to-spec/SKILL.md: OK`, exit 0 |
| 8/9 绑定最终提交复跑 | `run5/logs/final-pytest.*`, `run5/final-commit.txt` | 39 passed + 39 subtests exit 0; 代码状态与 8ce78be 相同 |
| 10 证据根核对 | `run5/environment.txt`; 本索引; `manifest.sha256` | 通过 |

## 验收标准 → 原件

| 验收标准 | 依据 |
| --- | --- |
| 验收1-24/26-30 全部场景与失败/边界分支有条款或 CLI 证据; AC-024 七例逐个达标 | `run5/text-mapping.md` (42 行) + `run5/logs/target-ac-*` |
| 规则 1-15 承接部分与技术接口/错误模式/安全有检查材料 | `run5/text-mapping.md` 第 2 节 + `run5/logs/scope-search.*` (规则9/10 搜索) + trace/pytest |
| review_id/--review 已移除无兼容; v1 固定; 原文/原子替换/输入与目标保护按真实入口验证 | `target-promote-removed-option.*`, `trace-*` |
| 复用 milestone-01 编号结果, 无重复汉化; 全仓审计交父级 | `text-mapping.md` 第 4 节 |
| 测试与格式检查留完整记录 | `pytest.*`, `pytest-collect.*`, `check-skill.*` |
| 环境阻塞项记未验证 | 见工单交付证据"未验证项" |

## 保留与清理

- 全部原件默认保留, 不清理; 未使用 `/tmp` 作唯一存放 (TMPDIR 指向各 run 的 `tmp/`, 随 run 目录保留).
- `run*/tmp` 为运行缓存 (uv 临时目录), 与原件同置但可重建, 不计入 `manifest.sha256`.