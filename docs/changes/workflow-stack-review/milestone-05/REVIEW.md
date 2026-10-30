# milestone-05 独立文档复核

任务: `workflow-stack-review/milestone-05-review`.
本报告只复核指定目标与 AC-05-01 至 AC-05-07, 不是实现记录, 不是整条路线或正式终点验收.

## 结论

- AC-05-01 未完全满足: 公共授权主体已改为指针, 验收特有语义保留, 但仍有一处共用规则内联重复. 详见下文已证实问题.
- AC-05-02 至 AC-05-06 的文档要求和规定的三次静态检查满足. 这不消除 AC-05-01 的问题.
- AC-05-07: 本复核会话的命令记录符合操作限制; 实现期间是否从未同步或修改安装目录/全局配置, 未独立证实. 仓库差异不能证明这类历史上的未发生行为.
- 未发现授权范围, 原始数据保留, 验收报告状态或旧有执行分工被删漏. 不据此推断 LLM 实际遵从率或安装效果.

## 身份, 版本与判据

- 独立 pi 会话与 mailboxSessionId: `01a18c58-8d8c-7542-b650-365bc3d03d8a`.
- `mailbox_listen(action="start")` 实际返回 `running=true`, piSessionId 与 mailboxSessionId 相等. 地址不同于协调方 `01a18bb7-daad-71ad-b7ab-ba6b1373fc72`.
- 会话头原件: `/home/bolo/.pi/agent/sessions/--home-bolo-Workspace-refactor-skill-around-verification--/2026-10-30T10-26-16-077Z_01a18c58-8d8c-7542-b650-365bc3d03d8a.jsonl:1`.
- 身份文件: `/home/bolo/docs/identity.md`, 容器 `swt-refactor-skill-around-verification`, 分支 `refactor-skill-around-verification`, 工作目录 `/home/bolo/Workspace/refactor-skill-around-verification`.
- 范围基线: `57e93dce741f343ec45b567b8eec6ba6a1e684c9`.
- 实现目标: `14c624f0b7f5b6eda9df722bff6fb4826ee1bc5f`.
- 标准提交: `57e93dce741f343ec45b567b8eec6ba6a1e684c9`, 文件 `docs/changes/workflow-stack-review/ACCEPTANCE.md`, 只取 AC-05-01 至 AC-05-07.
- 复核开始及静态检查时 HEAD: `5e5175b711b691ed2aecc67f46227ee446bd16ce`.

会话头通过 read 工具直接读取, 原始内容如下:

```json
{"type":"session","version":3,"id":"01a18c58-8d8c-7542-b650-365bc3d03d8a","timestamp":"2026-10-30T10:26:16.077Z","cwd":"/home/bolo/Workspace/refactor-skill-around-verification"}
```

2026-10-30T10:32:06Z 执行:

```bash
git show -s --format='commit=%H%ncommitter_time=%cI%nauthor_time=%aI' 14c624f0b7f5b6eda9df722bff6fb4826ee1bc5f
```

原始输出:

```text
commit=14c624f0b7f5b6eda9df722bff6fb4826ee1bc5f
committer_time=2026-10-30T10:24:12+00:00
author_time=2026-10-30T10:24:12+00:00
```

会话创建时间晚于实现提交 2 分 4.077 秒. 本会话从独立复核任务开始, 未接收实现过程或参与实现/修复, 未读取作者自检报告正文. 时间和本会话工具记录是独立性的可核对依据, 不是对同账户全部其他会话历史的证明.

已读取仓库 `AGENTS.md`, 已调用 `verification-contract` 与 `writing-for-llm`, 并读取后者的 `SKILL-MECHANICS.md` 和 `GLOSSARY.md`. 检查选择限于本次已确认的文档标准, 文本差异, 指针落点与已有静态校验器. 不以静态检查声称 skill 的实际执行行为已验证不变.

## 独立追查范围

2026-10-30T10:27:33Z 从基线到目标执行 `git diff --name-status`, 随后独立读取完整差异. 实际只有五个文件:

```text
M	README.md
M	workflow/blast-radius/SKILL.md
M	workflow/blast-radius/reference/PROVENANCE.md
M	workflow/maintain-verification-skill/SKILL.md
M	workflow/verify-change/SKILL.md
```

完整差异入口:

```bash
git diff --no-ext-diff --unified=5 57e93dce741f343ec45b567b8eec6ba6a1e684c9 14c624f0b7f5b6eda9df722bff6fb4826ee1bc5f -- README.md workflow/blast-radius/SKILL.md workflow/blast-radius/reference/PROVENANCE.md workflow/maintain-verification-skill/SKILL.md workflow/verify-change/SKILL.md
```

命令实际执行成功, 所在工具调用退出码 0. 下列位置均指实现目标中的行号, 不是作者自检的描述:

| 修正项 | 差异位置与实际观察 |
| --- | --- |
| 验收授权 | `workflow/verify-change/SKILL.md:59-62`, 去掉批准绑定范围, 同范围复跑, 换范围重批及工具不授予权限等成段复述, 改指公共授权节; 仍有一处短句重复, 见已证实问题 |
| 调查证明授权 | `workflow/blast-radius/SKILL.md:65`, 原先的先问要求改为按公共授权节获批 |
| 一次性实验授权/清理 | 同文件 `:74,79`, 先指授权节, 清理同时指授权与原始数据两节 |
| 配方复跑完成标准 | `workflow/maintain-verification-skill/SKILL.md:67`, 正面界定配方当前可执行与本次复跑结果 |
| 调查者角色 | `workflow/blast-radius/SKILL.md:9`, 去掉依赖外部定义的角色称谓, 按调用方分工描述组织产品验收的情形 |
| 调用关系说明 | `README.md:9-15`, 句子在目录标题下且早于第一张 skill 表 |
| 来源说明两行 | `workflow/blast-radius/reference/PROVENANCE.md:48-49`, 分别同步授权指针和组织产品验收的角色说明 |

独立执行 `git diff --name-status 14c624f0b7f5b6eda9df722bff6fb4826ee1bc5f 5e5175b711b691ed2aecc67f46227ee446bd16ce`, 只列出新增 `docs/changes/workflow-stack-review/milestone-05/IMPLEMENTATION.md`. 未读取其正文或采用其结论.
公共安全材料为 `workflow/verification-contract/SAFETY.md` 和通向它的 `workflow/verification-contract/SKILL.md`. 另核对来源说明引用的 `docs/changes/verification-skills/DECISIONS.md:228-235` 的 D025, 只用来检查已有分工与历史原文未变, 不添加验收标准.

## 逐条结果

### AC-05-01: 未完全满足, 有残留重复

- `workflow/verify-change/SKILL.md:59` 的相对链接抵达 `workflow/verification-contract/SAFETY.md`, 明指实际存在的 `写入与授权` 节.
- 已删除的共用细则由 `SAFETY.md:19-22` 承接: 批准前说明对象/操作/保留和访问方式, 批准范围绑定, 同范围复跑, 换任一范围重新授权, 工具不自动授予权限. 因而删除旧批准句未造成范围授权语义缺失.
- `SKILL.md:59` 明确保留获批前相关项记未检查. `:60` 原样保留派工单写入批准范围, 要求验收者逐次记录, 超范围验收者停下且组织者不替其扩权三条.
- `:61-62` 的数据留存, 实例停止/清理记录及完成标准未改. `verification-contract/SKILL.md:22` 继续指向公共安全文档, 数据保留可抵达 `SAFETY.md:11-15`.
- 但 `:59` 仍内联 `默认只读.`. 这是 `SAFETY.md:19` 的同文共用规则, 不属本 AC 指定保留的验收特有条款. 不能将本项记为完全去重.

### AC-05-02: 文本要求满足

