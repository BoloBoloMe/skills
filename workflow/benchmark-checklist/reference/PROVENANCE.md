# 来源, 许可与行为差异

本技能是固定上游版本的复刻与适配, 不是原创. 本文件记录固定来源, 随包许可, 逐项行为差异, translate-a-skill 第 7 节校验材料, 以及行为保真演练入口, 供后续核对.

## 固定来源

- 仓库: `cursor/plugins`, 上游路径 `pstack/skills/benchmark-checklist/SKILL.md`.
- 固定 SHA: `4382e687a50b8d2c5ce4d141d001186589cff8d5`. 不追浮动 main: 上游 main 之后有更新, 本副本以该 SHA 为唯一输入.
- 只读获取命令与结果 (2026-10-19, 无代理):

```bash
curl -sS -m 20 -w "%{http_code} %{size_download}\n" -o /tmp/iss13-upstream/skills_benchmark-checklist_SKILL.md \
  https://raw.githubusercontent.com/cursor/plugins/4382e687a50b8d2c5ce4d141d001186589cff8d5/pstack/skills/benchmark-checklist/SKILL.md
curl -sS -m 20 -w "%{http_code} %{size_download}\n" -o /tmp/iss13-upstream/LICENSE \
  https://raw.githubusercontent.com/cursor/plugins/4382e687a50b8d2c5ce4d141d001186589cff8d5/pstack/LICENSE
```

| 文件 | HTTP | 字节 | 行数 | sha256 |
| --- | --- | --- | --- | --- |
| 上游 `benchmark-checklist/SKILL.md` | 200 | 5002 | 39 | `ba109e96c8f6c1c391baccf19e5d11e14370df7b3f2605e1572cd565a6c0fca0` |
| 上游 `pstack/LICENSE` | 200 | 1067 | 21 | `bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e` |

上游原文副本 (只读抓取, 未改字节) 存于 `docs/changes/verification-skills/evidence/ISSUE-13/upstream/benchmark-checklist-SKILL.md` 与同目录 `pstack-LICENSE.txt`.

## 随包许可

- `workflow/benchmark-checklist/LICENSE` 与上游 `pstack/LICENSE` 逐字节相同, sha256 `bc957ca6bee02792566a1a028d105e02e247c6e77cf057061674273da77b200e`.
- 内容是完整 MIT: 版权行 `Copyright (c) 2026 Lauren Tan`, 授权段, 版权与许可必须随附的条件段, 以及全大写免责段 (无担保, 不承担任何责任).
- 不以作者名或仓库链接代替许可正文: 上述文本就在本包内, 不依赖外部材料.

## 逐项差异表

字段固定为源版位置, 目标版位置, 影响, 处理决定. 每行一条差异, 不把范围缩减藏在普通翻译里.

| 源版位置 | 目标版位置 | 影响 | 处理决定 |
| --- | --- | --- | --- |
| frontmatter `description` 英文触发句 ("Use when you run a benchmark or report a speedup...") | frontmatter `description` 单行中文摘要, 列出覆盖的核查项; 保留 `disable-model-invocation: true` | 调用方式从模型自动触发改为用户点名 | 按 DECISIONS D022 用户调用, 触发词只作人类可读摘要 |
| 标题 `# Benchmark checklist` | `# 性能测量核查` | 标题中文化, 层级不变 | 保留 (标题层级未因翻译改变) |
| 引言段与 "one run is enough ... never a ballpark" 段 | 引言段保留四种判定; 粗估例外后移到 `## 粗估与选型` | 粗估例外的位置从开头移到选型节, 内容不减 | 保留: 例外条件 (单次仍查第 4/7 问, 选型永远不算粗估) 逐条保留 |
| `## Before you run anything` 三条 | `## 测量前` | 三条保留, 另补脚本随机扰动/固定种子记录与分析器单跑不进报告 | 保留收紧 |
| `## The questions` 1 到 7 | 拆成 `## 测量前`, `## 两侧按生产方式调优`, `## 重复与波动`, `## 错误计数与工作是否真的发生`, `## 收益上限与端到端`, `## 基线与脚本固定前` 六节, 问题编号只在第 4 与第 7 问引用 | 上游单节七个编号问题按测量阶段拆开 | 接受: 每个问题逐条保留, 无遗漏; 编号引用改为按节名加原编号 |
| 第 1 问的工具清单 (`top`, `pidstat`, `node --cpu-prof`, `py-spy`, `perf`, `strace -c`) | 只写"分析器或追踪器", 未逐项列工具名 | 具体工具提示减少 | 记录在案, 不改正文: 工具名属示例, 规则 (限制因素单独跑, 该次数字不进报告, 负载生成器先饱和也算限制因素) 全部保留 |
| 第 3 问 "Compare bytes per second with disk and network bandwidth, operations per second times cost per operation with your cores..." | `## 收益上限与端到端` 的物理上限段: 每秒字节数对磁盘与网络带宽, 每秒操作数乘每操作成本对核心数, 省下的时间对被改动那一段自己的耗时 | 初版只保留占比算式 (占 10% 的段全删, 上限约 11%), 漏掉带宽与核心两组 | 已补齐: 与 TECHNICAL 已确认的"用带宽/核心时间/占比核对物理上限"一致, 见本 ISSUE 提交 |
| 第 4 问 "If the script does not count errors, add the count" | `## 错误计数与工作是否真的发生`: 在授权的独立实验脚本里补计数与正确性校验; 冻结产品源码不改, 只能改源码才拿得到计数时报缺口 | 上游允许直接给脚本加计数, 本地以冻结源码与一次性实验边界收紧 | 保留收紧: 不改产品源码, 改为报缺口 |
| 第 5 问 (每侧至少 5 次交替, 中位数与极差, 差距小于波动为无可测差异, 接近时用秩和检验或工具统计) | `## 重复与波动` | 逐条保留, 另补"不新建统一显著性阈值, 不靠中位数大小或单次结果宣布赢家" | 保留收紧 |
| 第 6 问 (微结果旁实测用户端到端并报占比) | `## 收益上限与端到端` | 保留 | 保留 |
| 第 7 问 (工作真的发生在计时区且结果被用上) | `## 错误计数与工作是否真的发生` 后半段 | 保留, 列举无迭代生成器, 未 await 异步, JIT 丢弃, 超时 | 保留 |
| `## Report` 四条 (判定先行, 数字带单位/次数/极差/限制因素, 无法下结论条件, PR 只一个主数字 per the **Opening a PR** playbook) | `## 判定` 与 `## 对外报告` | 上游 playbook 指针改为自足规则: 主数字带单位与前后对照加证据链接, 完整次数/极差/失败数/限制因素留在链接材料, 内部证据不缩减 | 按 DECISIONS D021 自足, 不指向上游 playbook |
| `## Other perf material` (Perf issue 与 Hillclimb playbook 两个指针) | `## 基线与脚本固定前` | 改成自足步骤: 规划前先审基线方法, 固定脚本前必须有错误数与工作量输出, 缺就补并重跑, 只能改产品源码才做得到时报缺口 | 按 D021 保留检查接入要求, 不搬两套优化流程 |
| 上游无输入定义与写入授权 | `## 输入与授权` | 新增: 调用者给主张, 脚本, 两侧条件, 已有材料; 本清单不授予改冻结源码, 新增正式用例或新权限 | 本地新增边界, 不改上游检查要求 |
| 上游无一次性实验边界 | `## 一次性实验的边界` | 新增: 非正式 TC 标记, 授权范围, 只动独立脚本与临时数据, 清理写进记录, 内部结果不等于成品入口通过 | 本地新增边界, 不改上游检查要求 |
| 上游无交付边界 | `## 对外报告` 末段: 本清单只产出草稿与判定, 提交/推送/开 PR/合并由使用者做 | 新增交付边界 | 按 DECISIONS D024 |

