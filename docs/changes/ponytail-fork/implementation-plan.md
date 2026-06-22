# ponytail 复刻实现方案

**基准**: ponytail v4.7.0 (https://github.com/DietrichGebert/ponytail)
**目标仓库**: D:/Workspace/skills
**状态**: 待确认

---

## 1. 文件清单

```
workflow/ponytail/
└── SKILL.md              # 中文版核心规则, 从 skills/ponytail/SKILL.md 翻译

workflow/ponytail-review/
└── SKILL.md              # 中文版, 从 skills/ponytail-review/SKILL.md 翻译

workflow/ponytail-audit/
└── SKILL.md              # 中文版, 从 skills/ponytail-audit/SKILL.md 翻译

workflow/ponytail-debt/
└── SKILL.md              # 中文版, 从 skills/ponytail-debt/SKILL.md 翻译

workflow/ponytail-gain/
└── SKILL.md              # 中文版, 从 skills/ponytail-gain/SKILL.md 翻译

workflow/ponytail-help/
└── SKILL.md              # 中文版, 从 skills/ponytail-help/SKILL.md 翻译

pi/ponytail/
├── index.js              # pi extension 入口, 从 pi-extension/index.js 精简
├── package.json
├── config.js             # 从 hooks/ponytail-config.js 精简
└── instructions.js       # 从 hooks/ponytail-instructions.js 精简
```

**不包含**: AGENTS.md, README.md, benchmarks, examples, commands, hooks, MCP, 各 agent 适配器副本, 辅助 skills 的 OpenClaw/OpenCode 副本.

---

## 2. 翻译规则

### 翻译为中文

- SKILL.md frontmatter 的 `description` 字段
- 说明性文字: 规则解释, 行为描述, 示例旁白, 表格标题
- 输出格式说明

### 保留英文

- SKILL.md frontmatter 的 `name` 字段
- 代码, 命令, 路径, 技术术语
- 触发词 (如 `"review for over-engineering"`)
- 命令名 (`/ponytail`, `ponytail-review`)
- `ponytail:` 注释标记

### 示例

原始:
```
description: >
  Forces the laziest solution that actually works, simplest, shortest, most
  minimal. Use whenever the user says "ponytail", "be lazy"...
```

翻译后:
```
description: >
  强制执行最懒但实际可用的方案, 最简单, 最短, 最精简.
  当用户说 "ponytail", "be lazy", "lazy mode", "simplest solution",
  "minimal solution", "yagni", "do less", "shortest path",
  或抱怨过工程, 膨胀, 样板, 不必要依赖时使用.
```

原始:
```
Stop at the first rung that holds:
1. Does this need to exist at all? (YAGNI)
2. Stdlib does it? Use it.
```

翻译后:
```
在第一个成立的阶梯处停下:
1. 这东西需要存在吗? (YAGNI)
2. 标准库能做吗? 用标准库.
```

---

## 3. pi Extension 设计

### 3.1 架构

```
pi/ponytail/
├── index.js          ← 注册命令, 监听事件, 注入 prompt
├── package.json      ← { "type": "module" }
├── config.js         ← mode 解析, 默认值, 停用检测
└── instructions.js   ← 读取 SKILL.md, 按 level 过滤, 生成指令
```

与原始 ponytail 的差异:

| 原始 | 方案 B |
|------|--------|
| 通过 pi plugin marketplace 安装 | 用户手动安装到 pi extensions 目录 |
| `instructions.js` 从 `../skills/ponytail/SKILL.md` 读取 | 从 pi 规范路径读取 (具体路径由 pi 的 skill 发现机制决定) |
| 支持 statusline | 不支持 |
| 注册 6 个命令 | 同 |
| 状态文件 (`~/.claude/.ponytail-active`) | 不写文件, 通过 pi 的 session entries 持久化 |

### 3.2 命令

```
/ponytail                    → 报告当前 level
/ponytail lite|full|ultra    → 切换 level
/ponytail off                → 关闭
/ponytail status             → 显示当前 level + 默认 level
/ponytail-review             → 触发 ponytail-review skill
/ponytail-audit              → 触发 ponytail-audit skill
/ponytail-debt               → 触发 ponytail-debt skill
/ponytail-gain               → 触发 ponytail-gain skill
/ponytail-help               → 触发 ponytail-help skill
```

停用: 输入 "stop ponytail" 或 "normal mode" 时关闭.

### 3.3 事件流

```
pi 启动
  │
  ├─→ session_start
  │     └─→ 从 session entries 恢复上次 level
  │
  ├─→ before_agent_start
  │     └─→ 读取 SKILL.md, 按 level 过滤, 追加到 systemPrompt
  │
  └─→ input
        └─→ 检测 /ponytail 命令 → 切换 level
        └─→ 检测 "stop ponytail" / "normal mode" → 关闭
```

### 3.4 level 默认值

```
PONYTAIL_DEFAULT_MODE 环境变量
  → ~/.config/ponytail/config.json 的 defaultMode 字段
    → "full" (硬编码)
```

### 3.5 SKILL.md 路径

SKILL.md 的读取路径是 pi 的 skill 发现路径, 不是本仓库路径. 用户在 pi 中安装 skill 后, pi 将 skill 目录注册到 skill registry. extension 通过 pi 的 API 获取 skill 内容, 而不是硬编码相对路径.

具体实现: `instructions.js` 通过 pi 的 `getSkillContent("ponytail")` 或类似机制获取 SKILL.md 正文, 而不是直接 `fs.readFileSync`.

---

## 4. 各 SKILL.md 内容规格

### 4.1 workflow/ponytail/SKILL.md

从 `skills/ponytail/SKILL.md` 翻译, 保留:

- frontmatter (name, description, argument-hint, license)
- 身份声明 + Persistence
- 6 级阶梯 + 每级示例
- 7 条规则 + 反模式展开
- 输出格式规范
- 三级强度表格 + worked example
- 安全底线 (校验, 错误处理, 安全, 无障碍, 硬件校准)
- 测试纪律
- 边界声明

**不保留**: 与 Caveman 的联动说明 (原 SKILL.md 末尾 "pair with Caveman for terse prose")

### 4.2 workflow/ponytail-review/SKILL.md

从 `skills/ponytail-review/SKILL.md` 翻译, 保留全部.

### 4.3 workflow/ponytail-audit/SKILL.md

从 `skills/ponytail-audit/SKILL.md` 翻译, 保留全部.

### 4.4 workflow/ponytail-debt/SKILL.md

从 `skills/ponytail-debt/SKILL.md` 翻译, 保留全部.

### 4.5 workflow/ponytail-gain/SKILL.md

从 `skills/ponytail-gain/SKILL.md` 翻译, 保留全部.

### 4.6 workflow/ponytail-help/SKILL.md

从 `skills/ponytail-help/SKILL.md` 翻译, 保留全部.

---

## 5. 与现有仓库的交互

### 不集成到 orchestrator

ponytail 是编码风格 skill, 不是流程 skill. 不进入 `workflow/orchestrate` 的决策树.

### 与现有 AGENTS.md 的关系

`D:/Workspace/skills/AGENTS.md` 定义电报文风格. ponytail 管代码产出, 电报文管对话风格. 两者正交, 不合并.

### 与现有 skill 的兼容性

| Skill | 与 ponytail 的关系 |
|-------|-------------------|
| tdd | 互补: ponytail 要求非平凡逻辑留一个 runnable check, tdd 提供完整测试框架 |
| codebase-design | 互补: ponytail 防止过度设计, codebase-design 指导何时需要 deep module |
| grilling | 正交: ponytail 管 you build what, grilling 管 you decide what |
| diagnosing-bugs | 互补: ponytail 最小化新代码, diagnosing-bugs 最小化复现 |

---

## 6. 实现顺序

```
Phase 1: workflow/ponytail/SKILL.md           ← 核心, 先做
Phase 2: pi/ponytail/*                        ← extension, 依赖 Phase 1
Phase 3: workflow/ponytail-review/SKILL.md    ← 辅助 skill
Phase 4: workflow/ponytail-audit/SKILL.md
Phase 5: workflow/ponytail-debt/SKILL.md
Phase 6: workflow/ponytail-gain/SKILL.md
Phase 7: workflow/ponytail-help/SKILL.md
```

---

## 7. 风险与边界

1. **SKILL.md 路径**: pi extension 读取 SKILL.md 的方式取决于 pi 的 skill API. 如果 pi 当前没有 `getSkillContent()` 等 API, 需要回退到 `fs.readFileSync` 并约定安装路径.
2. **翻译质量**: 中文翻译可能改变原始 prompt 的调性. 翻译后需验证 agent 行为是否一致.
3. **上游更新**: ponytail 上游更新时, 需手动同步. 建议在 SKILL.md 注释中标注 base version 和 commit hash.
4. **level 过滤逻辑**: `filterSkillBodyForMode()` 依赖 SKILL.md 中表格行和 worked example 的特定格式. 中文翻译后格式不变, 仅文本翻译, 过滤逻辑不受影响.
5. **pi 兼容性**: 需确认 pi 的 extension API 是否支持 `registerCommand`, `on("session_start")`, `on("before_agent_start")`, `on("input")`, `appendEntry`, `sendUserMessage` 等接口.