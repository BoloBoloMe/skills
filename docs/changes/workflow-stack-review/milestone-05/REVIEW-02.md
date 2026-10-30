# milestone-05 返修独立文档复核

任务: `workflow-stack-review/milestone-05-review`.
只复核本轮目标与既定 AC-05-01 至 AC-05-07. 首轮失败观察保留, 不覆盖 `REVIEW.md`, 不代表其他里程碑或正式终点验收.

## 结论

- AC-05-01 的首轮重复问题已在新目标中消除. AC-05-01 至 AC-05-06 的文档/静态证据要求满足.
- AC-05-07 已补查指定原实施和返修会话的原始工具调用及结果. 有返回的操作未见同步调用或直接修改已安装 skills/agent 全局配置的操作; 但返修日志有一条生成错误且没有对应工具结果的记录, 执行状态仍未证实. 保留这个日志缺口, 不报本项全面通过.
- 本轮没有新发现的已证实文本问题. 记录缺口不等于已经发生越权操作, 也不等于已经证明没有发生.
- 三个 SKILL.md 均在核对新目标一致后重新实跑仓库校验器, 实际退出码各为 0. 不把静态检查扩大为 LLM 遵从率或安装效果证明.

## 身份, 版本与判据

- 独立会话及 mailboxSessionId: `01a18c58-8d8c-7542-b650-365bc3d03d8a`, 本轮 `mailbox_listen(status)` 返回同一 piSessionId, `running=true`.
- 会话创建: `2026-10-30T10:26:16.077Z`, 原件 `/home/bolo/.pi/agent/sessions/--home-bolo-Workspace-refactor-skill-around-verification--/2026-10-30T10-26-16-077Z_01a18c58-8d8c-7542-b650-365bc3d03d8a.jsonl:1`.
- 容器/分支/目录沿用首轮: `swt-refactor-skill-around-verification`, `refactor-skill-around-verification`, `/home/bolo/Workspace/refactor-skill-around-verification`.
- 范围基线及标准提交: `57e93dce741f343ec45b567b8eec6ba6a1e684c9`.
- 唯一判据: 上述提交的 `docs/changes/workflow-stack-review/ACCEPTANCE.md`, AC-05-01 至 AC-05-07. 未采用其他未确认讨论改变判据.
- 原实现目标: `14c624f0b7f5b6eda9df722bff6fb4826ee1bc5f`.
- 本轮新目标: `6d0c4b25b4b8e84bd45c43549d442dd8cfb29395`.
- 本轮开始及三次校验时 HEAD: `572da571c68925bd3c6e8dedc5a1f82c3984057b`.
- 首轮报告: `c8a2f9a2ef5ec1bcf67e6f822e454c203e09b92c:docs/changes/workflow-stack-review/milestone-05/REVIEW.md`.

这是原独立复核会话的续查, 不是新开于返修之后的会话. 会话创建晚于原实现提交, 但早于返修提交, 不以创建时间冒充未参与返修的全部证明.
本会话原生记录 `:44,48` 显示返修提交之前的 write/edit 目标都只是首轮 `REVIEW.md`, 时间分别为 `10:36:31.247Z` 和 `10:37:32.388Z`; 首轮报告提交只新增该文件. 实际返修由另一会话完成, 其 edit 与提交记录见下文. 本会话没有修复被核正文, 本轮只新增本报告.
沿用已调用的 `verification-contract` 和 `writing-for-llm` 的文档检查要求. 不执行同步, 不改安装目录/全局配置, 不新增测试脚本或开展产品/LLM 行为实验.

## 版本一致性与旧观察适用性

2026-10-30T10:49:38Z 独立检查:

```bash
git diff --no-ext-diff --unified=3 14c624f0b7f5b6eda9df722bff6fb4826ee1bc5f 6d0c4b25b4b8e84bd45c43549d442dd8cfb29395 -- README.md workflow/blast-radius/SKILL.md workflow/blast-radius/reference/PROVENANCE.md workflow/maintain-verification-skill/SKILL.md workflow/verify-change/SKILL.md workflow/verification-contract/SAFETY.md workflow/verification-contract/SKILL.md general/writing-for-llm/check_skill.py docs/changes/workflow-stack-review/ACCEPTANCE.md
```

