# llm-select 数据目录进容器: 只读挂载方案

状态: 已执行 (2026-10-07, 方案 A 落地; 决策见 [DECISIONS.md](DECISIONS.md) D059 与 [ADR-0018](../../adr/0018-host-config-dir-runtime-ro-mount.md)). 下文保留方案原貌, 第 6 节补拍板结果.

## 1. 问题

背景: `llm-select` skill 给子代理挑模型与 thinking 档. 它的输入是每台设备各一份的两份文件:

- `~/.agents/llm-select/llm-scores.json` (评分表: 候选模型各维能力相对基准的比率分)
- `~/.agents/llm-select/model-catalog.json` (模型目录: 成本, 是否推理模型, thinking 支持档)

算法在 skill 目录下的 `score.py`, 输出选型表.

现象: 容器里这两份文件不存在, 于是该 skill 在容器内 100% 跑不起来. 容器内实测:

```text
$ ls ~/.agents/llm-select/
ls: cannot access '/home/bolo/.agents/llm-select/': No such file or directory

$ cd ~/.agents/skills/llm-select && uv run python score.py
no-catalog: /home/bolo/.agents/llm-select/model-catalog.json      (退出码 1)
```

会话里的两次调用报错完全相同 (2026-10-06 14:44:02 会话 `01a111aa`; 2026-10-07 01:57:25 会话 `01a111eb`, 相隔 11 小时), 所以不是偶发. 用仓库里的模板凑也不行:

```text
$ uv run python score.py --scores scores-template.json --catalog model-catalog-template.json
bad-baseline: (baseline 为空)
```

后果: 选型退化成凭印象, 而"不凭印象选型"正是这个 skill 存在的理由.

- 会话 `01a111eb`: agent 只在思考里记了一句"catalog 缺, 用不了", 没告诉用户, 直接拍定三个子会话的模型 (instigator=gpt-5.6-sol, verifier=gpt-5.6-luna, verifier2=gpt-5.6-terra), thinking 一律 `high`.
- 会话 `01a111aa`: agent 起两个研究子会话时没指定模型 (用 pi 默认), 用户随后手动改成 `gpt-5.6-luna`.
- 用户在会话头手工切模型 (会话 `01a111aa` 切 20 次, 会话 `01a111eb` 切 15 次).

根因: 容器创建路径只把宿主 `~/.agents/skills` 运行期只读挂进容器 (`workflow/use-sandbox-worktree/scripts/swt.py:2555-2556`), 而 `~/.agents/llm-select` 是 `skills` 的兄弟目录, 没人管. 镜像构建那层同样没有它: `image-prep.py:328-344` 的 `stage_context` 只 copytree `skills/` 与 `pi-agent/`, Containerfile 里只有 `COPY skills/` 与 `COPY pi-agent/` (`image-prep.py:290-291`). 所以容器里既没有烤入副本, 也没有挂载.

## 2. 目标

- 容器内 `cd ~/.agents/skills/llm-select && uv run python score.py` 直接出选型表.
- 表内容与宿主 (真设备) 那份逐字一致.
- 容器不能改这两份文件.
- 宿主改分后, 新建的容器立即看到新值, 不需要重建镜像.

## 3. 方案 A (推荐): 运行期只读挂载宿主目录

### 3.1 改动点

只改一个文件: `workflow/use-sandbox-worktree/scripts/swt.py`.

1. 常量区, 在 87-88 行现有两个常量旁边加一对:

```python
SKILLS_HOST_DIR = Path.home() / ".agents" / "skills"
SKILLS_CONTAINER_DIR = "/home/bolo/.agents/skills"
LLM_SELECT_HOST_DIR = Path.home() / ".agents" / "llm-select"
LLM_SELECT_CONTAINER_DIR = "/home/bolo/.agents/llm-select"
```

2. birth 组装 `podman create` 的段里, 紧跟 skill 库挂载 (2555-2556 行) 之后加一处:

```python
if assert_llm_select_mountable(LLM_SELECT_HOST_DIR):
    command.extend(["-v", f"{LLM_SELECT_HOST_DIR}:{LLM_SELECT_CONTAINER_DIR}:ro"])
```

### 3.2 存在性守卫

仿 `swt.py:2463-2488` 的 `assert_skills_mountable`, 但语义不同: skills 缺失容器就没法工作, 硬拦; llm-select 缺失只是退回现在的 `no-catalog` 状态, 所以软跳过. 守卫做两件事:

- 目录不存在: 向 stderr 打一行提示 (例如 "host 无 llm-select 数据目录, 容器内该 skill 不可用"), 返回 False, 不挂载.
- 目录存在但有非全局可读路径: rootless uid 映射下容器 `bolo` 只能靠 other 权限位读宿主树, 按同规则点名 (目录需 `o+rx`, 文件需 `o+r`). 这一支是硬拦还是软跳过, 见第 6 节.

### 3.3 为什么不整体挂 `~/.agents`

宿主 `~/.agents` 下还有 sandbox-worktree 的运行记录 (决策收据, 审计, 镜像构建记录) 与 mailbox 相关物. 现有规矩是这些留在宿主不进容器 (D023 明确 sessions 不进容器). 只挂 `llm-select` 一个目录, 暴露面最小.

### 3.4 为什么挂载优于镜像 COPY