- 第 4 节 `:65` 的授权指针和第 5 节 `:74` 的实验授权指针均抵达 `SAFETY.md:17-22`.
- 第 5 节 `:79` 的清理指针明确要求同时执行 `写入与授权` 与 `原始数据`. 后者实际规定默认保留, 停止实例也保留, 复跑隔离, 清理旧数据先留可查看副本, 其他删除须批准, 截图/日志不代替原始数据.
- 第 4 节的仓库外脚本或报告附全文, 源码/测试原样, 脚本全文与输出交接未删. 第 5 节的批准独立脚本/临时目录, 不改源码/既有测试/配置, 非正式 TC 标记, 临时数据位置, 清理结果交接, 未跑产品入口仍记未运行等均保留.
- `:74` 与 `:79` 仍各有按范围清理的短提示, `:65` 仍有只读调查不需额外授权的既有提示. 这些没有展开另一套重新授权或原始数据规则; 清理执行约束已明确交给同一公共文档. 本项不声称所有词义重叠均已消失, 也不将原有实验范围/交接提示另立为新增不合格条件.

### AC-05-03: 文本要求满足

`workflow/maintain-verification-skill/SKILL.md:67` 已用正面结果限定结论: `配方当前可执行与本次复跑结果`. 该完成标准不再点名 `verify-change`, 全文也无该名字. 原有新子会话, 全部新改功能及入口, 加载来源, 操作/取证/保留记录均保留. `:10,78` 继续约束配方不另立标准, 范围内通过不等于全项目验证. 未把配方复跑改称产品验收.

### AC-05-04: 文本要求满足

`workflow/blast-radius/SKILL.md:9` 保留使用者自己调查和运行证明. 只有按调用方分工组织产品验收的情形才要求实际验收子会话, 没有改成所有调查都另起指挥层. 多模型调查可以委派的原句也保留.
`PROVENANCE.md:48` 与新的授权指针相符, `:49` 与组织者不亲自验收/须派实际验收子会话相符. 本次该文件恰好只改这两行. D025 原文保留, 与上述分工一致; `verify-change/SKILL.md:52-55,71` 的方法交实际验收者调用的分工也未改.
基线到目标对 `docs/changes/verification-skills/DECISIONS.md` 执行 `git diff --exit-code` 无输出, 实际退出码 0. 当前文件与目标比较同样退出码 0, 未用改写历史决策消除差异.

### AC-05-05: 文本要求满足

`README.md:9` 为 `## 目录`, `:11` 是新增调用关系口径, `:13` 是通用技能小节, `:15` 才开始第一张 skill 表. 句子明确只有执行调用进调用图, 引用, 分工声明与重新派活不算调用边. 内容与位置均直接见基线到目标差异.

### AC-05-06: 证据要求满足

五处正文修正, README 句子和来源说明两行均已在上表与目标差异逐项定位. 三个修改后的 SKILL.md 均在当前仓库实际执行指定校验器, 各退出码为 0. 运行前已证明当前文件与目标一致, 原始命令/输出/UTC 时间及版本见下文. 本报告由创建晚于实现提交的独立会话产生, 绑定完整目标提交. 此项满足不表示其他 AC 自动通过.

### AC-05-07: 本会话记录范围满足, 实现期间未全面独立证实

本会话未执行 `sync-to-pi.py`, 未修改真实已安装 skills 或 agent 全局配置, 未新增测试脚本, 未启动产品/测试服务或 LLM 行为实验. 已安装 skills 未作为修改或同步目标; 仅加载复核/信箱指引并运行信箱脚本. 信箱身份准备与监听是任务明确要求的会话级操作, 未将仓库内容同步到安装目录.
上述否定结论只涵盖本会话可复核的工具/命令记录, 不覆盖实现者此前全部操作或其他进程. 本次只新增本报告并仅提交它. 不读取或修改 ROADMAP.json 正文/数据, 不提交其状态变化. 一次工作区 `git diff --name-only` 的排除项未命中实际嵌套位置, 因而仅列出了路线图文件路径; 未输出或查看其正文, 随后改用 `:(glob,exclude)**/ROADMAP.json` 排除. 未取用路线图数据作为判据.
模型实际遵从率, 已安装目录同步效果, 全局配置的历史状态及实现期是否从未运行同步, 均不在本次已验证范围. 不把没有仓库差异当成这些事项已经获得全面证明.

## 版本一致性与指针实查原件

