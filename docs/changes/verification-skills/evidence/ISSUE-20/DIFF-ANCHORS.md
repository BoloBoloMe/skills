# 差异表逐行对照上游原文 (ISSUE-20, TS-001)

本文件由 `check-diff-anchors.py --markdown` 生成, 表内引文由脚本按行号从上游原文与本地 SKILL.md 实地取出并断言命中, 不是手抄.

- 上游原文: `docs/changes/verification-skills/evidence/ISSUE-13/upstream/blast-radius-SKILL.md` (50 行), `benchmark-checklist-SKILL.md` (39 行), 固定 SHA `4382e687a50b8d2c5ce4d141d001186589cff8d5`.
- 本地文本: `workflow/blast-radius/SKILL.md` (94 行), `workflow/benchmark-checklist/SKILL.md` (126 行), 分支 `issue/20` 实现提交.
- "无对应行" 表示该差异是本地新增, 脚本用正则确认上游全文确实没有该概念, 避免把上游已有的东西记成新增.


### workflow/blast-radius

| 行 | 上游原文位置与引文 | 本地位置与引文 | 对照结论 |
| --- | --- | --- | --- |
| 1 | 第 2-4 行: `description: "Find what a change could break` | 第 2-4 行: `description: 调查变更在 diff 之外` | frontmatter 上游第 4 行原本就是 disable-model-invocation: true, 只改 description 措辞 |
| 2 | 第 7 行: `# Blast radius` | 第 7 行: `调查一个变更在别处会破坏什么` | 上游 H1 在本地没有对应标题, 本地从引言起 |
| 3 | 第 11 行: `Companion to `how` and `why`` | 第 15-25 行: `gh pr view` | 上游 companion 指针换成第 1 节内联历史定位命令 |
| 4 | 第 15-27 行: `### How sure are you` | 第 37-47 行: `## 3. 给每个事实标证据级别` | 上游 H2+H3 拍平成第 3 节与第 4 节 |
| 5 | 第 33 行: `Use `why` step 2 to pull the PR and commits` | 第 17-25 行: `git log --oneline -20` | 上游指针换成可直接执行的 git 命令 |
| 6 | 第 35 行: `Solid versus React` | 第 33 行: `运行时机 (注册时机, 异步, 卸载, 生命周期)` | 框架专名换成通用运行时机说法 |
| 7 | 第 36 行: `Same rules as `why`` | 第 66-68 行: `真实 file:line` | 诚实纪律内联到第 5 节 |
| 8 | 第 36 行: `a search that finds nothing is still an answer` | 第 68 行: `符号检索没有结果也是答案` | 空结果报告要求收紧为写明范围与边界 |
| 9 | 第 37 行: `Write a script or test that runs the real code` | 第 49-60 行: `## 4. 写可失败的证明脚本` | 一句要求扩成可失败脚本的完成标准 |
| 10 | 第 38 行: `run it as an `arena`` | 第 72-80 行: `reference/multimodel.md` | arena 产物流程换成 use-herdr/llm-select 承接 |
| 11 | 第 48 行: `Write it through `unslop`` | 第 92 行: `reference/report-style-zh.md` | 英文文风清单换成中文报告规则 |
| 12 | 无对应行; 全文无 `permission\|authoriz\|approv` | 第 55 行: `只读调查不需要额外授权` | 上游无写入授权句, 本地新增 |
| 13 | 无对应行; 全文无 `verifier\|acceptance\|delegate\|subagent` | 第 9 行: `自己调查并运行证明是我的角色` | 上游无角色句, 本地按 D025 新增 |
| 14 | 无对应行; 全文无 `only one model` | 第 77 行: `只有一款模型可用` | 上游无单模型缺口处理, 本地新增 |
| 15 | 第 46 行: `Before you merge` | 第 92 行: `不自动合并` | 上游只有合并前检查项, 没有交付边界句 |
| 16 | 第 48 行: `strip anything private` | 第 92 行: `对外发出前脱敏` | 原意保留 |

### workflow/benchmark-checklist

| 行 | 上游原文位置与引文 | 本地位置与引文 | 对照结论 |
| --- | --- | --- | --- |
| 1 | 第 2-4 行: `description: "Vet a perf measurement` | 第 2-4 行: `description: 报告或采信性能数字前的测量核查` | frontmatter 上游第 4 行原本就是 disable-model-invocation: true, 只改 description 措辞 |
| 2 | 第 7 行: `# Benchmark checklist` | 第 7 行: `# 性能测量核查` | H1 中文化, 层级不变 |
| 3 | 第 9-11 行: `one run is enough` | 第 98-108 行: `## 粗估与选型` | 粗估例外后移到粗估与选型节 |
| 4 | 第 13-17 行: `## Before you run anything` | 第 30-38 行: `## 测量前` | 三条测量前检查保留并收紧 |
| 5 | 第 19-27 行: `## The questions` | 第 40-96 行: `## 两侧按生产方式调优` | 单节七个编号问题拆成六个测量阶段节 |
| 6 | 第 21 行: ``pidstat`` | 第 78-82 行: `用分析器找限制因素时` | 工具名不逐项列, 限制因素规则保留 |
| 7 | 第 23 行: `Compare bytes per second with disk and network bandwidth` | 第 72 行: `每秒字节数对磁盘与网络带宽` | 物理上限三组算式补齐 |
| 8 | 第 24 行: `If the script does not count errors, add the count` | 第 58 行: `脚本没计数时` | 改为授权内独立脚本补计数 |
| 9 | 第 25 行: `at least 5 times, alternating` | 第 50 行: `每侧至少 5 次` | 交替重复与统计判断逐条保留 |
| 10 | 第 26 行: `measure the end-to-end path` | 第 76 行: `补测真实入口的端到端` | 端到端实测保留 |
| 11 | 第 27 行: `Lazy code` | 第 60 行: `无人迭代的生成器` | 工作是否真的发生保留并列举 |
| 12 | 第 29-34 行: `## Report` | 第 110-122 行: `## 判定` | Report 四条拆成判定与对外报告两节 |
| 13 | 第 36-39 行: `## Other perf material` | 第 86-96 行: `## 基线与脚本固定前` | 两套 playbook 指针换成检查接入要求 |
| 14 | 无对应行; 全文无 `permission\|authoriz\|approv` | 第 11 行: `## 输入与授权` | 上游无输入定义与写入授权, 本地新增 |
| 15 | 无对应行; 全文无 `temporary\|one-off\|throwaway` | 第 15 行: `## 一次性实验的边界` | 上游无一次性实验边界, 本地新增 |
| 16 | 无对应行; 全文无 `merge\|push` | 第 124 行: `这份清单只产出草稿与判定` | 上游无交付边界, 本地按 D024 新增 |

OK 两份差异表逐行指到上游原文与本地行, 调用方式与标题结构说法已更正