实际只有 `workflow/verify-change/SKILL.md:59` 一行变化, 只删除指针前的 `默认只读.`. 第 5 步其他内容未变. 又检查首轮报告提交到新目标的名称差异, 只列出 `M workflow/verify-change/SKILL.md`, 未借返修改其他文件.
新目标到当时 HEAD 的名称差异只列出新增 `docs/changes/workflow-stack-review/milestone-05/REPAIR.md`. 未读取该自检正文或采用其结论.

同一时间执行新目标到当前工作区的 `git diff --exit-code`, 路径为上述五文件及 SAFETY.md, verification-contract/SKILL.md, check_skill.py, ACCEPTANCE.md. 无差异正文, 紧接命令读取的实际退出码为 `new_target_worktree_exit_code=0`. 对首轮报告执行与 `c8a2f9a2ef5ec1bcf67e6f822e454c203e09b92c` 的比较, 实际为 `original_review_unchanged_exit_code=0`.

2026-10-30T10:53:52Z 对以下未变输入执行旧目标到新目标的 `git diff --exit-code`:

```text
README.md
workflow/blast-radius/SKILL.md
workflow/blast-radius/reference/PROVENANCE.md
workflow/maintain-verification-skill/SKILL.md
workflow/verification-contract/SAFETY.md
workflow/verification-contract/SKILL.md
general/writing-for-llm/check_skill.py
docs/changes/workflow-stack-review/ACCEPTANCE.md
docs/changes/verification-skills/DECISIONS.md
```

原始退出码输出为 `unchanged_old_observation_inputs_exit_code=0`, 无差异正文. 因而首轮对 AC-05-02 至 AC-05-05 的观察仍适用于这些完全相同的输入; 本轮仅改 verify-change 的短句不会改变这些观察的文档条件. 引用的是旧观察, 不冒充本轮重跑.
基线到新目标对五个被核文件执行 `git diff --check`, 实际输出 `new_range_diff_check_exit_code=0`. 对同一路径范围的名称差异仍恰好为原五文件.

运行前目标 blob 与当前 `git hash-object` 逐项相等:

| 文件 | 新目标与当前共同 blob |
| --- | --- |
| `workflow/verify-change/SKILL.md` | `ed8d4934bca0283c3d49f584b5196588a30fce04` |
| `workflow/blast-radius/SKILL.md` | `9cf477c19aa38d759f898d26313151ca911cb6ab` |
| `workflow/maintain-verification-skill/SKILL.md` | `5a0d9c185dca886b568a7fbbf3d54393d8f2db79` |
| `general/writing-for-llm/check_skill.py` | `65f47f5652f5541a04964ea6240bc978ae318823` |
| `docs/changes/workflow-stack-review/ACCEPTANCE.md` | `1d692fc4d9bf46421b02e35b41d8be3f4ef9e398` |

标准文件 blob 还与标准提交相等. 命令为 `git rev-parse <提交>:<路径>` 和不带 `-w` 的 `git hash-object <路径>`, 不写对象或修改标准.

## AC-05-01 至 AC-05-07 逐条结果

### AC-05-01: 文本要求满足, 首轮问题已消除

本轮重新读取 `workflow/verify-change/SKILL.md:59-62` 和 `workflow/verification-contract/SAFETY.md:11-22`, 不引用返修者解释代替观察.
`SKILL.md:59` 的公共授权改用相对链接与明确的 `写入与授权` 节名, 文件真实抵达 `workflow/verification-contract/SAFETY.md`; 本轮 `realpath -e` 成功, 标题检索仍为 `17:## 写入与授权`.
首轮残留的 `默认只读.` 已删除, 默认只读要求仍在公共文档 `:19`. 在 verify-change 全文检索 `默认只读|旧批准|批准绑定|同范围`, 实际无命中, rg 退出码 1, 不是报错或跳过.

- 获批前相关项记未检查仍在 `SKILL.md:59`.
- 派工单原样写入批准范围, 要求验收者逐次记录, 超范围验收者停下且组织者不替其扩权, 三条仍完整在 `:60`.
- `SAFETY.md:19-22` 承接批准前说明资源/对象/操作/保留与访问方式, 批准绑定范围, 同范围复跑, 换范围重新授权及工具不自动授予权限. 未再内联旧批准不作新范围依据.
- `SKILL.md:61-62` 的数据留存/复跑, 必要停止/清理记录及验收完成标准未改. 经未变的 verification-contract/SKILL.md:22, 仍能抵达 SAFETY 的原始数据节 `:11-15`.

