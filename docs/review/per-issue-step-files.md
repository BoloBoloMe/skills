# 审核: Per-issue 步骤文件生成 — 过度工程

日期: 2026-07-04

## 背景

`blinders` 改造后, to-issues 在发布 AFK issue 时, 为每个 issue 在产物目录生成 15 个步骤文件 (`step-01.md` ~ `step-15.md`) 和 `_current.md`. 父会话按 `_current.md` 读取当前步骤机械执行.

步骤文件内容由 `step-gen-guide.md` 模板生成, `<...>` 占位符替换为 issue 特定的绝对路径.

## 问题

Per-issue 步骤文件生成存在过度工程.

### 1. 与 prompt 重构原则矛盾

prompt 重构建立了核心原则: **静态内容不按实例复制**. 旧 prompt 模型是"父会话读 prompt → 替换占位符 → 传给子代理". 新模型是"prompt 文件静态, 父会话将路径注入 task". 而步骤文件仍然沿用旧模型: 编译期生成 N 份路径不同的副本.

父会话**已经在做路径注入** (给子代理的 task 里写 `角色文件: xxx`, `输入文件: xxx`). 同样的能力可以用于自己执行的步骤模板, 不需要预烘焙.

### 2. 文件爆炸

N 个 AFK issue 产生 N × 16 个文件. 其中 1 个 `_current.md` 是 issue 特有的, 15 个步骤文件重复同一份模板, 唯一差异是 baked-in 的绝对路径.

5 个 issue → 80 个文件, 其中 75 个文件承载的信息量等于 1 个模板文件 + 1 个 per-issue config.

### 3. 生成成本

to-issues 必须加载 348 行的 `step-gen-guide.md`, 为每个 issue 做 15 次占位符替换. 此成本与 issue 数成线性关系. 如果将来步骤数增加到 20 或 issue 数增加到 10, 成本继续放大.

### 4. 眼罩原则的血肉分离

当前设计靠纪律 ("不要读其他 step-NN.md") 防止父会话窥探后续步骤. 这是口头约束, 不是结构约束. 15 个步骤文件明文躺在同一目录, 父会话的模型有能力读取任意文件.

如果把步骤文件放在 issue 产物目录之外的共享位置, 父会话手里只有 `_current.md` 给出的具体路径, 不暴露目录整体.

### 5. `_current.md` 承载了唯一真正 per-issue 的状态

步骤文件不是 per-issue 的 — 它们描述工作流逻辑, 对所有 AFK issue 通用. `_current.md` 才是唯一 per-issue 的: 它记录"这个 issue 执行到哪了". 当前设计混淆了工作流定义 (what to do) 和工作流状态 (where we are).

## 决议

### 方案: 7 步 × 全局一份, `_current.md` 格式 `ISSUE-KEY:NN`

**文件布局**:

```
docs/changes/<slug>/afk-running/
  _current.md               ← "ISSUE-01:03" (当前 issue + 步骤)
  step-01.md ~ step-07.md   ← 7 个, 全 issue 共用
  ISSUE-01/                  ← per-issue 产物
  ISSUE-02/
```

**父会话执行循环**:

1. 读 `_current.md` → 解析 `<issueKey>` 和 `<stepNN>`
2. 读 `step-NN.md` → 按指引执行, 路径按目录约定推断
3. 更新 `_current.md`

**per-feature 固定: 8 个文件** (`_current.md` + 7 step files). 不随 issue 数增长.

**关键决策**:

- `_current.md` 格式: `<issueKey>:<stepNN>` (如 `ISSUE-01:03`).
- 不设 `index.md`, issue 文件按 `issues/<NN>-<slug>.md` 约定定位.
- contract 和 decisions 在 feature 根目录, 固定文件名.
- 步骤文件不含 baked-in 路径, 全部按约定推断.
- 步骤 07 出口: 扫描 `afk-running/` 下未完成 issue → 切换; 全部完成 → `done`.
- 步骤文件内容从 SKILL.md 工作流中提取, 父会话初始化时生成一次. skill 本身不提供步骤模板文件.

## 影响评估

| 维度 | 旧方案 (per-issue 15 步) | 决议方案 |
|------|------------------------|---------|
| 步骤文件数 | 15 × N (N=issue 数) | 7 (固定) |
| per-feature 总文件数 | 1 + 15N | 8 (固定) |
| 步骤文件位置 | per-issue 产物目录 | afk-running/ 根 |
| 盲视保证 | 纪律约束 | 同 (一次只持一个) |
| 多 issue 编排 | 无 (per-issue 独立) | step-07 自动切换到下一 issue |
| 生成者 | to-issues | 父会话初始化时一次 |
| 路径来源 | baked-in 绝对路径 | 目录约定推断 |

## 置信度

**高**. 前提矛盾 (父会话已在做路径注入) 是强证据. 文件爆炸是可量化的客观问题.
