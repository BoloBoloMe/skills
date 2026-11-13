# 非作者复核更正版原始输出

入库注: 仅把非 ASCII 标点与箭头改为 ASCII, 其余正文未改. 原件为 `/tmp/remove-verification-tools-review.md`; 初稿在 `/tmp/remove-verification-tools-review-01.md`. 复核覆盖源码删除与 README, 后增 ADR/归档材料的核对见 [VERIFICATION.md](VERIFICATION.md).

# remove-verification-tools 非作者复核报告 (v2, 更正版)

复核者: 会话 01a1a5ea-dc00-744d-bb9f-0339cbd5bb74 (独立信箱与守护自检通过; 接手信投递成功, 完成信被服务判对端离线, 未强投, 本轮改走 Herdr 交互)
仓库: /home/bolo/Workspace/refactor-skill-around-verification (只读, 未提交/未同步/未改配置, 未开子会话)
基线: 829a1ad (HEAD 即该提交)

## 更正记录 (相对 v1)

1. 计数改正: 差异是 1 个文件修改 + 5 个文件删除 = 6 项 (v1 摘要误写 "6 个文件被删", 正文误写 "7 项").
2. 边口径改正: 删除前的执行调用边是 3 条: create->verification-contract, create->use-herdr, maintain->verification-contract. v1 漏掉 create->use-herdr, 且误把 maintain "按 create 某节执行" 计成边; 现按正文语义判为普通引用.
3. 推断收回: 撤回 "新项目上配方分支永远为空" 这一越界推断. 已证实的只是仓库内不再有生成/维护配方的 skill; 用户手工写配方, 项目自带配方等情形无法排除, verify-change 对既有配方的可选支持仍然有效且不应删除.
4. 实测口径改正: pytest 那条确为实际执行, 现附命令与原始输出片段 (退出码 3, 停在 conftest 的 podman 调用). 另补一条: 同一个用例用 unittest 直跑通过.

## 结论摘要

- 删除范围与 README 入口一致: 5 个文件删除 (两项 skill 各自 SKILL.md + agents/openai.yaml, 加 maintain 的 reference/drift-classification.md), 1 处 README 两行删除, 无夹带.
- 现行源码零残留: 两个旧名在仓库管理的非 docs 文件里没有任何入口, 引用或执行调用语句. README 技能表 38 行与 38 个 SKILL.md 目录一一对应, 链接全可达.
- 调用关系变化: 删除前这两项是入边 0 的两个节点, 出边共 3 条 (其中 2 条指向 verification-contract, 1 条指向 use-herdr). 删除后 3 条出边随之消失, 没有悬空边, 两目标各自都还有其他调用方.
- 同步计划不再发现这两项 (按源目录枚举), 但普通同步不做反向清理, 真实安装目录两份旧副本仍在.
- 未损伤其余 38 个 skill: 文件零改动, 技能元数据守卫用例通过.
- 未发现阻断性问题. 待你拍板的三条见第八节.

## 一. 实际核对范围