指定的验收特有语义得以保留, 首轮指出的额外共用短句重复不再存在. 不把此静态结论推成实际操作一定遵从.

### AC-05-02: 文本要求满足, 引用适用的首轮观察

引用首轮报告 `REVIEW.md:91` 的本轮前观察, 原检查时间见该报告, 绑定原目标 `14c624f0b7f5b6eda9df722bff6fb4826ee1bc5f`. 对应文件和公共文档的旧新差异已证实为零.
`blast-radius/SKILL.md:65,74` 的授权指向写入与授权节, `:79` 清理同时抵达写入与授权/原始数据两节. 原有授权范围, 原始数据保留, 脚本全文/输出与清理结果交接均未漏. 首轮对短提示仍有词义重叠但未展开另一套规则的范围判断保持不变, 本轮不另立去重标准.

### AC-05-03: 文本要求满足, 引用适用的首轮观察

引用 `REVIEW.md:98`, 同一原目标的旧观察. `maintain-verification-skill/SKILL.md:67` 与其上下文完全未变, 正面限定为配方当前可执行与本次复跑结果, 不点名 verify-change, 不扩大为产品验收或全项目通过.

### AC-05-04: 文本要求满足, 引用适用的首轮观察

引用 `REVIEW.md:102`, 同一原目标的旧观察. `blast-radius/SKILL.md:9` 按调用方分工描述组织产品验收者, 使用者亲自调查/运行及可委派多模型调查的旧分工未变. `reference/PROVENANCE.md:48-49` 两行仍与正文相符. 历史 D025 及相关决策文件与旧目标相同, 未改历史决策原文.

### AC-05-05: 文本要求满足, 引用适用的首轮观察

引用 `REVIEW.md:108`, 同一原目标的旧观察. README 及位置完全未变: `:9` 为目录标题, `:11` 为调用关系说明, `:15` 才开始第一张 skill 表. 口径仍是只画执行调用, 引用/分工声明/重新派活不算调用边.

### AC-05-06: 证据要求满足

首轮 `REVIEW.md:48-79` 的五处修正, README 与来源说明差异定位仍适用, 本轮另补唯一返修的实际差异. 三个修改过的 SKILL.md 已在新目标内容一致的当前仓库重新检查, 各实际退出码 0, 原始记录见下文. 本会话仍独立于实施和返修, 报告绑定新目标与同一标准, 不覆盖首轮失败观察.

### AC-05-07: 已返回操作符合, 留一处日志缺口

从指定原生会话日志逐条抽取实际工具调用并按 toolCallId 对接结果, 没有用作者分析/自评或自检文档替代工具记录. 可见且有返回的操作未见实际运行同步, 或直接修改已安装 skills/agent 全局配置. 原实施期的操作记录缺口已大幅补齐, 但返修会话有一条生成错误且缺结果的记录, 不能判定其是否派发/执行, 详见下一节.
本会话可见命令仍未执行同步或修改已安装 skills/全局配置; mailbox 身份与监听属于明确授权的会话级通信操作. 未查看当前 ROADMAP.json 数据, 未暂存或提交其状态变化. 本轮只新增本报告, 不新增测试脚本或启动产品/测试服务及 LLM 行为实验.
本项不报全面通过. 观察边界为指定会话, 指定时间范围和可见命令/工具结果, 不扩展为整个账户, 其他进程, 隐藏副作用或系统全部历史的证明. 安装效果与 LLM 实际遵从率仍未验证.

## AC-05-07 原始工具记录补查

### 来源, 筛选范围与结果配对