2026-10-30T10:29:07Z, 在三次校验之前执行:

```bash
git diff --exit-code 14c624f0b7f5b6eda9df722bff6fb4826ee1bc5f -- README.md workflow/blast-radius/SKILL.md workflow/blast-radius/reference/PROVENANCE.md workflow/maintain-verification-skill/SKILL.md workflow/verify-change/SKILL.md workflow/verification-contract/SAFETY.md workflow/verification-contract/SKILL.md general/writing-for-llm/check_skill.py docs/changes/workflow-stack-review/ACCEPTANCE.md
rc=$?; printf 'exit_code=%s\n' "$rc"
```

原始输出:

```text
exit_code=0
```

同一工具调用执行基线到目标对 SAFETY.md, verification-contract/SKILL.md, check_skill.py 与 ACCEPTANCE.md 的 `git diff --exit-code`, 原始输出为 `baseline_support_diff_exit_code=0`, 无差异正文. 对五个变更文件执行 `git diff --check` 的原始输出为 `diff_check_exit_code=0`, 无诊断. 这些退出码均紧接对应命令读取, 不是以最后一个打印命令的退出码冒充检查退出码.

目标 blob 与当前 `git hash-object` 逐项一致:

| 文件 | 目标与当前共同 blob |
| --- | --- |
| `workflow/verify-change/SKILL.md` | `b2a2ea80f2447210c7db4c6dfc6615913b8a6de1` |
| `workflow/blast-radius/SKILL.md` | `9cf477c19aa38d759f898d26313151ca911cb6ab` |
| `workflow/maintain-verification-skill/SKILL.md` | `5a0d9c185dca886b568a7fbbf3d54393d8f2db79` |
| `general/writing-for-llm/check_skill.py` | `65f47f5652f5541a04964ea6240bc978ae318823` |
| `docs/changes/workflow-stack-review/ACCEPTANCE.md` | `1d692fc4d9bf46421b02e35b41d8be3f4ef9e398` |

blob 命令分别为 `git rev-parse <提交>:<路径>` 与 `git hash-object <路径>`, 未使用写入对象的 `-w`. 标准 blob 同时与标准提交一致. 2026-10-30T10:33:19Z 再次执行上述目标内容比较, 实际仍为 `target_contents_exit_code=0`, HEAD 仍为已记录的 `5e5175b711b691ed2aecc67f46227ee446bd16ce`.

2026-10-30T10:32:06Z 执行指针路径与标题实查:

```bash
realpath -e workflow/verify-change/../verification-contract/SAFETY.md workflow/blast-radius/../verification-contract/SAFETY.md workflow/maintain-verification-skill/../verification-contract/SAFETY.md
rc=$?; printf 'realpath_exit_code=%s\n' "$rc"
rg -n '^## (写入与授权|原始数据)$' workflow/verification-contract/SAFETY.md
rc=$?; printf 'section_lookup_exit_code=%s\n' "$rc"
```

原始输出:

```text
/home/bolo/Workspace/refactor-skill-around-verification/workflow/verification-contract/SAFETY.md
/home/bolo/Workspace/refactor-skill-around-verification/workflow/verification-contract/SAFETY.md
/home/bolo/Workspace/refactor-skill-around-verification/workflow/verification-contract/SAFETY.md
realpath_exit_code=0
11:## 原始数据
17:## 写入与授权
section_lookup_exit_code=0
```

链接使用文件路径加正文节名, 不是带片段的 Markdown 锚点. 文件真实存在, 所指节名逐字匹配, 并已读取相应节全文; 不只凭链接字面判断有效.

## 三个 SKILL.md 的实际校验原件

工作目录为上述当前仓库. 2026-10-30T10:29:23Z 的环境命令:

```bash
uv --version
PYTHONDONTWRITEBYTECODE=1 uv run python --version
uname -srm
git rev-parse HEAD
```

原始输出:

```text
uv 0.13.1 (x86_64-unknown-linux-gnu)
Python 3.11.2
Linux 7.0.0-31-generic x86_64
5e5175b711b691ed2aecc67f46227ee446bd16ce
```