- `git diff 829a1ad --stat` / `--name-status` (含暂存与未暂存), `git diff --cached`, `git diff`, `git status`, `git log -1`, `git diff 829a1ad --check`.
- README 全文与 `## 目录` 调用关系口径; 技能表逐行与磁盘目录双向对账 (38/38).
- 829a1ad 与当前工作区 `git grep` (含 `--untracked`, 排除 docs) 查两个旧名与 drift-classification.
- 基线里两个被删 SKILL.md 的逐行重读, 只按语句语义判执行调用与普通引用.
- 38 个现存 SKILL.md 及其 reference/*.md 的执行调用语句抽取与目标对账.
- sync-to-pi.py 的枚举/清空/空壳剔除/扩展登记对账代码路径 (只读, 未运行同步).
- 单文件 pytest 一次 (附原始输出), 同一用例 unittest 直跑一次.
- `~/.agents/skills/` 两项旧副本的存在性, 类型, 与 829a1ad 的 sha256 比对, 是否有多余文件.
- docs/adr, docs/language, docs/proposals, docs/changes 里旧名与 "配方" 的命中位置.

## 二. 差异核对 (已证实, 计数已改正)

实际命令与输出:

```text
$ git diff 829a1ad --stat | tail -1
 6 files changed, 179 deletions(-)
$ git diff 829a1ad --name-status
M	README.md
D	workflow/create-verification-skill/SKILL.md
D	workflow/create-verification-skill/agents/openai.yaml
D	workflow/maintain-verification-skill/SKILL.md
D	workflow/maintain-verification-skill/agents/openai.yaml
D	workflow/maintain-verification-skill/reference/drift-classification.md
M=1 D=5 total=6
$ git diff --cached --name-status | wc -l
5
$ git diff --name-status
M	README.md
```

- 合计 6 项: 1 个修改 (README) + 5 个删除; 暂存区只有 5 个删除, README 是未暂存修改. 全部是删除行, 新增 0 行.
- 829a1ad 树里这两个目录的全部跟踪文件正好是上列 5 个, 没有漏删的脚本或参考文件; 工作区里两目录整体消失, 不留空壳, 无 `__pycache__` 残留.
- README 只删两整行: create-verification-skill 行 (原在 code-review 与 decision-ledger 之间) 和 maintain-verification-skill 行 (原在 lazy-dev 与 navigate 之间); 其余行未动, 字母序仍连续.
- `git diff 829a1ad --check` 退出码 0, 无空白错误.

## 三. 现行入口/引用/执行调用核对 (已证实, 零残留)

- `git grep --untracked -Ei 'create-verification|maintain-verification|drift-classification' -- . ':!docs'` 零命中 (rc=1).
- 829a1ad 对照: 删除前非 docs 范围的命中只有 (a) README 两行, (b) 这两个 skill 自己的文件, (c) 二者之间的一处称呼 ("`maintain-verification-skill` 也指向这里" 与 maintain 里两处 "按 create-verification-skill skill 的某节"). 没有第三个 skill 引用它们.
- 两目录都没有 pi-extension, 同步的扩展登记对账 (`_scan_extension_dirs` 只扫 `*/pi-extension`) 不涉及它们, settings.json 与 extensions.synced.json 无需收尾.
- 仓库根 agent-prompts 母本没有技能清单; docs/language/UBIQUITOUS_LANGUAGE.md 无旧名命中.

## 四. 调用关系变化 (按 README 口径逐条判断, 已改正)

口径: 只算执行调用; 引用, 分工声明, 重新派活不算边.

删除前, 两个被删 skill 的出边 (按语句原文判断):

| 位置 | 原文要点 | 判定 |
| --- | --- | --- |
| create:9 | "开始前调用 `verification-contract` skill, 只遵守共用底线" | 执行调用, 边 create->verification-contract |
| create:61 | "派一名未参与编写的会话实跑: 调用 `use-herdr` skill 开新子会话" | 执行调用, 边 create->use-herdr |
| create:61 | "在目标项目用 `/skill:verify-<应用名>` 加载当前配方" | 执行调用, 但目标在目标项目, 不属本仓库 skill |
| maintain:10 | "开始前调用 `verification-contract` skill, 只遵守共用底线" | 执行调用, 边 maintain->verification-contract |
| maintain:44 | "改配方前按 `create-verification-skill` skill 的 写入授权 节获批, 该节的完成标准同样适用" | 规则指针, 普通引用, 不算边 |
| maintain:60 | "派工与加载来源核对按 `create-verification-skill` skill 的新会话复跑 节执行" | 规则指针, 普通引用, 不算边 |
| create:61 | "`maintain-verification-skill` 也指向这里" | 普通引用, 不算边 |
| maintain:62 | "要求它调用 `verification-contract` skill 遵守共用底线" | 对复跑会话的派活 (重新派活), 不构成 maintain 自己的边 |
| create:25,33 | "按已调用的共用底线执行", 指针到 verification-contract/SAFETY.md | 文件引用, 不是新增边 (目标已由上表第 1 行覆盖) |

- 仓库内出边合计 3 条; 入边 0 条 (无其他 skill 调用它们).
- 删除后: verification-contract 少 2 个调用方, use-herdr 少 1 个调用方. 二者仍被多处调用 (verification-contract 被 benchmark-checklist, code-review, drive-execution, fix-bugs, to-execution, verify-change 等; use-herdr 被 mailbox, blast-radius, verify-change 等), 因此没有节点变成无人调用, 也没有悬空边.
- 说明一处口径分歧的处理: 若有人把 "按某 skill 的某节执行" 也算边, maintain->create 会多一条; 但两种读法都不影响删除结论, 因为两端都在同一批删除里, 且其余 skill 与它们无连接. 我按 README 口径判为引用.
- 现存 38 个 skill 的语句抽取里, 没有目标指向这两个已删名字; 唯一不在现存集合的 "目标" 是 writing-for-llm 被正则捕到的单字母 `x` (占位写法), 属抽取误报.

## 五. 同步计划能否再发现这两项 (已证实: 不会再发现)

- sync-to-pi.py:199 `sub_items = sorted(src.iterdir())`, :748-749 以 `repo_root / "workflow"` 为源: 计划完全由源目录枚举生成. 现场 workflow/ 下 24 个目录, 已无这两项; 目录不存在就不会产生计划项.
- 不触发空壳保护 (`_drop_empty_sources` 只对 "除忽略项外无文件的目录" 生效), 因为目录是整体消失而非留壳.
- 但 (已证实): execute_plan (sync-to-pi.py:619-635) 只在用户选 "清空 ~/.agents/skills" 时执行 `_clear_skills`, 否则逐项复制, 没有 "安装目录有但源里没有就删" 的反向清理. 一次普通同步不会撤掉已安装的这两份旧副本.

## 六. 真实安装目录现状 (已证实, 属你声明的非目标)

- `~/.agents/skills/create-verification-skill`, `~/.agents/skills/maintain-verification-skill` 仍在, 都是实体目录 (非指向仓库的软链), 删除不会让它们变成断链.
- 5 个文件与 829a1ad 版本 sha256 全等 (如 create/SKILL.md `0ecd51cf...`), 目录内无仓库外的多余文件.
- 含义: 仓库侧删除已完成, 但这两份 skill 在真实 agent 环境里仍可被手动加载或点名. 按你 "不同步安装版" 的决定, 不算本次缺陷, 只是待你处置的残留事实.

## 七. 是否损伤其他 skills (已证实)

- 剩余 38 个 skill 的 SKILL.md/reference 零改动 (差异里没有任何 M).
- `tests/test_skills_codex_metadata.py` 用 unittest 直跑通过, 说明成对删除后其余 skill 的 codex 元数据契约仍自洽.
- 两个被删 skill 的规则没有被别的 skill 依赖: 唯一自称 "唯一真相源" 的那节只被同批删除的 maintain 称呼过.
- 因此本项删除不改变其余 skill 的输入, 前置或判定标准.

## 八. 待核实疑点 (需你判断, 我不替你定)

1. 历史 ADR 与现实脱节: `docs/adr/0021-project-verification-recipes-not-acceptance-authority.md:3,5` 仍把两项描述为生成与维护项目配方的现行角色. 仓库既有惯例 (见 0025) 是旧 ADR 原文不改, 由新 ADR 记录取代关系; 本次没有取代记录. 按 "不删除历史 docs 记录" 的要求现状不动是合规的, 但要不要补一篇取代 ADR 由你定.
2. verify-change 的配方分支失去生产者 (需分清事实与推断):
   - 已证实: 删除后仓库内已无任何 skill 生成或维护项目级验证配方 (旧名零命中, 两目录不存在); `verify-change/SKILL.md:72` 与 `reference/SCENARIO-CHECK.md:9,11` 仍写 "项目有配方时..." / "没配方时..." 的可选分支; `verify-change/SKILL.md:106` 的 "不生成或修改项目级配方" 是对验收者的禁令.
   - 不能由此推断: 具体项目将来一定没有配方. 用户可手工编写配方, 项目可自带配方 (例如目标项目 `.agents/skills/verify-<应用名>/`), 也可来自别处; 这些路径本次都未排除.
   - 因此: 能说的是 "仓库不再提供生产/维护配方的 skill", 不能说 "配方分支永远为空". 删除这两项也不要求删掉 verify-change 对既有配方的可选支持, 那段文本仍有作用. 是否顺带收口措辞, 由你定.
3. 安装目录残留的处置: 清掉它们要么走同步的 "清空" 选项 (会连其他旧 skill 一起清空再重装), 要么手工删这两个目录. 两者都触碰真实 agent 配置, 超出本次授权.

## 九. 测试与实测口径 (已改正)

- 单文件 pytest 命令与原始输出 (确实执行过, 退出码 3):

```text
$ PYTHONDONTWRITEBYTECODE=1 uv run python -m pytest -p no:cacheprovider -q tests/test_skills_codex_metadata.py
exit=3
INTERNALERROR>   File "/home/bolo/Workspace/refactor-skill-around-verification/tests/conftest.py", line 236, in pytest_sessionstart
INTERNALERROR>     result = subprocess.run(["podman", "volume", "ls", "-q"],
INTERNALERROR>   File "/usr/lib/python3.11/subprocess.py", line 1901, in _execute_child
INTERNALERROR>     raise child_exception_type(errno_num, err_msg, err_filename)
INTERNALERROR> FileNotFoundError: [Errno 2] No such file or directory: 'podman'
```

  说明: 失败发生在 pytest 启动钩子 (conftest.py:236) 调用 `podman volume ls -q` 时, 本容器 PATH 里没有 podman, 因此那一轮没有任何用例执行, 我也没有因此得到该用例的通过结论.
- 同一用例改走 unittest 直跑 (不经 conftest), 通过:

```text
$ PYTHONDONTWRITEBYTECODE=1 uv run python -m unittest tests.test_skills_codex_metadata -v
test_all_skill_md_files_have_codex_metadata_contract ... ok
Ran 1 test in 0.004s
OK
```

- 只跑了这一个文件, 未跑整套 pytest, 未跑部署或外部资源检查; 两次运行后 `git status` 与运行前一致 (无新增跟踪改动).

## 十. 复核期间工作区的外部变化 (如实记录, 非我造成)

- 我第一版报告写在 09:39 (UTC), 之后 worktree 出现未跟踪目录 `docs/changes/remove-verification-skill-tools/VERIFICATION.md` (8543 字节, mtime 2026-11-04 09:40 UTC). 不是我创建或修改的, 也不在 `git diff 829a1ad` 里.
- 影响: 我的 6 项计数只覆盖跟踪文件. 若该文件将来被提交, 跟踪差异会变成 7 项 (1 M + 5 D + 1 新增), 计数需按提交时点重算.
- 该文件记录了作者一侧的核对 (38 项技能表一致, 同步计划 24 项不含被删两项) 和一段 "非作者复核仍在进行, 此处未记通过" 的占位. 我只把它当可交叉核对的信息, 不作为我的判据; 我的数字来自自己执行的命令.

## 十一. 未覆盖范围

- 未运行真实部署同步, 未做外部资源测试; 同步结论来自读代码与现场目录枚举.
- 未跑整套测试或产品验收流程; 只跑了技能元数据这一个用例, 加一次被环境挡住的单文件 pytest 尝试.
- 未把 .venv 内依赖自带示例 skills 计入仓库技能 (只按 git 跟踪文件判断).
- 未验证模型实际触发率, 未验证同步安装后模型是否还会加载旧技能.
- 未审 "两项规则是否该迁到别处" 的合理性 (你已明确不要求迁移).
- 未改仓库, 未改真实 agent 配置, 未开子会话; 只写 /tmp 下的复核文件.

## 十二. 我的复核意见

删除范围与 README 入口一致, 现行源码零残留引用, 调用图只少两个入边为 0 的节点及其 3 条出边, 无悬空调用; 同步计划不会再发现这两项; 其余 38 个 skill 未受影响. 未见需要退回重做的缺陷. 第八节三条与第十节的新增未跟踪文件需要你拍板. 最终人工接受仍由你判断, 本报告不代替验收.

## 十三. 投信状态 (如实记录)

- 接手信已投递成功 (信件 id f4f3f095fb9a49bbaac55111ee2b07a4, 态 "已进本机队列").
- 完成信投递失败: 服务把目标 01a1a596-e731-7649-8ece-1288678991f3 判为 "不在线", 脚本拒绝入队; 按规则未加 --force. 按本轮反馈, 改走 Herdr 交互交付, 不强投, 不重试通知.
- 本会话信箱自检: pi session 与 mailbox session 同为 01a1a5ea-dc00-744d-bb9f-0339cbd5bb74, running=true.

证据归档: /tmp/remove-verification-tools-review.md (v2, 即本正文); v1 初稿由你保留在 /tmp/remove-verification-tools-review-01.md