- `bootstrap.md` 说改分是事件驱动的 (模型升级, 价格调整, 观测与分数不符). 挂载: 宿主改完, 新 birth 即生效. COPY: 每次改分都要重建 base 镜像, 会顺着 D017 的谓词链淘汰 display 层与全部项目层.
- 与已确立的口径一致: skill 库本身就是运行期只读挂载, 遮蔽镜像烤入的副本 (2555-2556 行注释"实时跟随 host"); auth.json 走挂载或启动注入 (D044/D046). llm-select 数据属同一类"需要跟随宿主"的配置.
- 只读挂载防写回宿主, 同时保证容器里的表与宿主不分叉.

### 3.5 生效语义

`-v` 在 `podman create` 时确定: 改动只对新 birth 的容器生效, 运行中的容器不动. 与现有全部挂载点同一语义.

### 3.6 决策记录位置

改的是 use-sandbox-worktree, 决策应记进 `docs/changes/use-sandbox-worktree/DECISIONS.md`, 并补一条 ADR 或在既有 ADR 里引用. 现在与宿主路径暴露有关的既有决策是 D017 (镜像层淘汰谓词), D018/D023 (容器 home 复刻 host 布局, skill 库 COPY, auth.json 只读挂载), D044/D046 (auth.json 挂载与注入), D051 (wayland 直通).

## 4. 方案 B (备选): 镜像构建时 COPY

在 `image-prep.py:328-344` 的 `stage_context` 里把 `~/.agents/llm-select` 也 copytree 进构建上下文, Containerfile 加一行 `COPY`. 代价: 每次改分都要重建镜像, 容器里的表随镜像过期. 只在"不希望容器读到宿主实时数据"时才选.

## 5. 边界与风险

1. 宿主源目录必须先存在. 容器看不到宿主, 本文无法验证这一点; 落地前需在宿主执行 `ls ~/.agents/llm-select/`. 若宿主也没有, 先按 `bootstrap.md` 在宿主建表 (定基准 -> 派子代理联网调研打分 -> 落盘), 再挂.
2. rootless podman 对不存在的挂载源行为不友好 (可能创建 root 属主的空目录). 3.2 的守卫就是为了不落到这个情形.
3. 只读足够: `score.py` 只读, 不写这两份文件.
4. 容器 pi 的模型清单来自镜像快照 (`~/.pi/agent` 由镜像构建时复制), 可能与宿主漂移. 本方案不解决它: `SKILL.md` 已规定 `--scope` 取该平台自己的 `settings.json` 的 `enabledModels`, 容器内自洽. 是否让模型清单也跟随宿主, 是独立议题 (会牵动 auth.json 与凭据暴露面).

## 6. 待拍板 (已拍板)

1. 守卫在"目录存在但权限不对"时: **软跳过** (与缺失支同). 理由: llm-select 是可选增强, 硬拦会让它的配置问题拖垮整个 birth; 先例为 D044 的 host 文件缺席软跳过. 该支同样打 stderr 点名提示 (见 D059 守卫语义).
2. 是否同时改 `general/llm-select/SKILL.md` 补"拿不到评分表时怎么办": **本次不做**, 保持独立待办. 现状挂载落地后, 只有宿主也没建表时才触发该退路; 仍为独立缺陷, 可与挂载分开做.
3. 容器 pi 的模型清单要不要也跟随宿主: **本次不做** (见风险 4, 独立议题).

## 7. 验收

落地后新建一个容器, 在容器内执行:

```text
ls -la ~/.agents/llm-select/
cd ~/.agents/skills/llm-select && uv run python score.py
```

期望: 第一条列出宿主那两份文件; 第二条打印选型表 (各模型七维分, 七个画像总分, thinking 支持档与文字摘要). 与宿主上同一条命令的输出逐字比对一致.

失败态 (宿主目录缺失或权限不对): 不挂载, 容器内仍是 `no-catalog`, 且 birth 过程有明确提示, 不出现 root 属主空目录.

执行状态 (2026-10-07): 代码与快层用例已落 (swt.py + tests/test_swt_llm_select_mount.py), 本容器无 podman, 端到端验收 (上面两条命令) 未做, 需在宿主新建容器后执行.

## 8. 证据索引

- 容器内实测 (本文写作会话): 第 1 节的命令与输出, 以及 `ls ~/.agents/skills/llm-select/` 能列出 SKILL.md, bootstrap.md, score.py 与两个 template.
- 会话证据: `~/.pi/agent/sessions/--home-bolo-Workspace-review-old-sessions--/2026-10-06T14-42-07-477Z_01a111aa-*.jsonl` 的 14:44:02; 同目录 `2026-10-06T15-53-20-515Z_01a111eb-*.jsonl` 的 01:57:25.
- 代码: `workflow/use-sandbox-worktree/scripts/swt.py:87-88`, `:2463-2488`, `:2512-2560`; `workflow/use-sandbox-worktree/scripts/image-prep.py:290-291`, `:328-344`, `:836`.
- 决策: `docs/changes/use-sandbox-worktree/DECISIONS.md` 的 D017, D018, D023, D044, D046, D051.
- 同源问题记录: `docs/changes/review-session-skill/milestone-05/findings.md` (m05 实跑验收的问题清单; llm-select 一条未追加进去, 以本文为准).