以下为实际运行的三条检查命令. 每条命令前后分别打印 UTC 时间, 命令后立即用 `rc=$?` 取得实际退出码并打印. 全部设置 `PYTHONDONTWRITEBYTECODE=1`, 校验器为仓库中已读取源码的 `general/writing-for-llm/check_skill.py`, 不是安装目录副本.

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python /home/bolo/Workspace/refactor-skill-around-verification/general/writing-for-llm/check_skill.py /home/bolo/Workspace/refactor-skill-around-verification/workflow/verify-change/SKILL.md
PYTHONDONTWRITEBYTECODE=1 uv run python /home/bolo/Workspace/refactor-skill-around-verification/general/writing-for-llm/check_skill.py /home/bolo/Workspace/refactor-skill-around-verification/workflow/blast-radius/SKILL.md
PYTHONDONTWRITEBYTECODE=1 uv run python /home/bolo/Workspace/refactor-skill-around-verification/general/writing-for-llm/check_skill.py /home/bolo/Workspace/refactor-skill-around-verification/workflow/maintain-verification-skill/SKILL.md
```

原始检查输出及紧邻的时间/退出码记录:

```text
START verify-change 2026-10-30T10:29:23Z
/home/bolo/Workspace/refactor-skill-around-verification/workflow/verify-change/SKILL.md: OK
exit_code=0
END verify-change 2026-10-30T10:29:23Z

START blast-radius 2026-10-30T10:29:23Z
/home/bolo/Workspace/refactor-skill-around-verification/workflow/blast-radius/SKILL.md: OK
exit_code=0
END blast-radius 2026-10-30T10:29:23Z

START maintain-verification-skill 2026-10-30T10:29:23Z
/home/bolo/Workspace/refactor-skill-around-verification/workflow/maintain-verification-skill/SKILL.md: OK
exit_code=0
END maintain-verification-skill 2026-10-30T10:29:23Z
```

这是本轮直接观察, 非引用作者旧结果. 校验器只查 frontmatter/name/调用方式等规定的静态格式, 不验证链接, 文档去重, 语义保真或 LLM 遵从率. 后几项由本报告的文本核对承担或明确留为未验证, 不借 `OK` 扩大结论.

## 已证实问题

`workflow/verify-change/SKILL.md:59` 与 `workflow/verification-contract/SAFETY.md:19` 同时保留 `默认只读.`. 公共安全文档 `:3` 规定共用规则只在该处维护, 其他 skill 用指针而不复述; AC-05-01 又要求共用写入授权改用指针且不保留第二套共用规则. 该短句不是明确要求保留的验收特有语义.
这是范围很小的去重残留, 不是已观察到越权写入或安全执行失败. 不将其夸大为实际安全事故, 也不因主体规则已外提而隐去这处重复. 交回协调方处理; 本会话不改正文或标准, 不自行接受例外.

## 待核实疑点与局限

- 未见实现期违反同步/安装目录限制的直接证据. 但未独立检查实现者完整操作记录, 因而不能全面证明 AC-05-07 的实现期否定性断言. 若后续要求对此下完整结论, 仍缺可复核的实现期实际命令/操作记录; 作者自检结论本身不足以补齐.
- 实际观察: 本轮 git 差异, 文件正文/标题, 版本 blob, 会话头, 校验器输出与实际退出码.
- 文本推断: 公共规则经指针承接后语义未漏, 角色与结论边界未扩大. 这些是按已确认文档标准作出的静态判断, 不是 LLM 按文档运行的结果.
- 未验证: LLM 实际遵从率, 安装/同步效果, 产品实际运行, 其他里程碑, 整条路线或终点验收. 本任务没有为这些事项启动产品/测试服务, 运行行为实验或新增脚本.
- 没有运行会产生产品原始数据的实验. 本轮原始检查输出保存在本报告及本会话原生工具记录中; 未以摘要替代三次检查的原始结果, 未清理证据.

本报告不关闭 milestone-08, 不宣称正式验收或整条路线通过. 仍需后续按已确认流程处理问题/缺口并逐项确认.
