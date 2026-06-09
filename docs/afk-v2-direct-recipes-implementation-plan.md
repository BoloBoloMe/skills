# AFK v2 direct recipes 落地方案

## 决策

采用 direct `subagent({...})` recipes 作为 AFK v2 唯一权威实现方式. 不再维护 AFK saved chains. 不再保留 `workflow.afk-worker` 方案.

原因:

- AFK v2 的核心是父会话状态机, 不是一次性长 chain.
- 父会话需要在 implement, review, synthesis, fix, validate 之间保留调度权.
- 顶层 `chains/` 不是 pi runtime 默认发现路径, 维护 saved chains 会造成误解.
- direct recipes 可在运行时覆盖 builtin `worker` 的关键默认项: `context`, `reads`, `progress`, `output`, `outputMode`, `model`, `skill`, `acceptance`.
- 删除 `workflow.afk-worker` 可避免新增 agent 安装, 发现路径, prompt 漂移和双源维护问题.

## 落地目标

- `workflow/run-afk-workflow/SKILL.md` 成为 AFK v2 direct recipes 的唯一权威文档.
- AFK writer 默认使用 builtin `worker`, 不使用 `workflow.afk-worker`.
- skill 中发送给子代理的任务提示词统一使用中文.
- `SKILL.md` 符合 write-a-skill 规范: frontmatter 完整, description 明确触发条件, 主文档精简, 深层细节按需拆分引用.
- 不写入用户级 pi 目录. 不把本机用户目录写成运行依赖.

## 文件变更计划

### 1. 删除 AFK saved chains

删除以下文件:

```text
chains/workflow-afk-implement-only.chain.json
chains/workflow-afk-review-only.chain.json
chains/workflow-afk-fix-only.chain.json
chains/workflow-afk-implement-review.chain.json
```

处理原则:

- 不再保留 deprecated AFK chain.
- 不再让 `/run-chain workflow-afk-*` 成为推荐路径.
- 若需要 saved chain, 由目标项目自行放到项目级 `.pi/chains/`, 不由本仓库 AFK v2 文档承担.

### 2. 处理 `workflow.afk-worker`

删除所有推荐或保留 `workflow.afk-worker` 的文案.

替代口径:

```text
AFK v2 默认使用 builtin worker, 并通过 direct one-step chain 的 step 参数覆盖默认行为.
必须设置 context:"fresh", reads:false, progress:false, chainDir:<AFK_RUN_DIR>, outputMode:"file-only".
```

不再提供 `workflow.afk-worker` agent 配置示例.

### 3. 更新 `workflow/run-afk-workflow/SKILL.md`

目标结构:

```text
---
name: run-afk-workflow
description: 为 workflow 父会话选择 direct subagent recipes. 当 orchestrate 已分类, 且需要只读代码库探索, AFK v2 单阶段编码, diff review, 或 accepted finding 修复时使用. 不用于需求对齐, 方案制定, PRD, 议题拆分或执行决策外包.
---

# 运行 AFK 工作流

## 快速开始
## 工作流
## Direct recipes
## 父会话 synthesis
## 失败恢复
## 检查清单
```

write-a-skill 规范要求:

- frontmatter 保留 `name` 和 `description`.
- `description` 用第三人称, 说明能力和触发条件, 少于 1024 字符.
- `SKILL.md` 主体保持短, 优先 checklist 和最小 recipes.
- 如 direct recipes 变长, 拆到同目录 `AFK-V2-RECIPES.md`, `SKILL.md` 只引用一层.
- 不写设备专属路径. 使用 `<AFK_RUN_DIR>`, `<AFK_SESSION_DIR>`, `<repo>` 占位符.

### 子代理提示词语言

所有传给子代理的 `task` 字段改成中文.

要求:

- implement-only task 中文.
- review-only 三个 reviewer task 中文.
- fix-only task 中文.
- 子代理输出 schema 字段名可保留英文, 便于机器处理.
- 命令, JSON key, path placeholder 保持英文.

### implement-only recipe

使用 one-step `chain`, 不使用 single `agent`.

原因:

- step 级 `reads:false` 可禁用 builtin `worker` 的 `defaultReads`.
- step 级 `progress:false` 可禁用 builtin `worker` 的 `defaultProgress`.
- 相对 `output` 可配合 `chainDir` 落入 `<AFK_RUN_DIR>`.

最小 recipe:

```json
{
  "chain": [
    {
      "agent": "worker",
      "phase": "Implementation",
      "label": "实现已批准 milestone",
      "as": "implementation",
      "reads": false,
      "progress": false,
      "output": "worker-result.md",
      "outputMode": "file-only",
      "skill": "tdd",
      "task": "AFK_RUN_DIR=<AFK_RUN_DIR>. 读取 manifest.yaml, doc-pointers.md, allowed-files.txt, 目标 issue 全文, PLAN 对应章节和 PRD 必要章节. 只实现本次已批准 milestone. 你是当前工作树唯一写入者. 不使用仓库根 progress.md. 如缺少文档指针, 文档冲突, 需要修改非 allowed files, 或出现未批准的产品/API/架构/范围决策, 停止并报告.",
      "acceptance": {
        "criteria": [
          "Only approved milestone scope is implemented",
          "Allowed file boundaries are respected",
          "Focused validation is run or a blocker is reported",
          "No staged files remain",
          "Changed files and residual risks are reported"
        ],
        "evidence": [
          "changed-files",
          "commands-run",
          "validation-output",
          "residual-risks",
          "no-staged-files"
        ],
        "maxFinalizationTurns": 1
      }
    }
  ],
  "cwd": "<repo>",
  "context": "fresh",
  "chainDir": "<AFK_RUN_DIR>",
  "sessionDir": "<AFK_SESSION_DIR>",
  "clarify": false,
  "timeoutMs": 900000
}
```

### review-only recipe

优先使用 `chain:[{parallel:[...]}]`, 让相对 output 统一落到 `chainDir`.

最小要求:

- 三个 reviewer 并行: 正确性和回归风险, 测试和验证质量, 简洁性和范围控制.
- 每个 reviewer `reads:false`, `progress:false`.
- 每个 reviewer 禁止修改项目源码, 配置, 文档, 依赖文件和测试文件.
- 每个 reviewer 只返回有证据 findings.
- 输出写 `review-correctness.md`, `review-tests.md`, `review-simplicity.md`.

### fix-only recipe

使用 one-step `chain`.

最小要求:

- 只读取 `review-synthesis.md` 中的 `accepted_now`.
- 不处理 `deferred`, `needs_human_decision`, `rejected_as_not_evidenced`.
- 每个修复必须引用 `finding_id`.
- `reads:false`, `progress:false`, `output:"fix-result.md"`, `outputMode:"file-only"`.

## README 更新计划

将章节从 saved chains 口径改成 direct recipes 口径.

建议:

- 标题改为 `Pi 子代理 direct recipes`.
- 说明 AFK v2 不依赖顶层 `chains/` 自动发现.
- 说明 AFK v2 的权威入口是 `workflow/run-afk-workflow/SKILL.md`.
- 删除 AFK saved chain 文件列表.
- 删除 `workflow.afk-worker` 推荐.
- 保留 `workflow-context-scout.chain.json` 时, 明确它只是可选 saved chain 示例. 若不保留, 删除对应条目.

## 父会话运行流程

```text
INIT
-> PARENT_PREFLIGHT
-> DOC_POINTERS_READY
-> WORKER_RUNNING
-> PARENT_DIFF_CHECK
-> REVIEW_RUNNING
-> PARENT_SYNTHESIS
-> FIX_RUNNING | FINAL_VALIDATE
-> FINAL_VALIDATE
-> DONE | NEEDS_HUMAN
```

父会话职责:

- 写 `manifest.yaml`, `baseline.txt`, `allowed-files.txt`, `doc-pointers.md`.
- 运行 implement-only recipe.
- 检查真实 diff, 写 `diff-summary.md`.
- 运行 review-only recipe.
- 合并 reviewer 输出, 写 `review-synthesis.md`.
- 必要时运行 fix-only recipe.
- 最终验证, 写 `final-report.md`.

## 验证命令

```bash
git status --short --branch
rg -n "workflow.afk-worker|workflow-afk-implement-only|workflow-afk-review-only|workflow-afk-fix-only|workflow-afk-implement-review|chainName" README.md workflow/run-afk-workflow chains docs
rg -n "[，。；：！？、（）【】]" README.md workflow/run-afk-workflow docs
find chains -maxdepth 1 -type f -name "workflow-afk-*.chain.json" -print
git diff --check -- README.md workflow/run-afk-workflow chains docs
```

预期:

- 不再出现 `workflow.afk-worker` 推荐文案.
- 不再出现 AFK saved chain 作为推荐入口.
- `find chains ... workflow-afk-*.chain.json` 输出为空.
- `SKILL.md` frontmatter 合法, description 有触发条件.
- 子代理 task 文案为中文.
- 无中文全角标点.

## 风险

- Markdown 内 recipe 不能像 JSON 文件一样天然被发现或校验.
- 父代理复制 recipe 时可能漏字段.
- `SKILL.md` 过长会违背渐进式披露.

缓解:

- recipes 保持短, 只放必要字段.
- 在 `SKILL.md` 增加必填字段 checklist.
- 如超过 100 行, 拆 `AFK-V2-RECIPES.md`, `SKILL.md` 只保留入口和链接.
- 保留验证命令, 每次修改后运行.

## 推荐实施顺序

1. 删除 4 个 AFK chain JSON.
2. 重写 `workflow/run-afk-workflow/SKILL.md`, 改为 direct recipes + 中文子代理 task.
3. 删除 `workflow.afk-worker` 所有文案.
4. 更新 `README.md`.
5. 运行验证命令.
6. 汇报 changed files, validation, residual risks.