- 原实施原件: `/home/bolo/.pi/agent/sessions/--home-bolo-Workspace-refactor-skill-around-verification--/2026-10-30T07-34-18-075Z_01a18bbb-1cda-7447-b17f-fbd626f41e60.jsonl`.
- 返修原件: `/home/bolo/.pi/agent/sessions/--home-bolo--/2026-10-30T07-30-44-526Z_01a18bb7-daad-71ad-b7ab-ba6b1373fc72.jsonl`.
- 原实施筛选到 `2026-10-30T10:24:59.999Z`, 包含 10:24:59 这一整秒; 实际调用/结果分布在 `:6-98`, 最后结果时间 `10:24:59.846Z`.
- 返修筛选 `2026-10-30T10:38:55Z` 至本次请求发出所在整秒末 `10:47:43.999Z`, 实际相关记录在 `:100-113`.
- 只取 message 中 `type=toolCall` 的实际参数, 再以 id 匹配 `role=toolResult` 的 toolCallId. 对 codemode 检查实际传入代码及结果, 区分字符串中的文字与执行入口. 不以 grep 在全会话中命中命令名就算执行.
- write/edit 的报告正文不取作证据, 只取写入目标和成功/失败结果. 不采用作者推理, 派工正文, 自我评价或未确认的其他讨论作为判据. 历史只读路线图查询的业务结果不作为本轮标准.

2026-10-30T10:57:10Z 只读内联提取后的配对结果整理如下, 不是逐字输出; 原始 JSON 输出保留在本会话工具记录中. 没有新增脚本文件:

```text
原实施: read=2, bash=36, mailbox_listen=2, edit=5, write=1.
顶层 toolCall=46, 匹配结果=46, 无匹配结果=0.
返修: codemode=3, edit=1, bash=2, write=1.
表面 toolCall=7, 匹配结果=6, 无匹配结果=1.
```

这里的结果配对数不等于命令全部成功. 原实施 `:43/44` 的旧只读查询有错误标记; 未将它伪装成成功或与同步操作混为一谈. 三次新目标校验的实际退出码另有独立记录.

### 实际写入/执行及结果出处

| 会话及调用/结果行 | 直接观察 |
| --- | --- |
| 原实施 `:78/79-81`, `:82/83-84` | 五个 edit 目标恰为三个被核 SKILL.md, PROVENANCE.md 和 README.md; 结果分别确认替换 1/4/1/2/1 块, 无安装目录或全局配置路径 |
| 原实施 `:87/88` | 实际运行仓库 check_skill.py 三次, 输出三个绝对目标路径各 `OK`, `exit=0`, 时间 `10:23:46Z`; 这是旧观察, 不代替本轮重跑 |
| 原实施 `:91/92` | git add 明列五文件, commit 结果为 `14c624f`, 五文件变更; 没有同步命令 |
| 原实施 `:93/94`, `:95/96` | 仅写入并提交 IMPLEMENTATION.md; 只核写入目标和工具结果, 未采用自检正文 |
| 原实施 `:13/14` 及其他 mailbox 调用 | ensure-session 返回本会话独立配置路径, 其余为 presence/send 与监听状态. 属会话级通信准备, 不等同修改 agent 全局配置 |
| 返修 `:100/101` | codemode 内实际为读取首轮报告和 bash 的 git 状态/提交元数据/presence; 第二项结果 exit_code=0, 无同步或安装目录写入 |
| 返修 `:102/103` | edit 仅指仓库 verify-change/SKILL.md, 实际结果为成功替换 1 块 |
| 返修 `:104/105` | 仓库静态检查各 `OK`, `exit=0`; 明列单文件 git add, commit 返回 `6d0c4b25b4b8e84bd45c43549d442dd8cfb29395`, 一文件一增一删; 随后 find 只定位原实施日志 |
| 返修 `:106/107`, `:108/109` | 只写入并提交 REPAIR.md, 后做 mailbox presence, 无同步或安装目录写入 |
| 返修 `:112/113` | codemode 实际调用 mailbox presence/send, 两项结果 exit_code=0, 信件 id 为 `f05649ffc027449699dcea530b1cd14c` |

原实施其余 bash 参数逐条核对为材料读取/检索, Git 只读差异或历史, 静态校验与 mailbox 通信. 未发现 `sync-to-pi.py` 的执行入口, 也无面向安装目录/agent 全局配置的 edit/write 或 shell 写入命令.
原实施 `:49,55,97` 的发信正文提到同步命令, 以及读取 AGENTS.md/说明文档后在结果里出现该名字, 都不是运行该命令. 返修 codemode 的 body 字符串同理. 这些文字不转抄为实际执行记录或作者证明.

### 剩余日志缺口, 未作豁免

返修原件 `:110` 的原始元数据:

```text
record_id=3052970e
timestamp=2026-10-30T10:46:40.208Z
role=assistant
stopReason=error
errorMessage=stream error: stream disconnected before completion: stream closed before response.completed
```