## 没有搬入的部分

- 上游 `poteto-mode` 的提交, 发布, 自动合并流程与 PR 组织形态.
- 上游 perf-issue 与 hillclimb 两个 playbook 的完整优化流程; 只保留"基线用于规划前要审"与"测量脚本固定前必须自带错误数与工作量输出"两条检查接入要求.
- 不新建统一显著性阈值, 不新建结果 JSON 协议或自动评测平台.

## translate-a-skill 第 7 节校验

`check_skill.py` 只查 frontmatter 与名称一致性, 不当标点或翻译忠实性校验器. 忠实性与标点用 translate-a-skill 第 7 节的既有命令, 结果如下 (2026-10-19, 提交见本目录 HANDOFF).

命令 1, 全角标点扫描:

```bash
rg -n "[\x{ff0c}\x{3002}\x{ff1b}\x{ff1a}\x{ff01}\x{ff1f}\x{3001}\x{ff08}\x{ff09}\x{3010}\x{3011}]" workflow/benchmark-checklist/SKILL.md
```

无命中 (rg 退出码 1). 本包 `reference/*.md` 与本文件同样无命中.

命令 2, 残留英文审查 (原样列出命中, 不是要求清零):

```bash
rg -o "[A-Za-z][A-Za-z0-9_./:@|*\-]*" workflow/benchmark-checklist/SKILL.md | sort | uniq -c | sort -rn
```

| 命中 | 保留理由 |
| --- | --- |
| `uptime`, `nproc` | 命令名 |
| `await` | 代码关键字, 指无人 await 的异步任务 |
| `p50`, `ms`, `r` | 指标名, 单位, 算式变量 |
| `A`, `B`, `B...` | 交替测量的两侧标号 |
| `TC` | 本仓库既有术语 (test case) |
| `PR` | 平台概念, 无稳定中文对应词 |
| `Git`, `CPU` | 既有通用缩写 |
| `blast-radius`, `benchmark-checklist` | 技能名 |
| `name:`, `description:`, `disable-model-invocation:` | frontmatter key |
| `true` | frontmatter 取值 |

命令 3, frontmatter 与标题结构:

```bash
rg -n "^(|name:|description:|license:|compatibility:|metadata:|allowed-tools:|disable-model-invocation:|# |## )" workflow/benchmark-checklist/SKILL.md
```

命中 frontmatter 三行 (`name`, `description`, `disable-model-invocation`), 一个 H1 (`# 性能测量核查`) 与十一个 H2 (`## 输入与授权` 到 `## 对外报告`). 上游是 H1 加四个 H2 加单节内七个编号问题; 拆节差异与理由见上表.

通读测试: 全文按中文直接可执行, 每条检查都能独立照着做; 未发现直译腔或需回看原文才能确定顺序处.

## 行为保真演练

代表场景与对照结论写在 `docs/changes/verification-skills/evidence/ISSUE-13/TS-002-drill.md`, 含临时项目路径与提交, 会话名, 加载方式, 命令与原始输出. 对照口径是本文件的逐项差异表: 演练要确认汉化后仍然按每侧至少 5 次交替测量, 报中位数与极差, 计失败数并核输出正确性, 结论用四种判定之一.