其中有一个未完成的 codemode toolCall:

```text
call_QxPYS2ZJl0xxN0N7OtufMrMj|fc_09f248a61447fd21016ae47448f74887d092f02705c195e66c
```

可见代码在构造 mailbox 回信命令途中截断. 截至 2026-10-30T10:57:10Z 的原件中未找到该 id 的 toolResult. 不把缺结果推成工具已经执行成功, 也不反推一定未派发. 已向协调方请求实际派发/执行或未派发的原生记录, 请求信件 id `a865a931f8e2454da064cadb95abb348`.
这是剩余记录缺口, 不是已证实的同步/修改安装目录行为. 若要把本次返修全部执行状态也核对完整, 还缺该条的原生执行状态材料. 本报告不自行豁免, 不拿生成错误文字代替工具结果.

## 本轮三次静态检查原件

运行前的工作区一致性和 blob 见前文. 环境为 Linux `7.0.0-31-generic x86_64`, uv `0.13.1`, Python `3.11.2`, 所查 HEAD 为 `572da571c68925bd3c6e8dedc5a1f82c3984057b`. 校验器为新目标中的仓库 `general/writing-for-llm/check_skill.py`, 不是已安装副本.
2026-10-30T10:54:32Z 实际执行以下命令, 每次前后打印 UTC 时间, 命令后立即 `rc=$?` 并输出 `exit_code`:

```bash
PYTHONDONTWRITEBYTECODE=1 uv run python /home/bolo/Workspace/refactor-skill-around-verification/general/writing-for-llm/check_skill.py /home/bolo/Workspace/refactor-skill-around-verification/workflow/verify-change/SKILL.md
PYTHONDONTWRITEBYTECODE=1 uv run python /home/bolo/Workspace/refactor-skill-around-verification/general/writing-for-llm/check_skill.py /home/bolo/Workspace/refactor-skill-around-verification/workflow/blast-radius/SKILL.md
PYTHONDONTWRITEBYTECODE=1 uv run python /home/bolo/Workspace/refactor-skill-around-verification/general/writing-for-llm/check_skill.py /home/bolo/Workspace/refactor-skill-around-verification/workflow/maintain-verification-skill/SKILL.md
```

原始检查输出及紧邻记录:

```text
START verify-change 2026-10-30T10:54:32Z
/home/bolo/Workspace/refactor-skill-around-verification/workflow/verify-change/SKILL.md: OK
exit_code=0
END verify-change 2026-10-30T10:54:32Z

START blast-radius 2026-10-30T10:54:32Z
/home/bolo/Workspace/refactor-skill-around-verification/workflow/blast-radius/SKILL.md: OK
exit_code=0
END blast-radius 2026-10-30T10:54:32Z

START maintain-verification-skill 2026-10-30T10:54:32Z
/home/bolo/Workspace/refactor-skill-around-verification/workflow/maintain-verification-skill/SKILL.md: OK
exit_code=0
END maintain-verification-skill 2026-10-30T10:54:32Z
```

这些是本轮实际运行结果, 与原实施/返修者的旧结果分开. 校验器只证明规定的 frontmatter/name/调用方式等静态格式, 不替代指针/语义核对或 LLM 行为验证.

## 证据类型与结论边界

- 实际观察: 本轮文件/提交差异, blob 一致性, 指针实际落点, 三次校验原始输出/退出码/UTC 时间, 指定会话实际工具参数与相配结果, 一条缺结果的生成错误记录.
- 引用的旧观察: 首轮报告中 AC-05-02 至 AC-05-05 及原五处差异定位, 已按相同输入核对适用性. 原实施和返修的运行记录各保留原时间/来源, 不冒充本轮执行.
- 文本判断: 公共指针承接授权/数据规则, 规定的验收特有语义与执行分工保留, 配方复跑边界未扩大. 这不是 LLM 实际遵从的运行证明.
- 未验证: 上述无结果记录的实际派发/执行状态, 其他进程或时间范围外的操作, 安装效果, LLM 遵从率, 产品行为, 其他里程碑和正式终点验收.

没有产品实验原始数据需要另存. 本轮命令输出保存在本报告和本会话原生工具记录中, 未清理原件. 首轮失败报告原样保留; 本报告只覆盖新目标和原标准, 不关闭 milestone-08 或宣称正式验收通过.
