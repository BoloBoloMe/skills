# ponytail 仓库探索报告

**源仓库**: https://github.com/DietrichGebert/ponytail
**克隆位置**: /tmp/ponytail-20260623
**Stars**: 48.9k | **Forks**: 2.4k | **License**: MIT
**探索日期**: 2026-06-23

## 仓库规模

- 总文件数: 130 (不含 .git)
- JavaScript/ESM: ~2600 行
- Markdown: ~4300 行
- Python: ~1500 行
- JSON/TOML/YAML: ~420 行

## 核心分层

ponytail 仓库为 14 种 AI agent 提供同一套规则的不同分发形式. 按关注点分离为 5 层:

```
层 1: 规则文本 (Ruleset)          ← 核心灵魂, 唯一真实来源
层 2: Hook/Plugin 层 (Node.js)    ← Claude Code / Codex / Copilot 分发
层 3: Pi Extension                ← Pi agent 分发
层 4: 辅助 Skills                 ← review / audit / debt / gain / help
层 5: 其他                        ← benchmarks, examples, MCP, docs, commands
```

---

## 层 1: 规则文本 (Ruleset) — 核心

### 1.1 `AGENTS.md` (精简版, ~30 行)

所有 agent 适配器的共同版本. 包含:

- 核心身份声明: "You are a lazy senior developer. Lazy means efficient, not careless."
- 6 级阶梯决策 (The Ladder)
- 7 条规则 (不写抽象, 不引入依赖, 不写样板, 删除优先, 质疑复杂请求, 边缘情况选正确方案, ponytail: 注释)
- 安全底线: 不砍校验/错误处理/安全/无障碍/硬件校准
- 测试纪律: 非平凡逻辑留一个 runnable check

### 1.2 `skills/ponytail/SKILL.md` (完整版, ~100 行)

相对于 `AGENTS.md` 的增量:

- Skill frontmatter (name, description, argument-hint)
- Persistence 声明: ACTIVE EVERY RESPONSE
- 阶梯展开: 每级有示例 (`<input type="date">` over picker lib)
- 规则展开: 更具体的反模式描述
- 输出格式规范: "Code first. Then at most three short lines. 如果解释比代码长, 删解释"
- 三级强度: lite / full / ultra, 含表格和 worked example
- 硬件校准: 真实世界不是理想规格
- 边界: 只控制 what you build, 不控制 how you talk

### 1.3 各 Agent 适配器 (规则文本副本)

所有这些文件内容与 `AGENTS.md` 完全相同, 仅 frontmatter 不同:

| 文件 | 目标 Agent | Frontmatter |
|------|-----------|-------------|
| `.cursor/rules/ponytail.mdc` | Cursor | `alwaysApply: true` |
| `.clinerules/ponytail.md` | Cline | 无 frontmatter |
| `.windsurf/rules/ponytail.md` | Windsurf | 无 frontmatter |
| `.github/copilot-instructions.md` | GitHub Copilot | 无 frontmatter |
| `.agents/rules/ponytail.md` | Antigravity / 通用 | 无 frontmatter |
| `.kiro/steering/ponytail.md` | Kiro | `inclusion: always` |

**关键发现**: 这些文件是同一规则文本的 N 份副本, 通过 `scripts/check-rule-copies.js` 保持同步. 这是该仓库最大的维护负担.

---

## 层 2: Hook/Plugin 层 (Node.js)

Claude Code / Codex / Copilot 的插件分发. 核心文件:

### 2.1 `hooks/ponytail-config.js` (~80 行)

配置解析器:

- 四级 mode: `off`, `lite`, `full`, `ultra` (加 `review` 作为独立 mode)
- 默认值解析链: `PONYTAIL_DEFAULT_MODE` env > `~/.config/ponytail/config.json` > `"full"`
- 停用检测: `isDeactivationCommand()` — 精确匹配 "stop ponytail" / "normal mode"
- 跨平台 config 目录: XDG, APPDATA, ~/.config

### 2.2 `hooks/ponytail-instructions.js` (~80 行)

指令生成器:

- 从 `skills/ponytail/SKILL.md` 读取完整规则
- `filterSkillBodyForMode()` — 按 intensity level 过滤 mode-specific 行 (表格行和 worked example)
- `getFallbackInstructions()` — 硬编码的 fallback 版本 (当 SKILL.md 不可读时)
- Pi Extension 也复用此模块

### 2.3 `hooks/ponytail-activate.js` (~70 行)

SessionStart hook:

- 写 flag file (`~/.claude/.ponytail-active`) 供 statusline 读取
- 调用 `getPonytailInstructions()` 生成规则文本注入 session
- 检测 statusline 配置缺失, 生成 setup nudge
- `off` mode 时跳过激活

### 2.4 `hooks/ponytail-mode-tracker.js` (~50 行)

UserPromptSubmit hook:

- 解析 `/ponytail` 命令, 切换 mode
- 写 flag file 更新状态
- 检测 "stop ponytail" / "normal mode" 停用

### 2.5 `hooks/ponytail-runtime.js` (~40 行)

运行时工具:

- 写/清 flag file
- 适配 Claude Code / Codex / Copilot 三种输出格式
- Codex 用 `systemMessage`, Copilot 用 `additionalContext`

### 2.6 `hooks/ponytail-statusline.sh` / `.ps1`

Shell 脚本, 读取 flag file 显示状态栏标记 (如 `[PONYTAIL]`, `[PONYTAIL:ULTRA]`).

### 2.7 Plugin 清单文件

- `.claude-plugin/plugin.json` + `marketplace.json`
- `.codex-plugin/plugin.json`
- `.github/plugin/plugin.json` + `marketplace.json`
- `.agents/plugins/marketplace.json`
- `gemini-extension.json`

这些文件定义 hooks 注册, 命令和 marketplace 元数据.

---

## 层 3: Pi Extension

### 3.1 `pi-extension/index.js` (~120 行)

Pi agent 的扩展入口:

- 复用 `hooks/ponytail-config.js` 和 `hooks/ponytail-instructions.js`
- 注册 6 个命令: `/ponytail`, `/ponytail-review`, `/ponytail-audit`, `/ponytail-gain`, `/ponytail-debt`, `/ponytail-help`
- `on("session_start")`: 从 session entries 恢复 mode
- `on("before_agent_start")`: 将过滤后的规则注入 `systemPrompt`
- `on("input")`: 检测 "stop ponytail" / "normal mode" 停用命令
- `parsePonytailCommand()`: 解析 `/ponytail lite|full|ultra|off|status|default`
- `resolveSessionMode()`: 从 session entries 恢复上次 mode

### 3.2 `pi-extension/package.json`

最小化 `package.json`, 仅声明 `type: "module"` 和 test script.

---

## 层 4: 辅助 Skills

### 4.1 `skills/ponytail-review/SKILL.md`

Diff 审查, 专找过工程. 输出格式: `L<line>: <tag> <what>. <replacement>.`

5 种 tag: `delete`, `stdlib`, `native`, `yagni`, `shrink`. 结尾: `net: -<N> lines possible.`

### 4.2 `skills/ponytail-audit/SKILL.md`

全仓库审计. 与 ponytail-review 相同格式, 但扫描整个代码库. 按砍掉行数从大到小排序.

### 4.3 `skills/ponytail-debt/SKILL.md`

收集所有 `ponytail:` 注释, 生成债务账本. 标记 `no-trigger` 风险. 只读, 不修改文件.

### 4.4 `skills/ponytail-gain/SKILL.md`

显示基准测试收益的 ASCII 记分牌. 一次性展示, 不修改 mode.

### 4.5 `skills/ponytail-help/SKILL.md`

快速参考卡: levels, skills, 停用, 默认配置, 更新.

### 4.6 辅助 Skills 的多平台副本

- `.openclaw/skills/ponytail*/SKILL.md` — OpenClaw 格式 (由 `scripts/build-openclaw-skills.js` 从 `skills/` 生成)
- `.opencode/command/ponytail*.md` — OpenCode 命令格式

---

## 层 5: 其他

### 5.1 `benchmarks/`

基准测试框架, 含:

- `agentic/` — 真实 agentic 基准 (FastAPI + React 仓库, 12 个 feature tasks)
- `arms/` — 对比 arm (baseline, caveman, ponytail)
- `promptfooconfig*.yaml` — promptfoo 配置
- `results/` — 历史基准结果
- correctness tests, behavior tests, robustness audit

### 5.2 `examples/`

11 个 before/after 代码示例 (email-validation, debounce, deep-clone, csv-sum, 等).

### 5.3 `ponytail-mcp/`

MCP 服务器, 提供 `ponytail_instructions` tool.

### 5.4 `commands/`

6 个 `.toml` 文件定义 Claude Code 命令.

### 5.5 `docs/`

- `agent-portability.md` — 各 agent 如何加载 ponytail
- `platform-native.md` — 平台原生特性参考

---

## 当前仓库 `D:/Workspace/skills` 现状

### 目录结构

```
skills/
├── AGENTS.md              # 电报文风格, 文档目录结构约定
├── README.md              # 仓库说明, 技能一览
├── general/               # 通用交互与写作类技能 (browse-web, explore-repo, grilling, ...)
├── workflow/              # 面向代码库工作的流程技能 (orchestrate, tdd, diagnosing-bugs, ...)
├── others/                # 特定技术栈辅助技能 (payment-review, springboot-hcurl-generator)
├── pi/                    # Pi agent 本地配置
├── deprecated/            # 已归档技能 (hitl, telegraphic-style, zoom-out)
└── docs/
    └── agents/            # issue-tracker, triage-labels, domain 约定
```

### 现有 Skill 模式

每个 skill 是一个独立目录, 至少含 `SKILL.md` 作为入口. 例如:

```
general/browse-web/
├── SKILL.md
├── REFERENCE.md
└── scripts/
    └── browse_web.py
```

### 关键约束

- 本仓库是 skill 源码与资料仓库, 不声明目录会被 agent 自动发现
- 真实使用时需按目标 agent 的安装方式安装或链接
- 仓库内已有 `AGENTS.md` 定义电报文风格
- 已有 `docs/changes/` 用于 issue tracker

---

## 最小复刻方案分析

### 核心问题: 什么是 ponytail 的"最小版本"?

ponytail 的本质是一个 **prompt engineering 规则集**. 所有 Node.js hooks, 插件清单, benchmark, MCP, 多平台适配器都是分发机制. 核心只有一个东西:

> **阶梯式最小化决策规则 + 安全底线**

### 方案 A: 纯 Skill 方式 (推荐)

在 `general/ponytail/` 下创建一个 skill, 包含:

```
general/ponytail/
├── SKILL.md              # 完整版规则 (从 skills/ponytail/SKILL.md 精简)
├── AGENTS.md             # 精简版规则 (从 AGENTS.md 复制, 用于全局指令)
└── README.md             # 说明: 本 skill 是什么, 怎么用
```

**优点**:
- 符合本仓库现有 skill 组织模式
- 零依赖 (不需要 Node.js runtime)
- 可以被 pi 的 skill 系统加载
- 也可以手动复制到目标项目的 `AGENTS.md` 或 `.cursor/rules/` 中使用

**缺点**:
- 没有 mode 切换 (lite/full/ultra/off)
- 没有 `/ponytail` 命令
- 没有 session 持久化

### 方案 B: Skill + Pi Extension

在方案 A 基础上增加 `pi/ponytail/` 扩展目录:

```
general/ponytail/
├── SKILL.md
├── AGENTS.md
└── README.md

pi/ponytail/
├── index.js              # 从 pi-extension/index.js 精简
├── package.json
└── README.md
```

**优点**:
- 保留 level 感知 (lite/full/ultra) 和 `/ponytail` 命令
- pi 安装后自动注入 system prompt

**缺点**:
- 增加 Node.js 依赖
- 需要维护 `hooks/ponytail-config.js` 和 `hooks/ponytail-instructions.js` 的依赖

### 方案 C: 仅全局 AGENTS.md 规则

将 ponytail 规则直接合并到当前仓库的 `AGENTS.md` 中.

**优点**:
- 最简单
- 对本仓库所有 agent 自动生效

**缺点**:
- 与已有的电报文风格可能冲突
- 难以按需开关
- 无法分发到其他项目

### 方案选择建议

**推荐方案 A**, 原因:

1. 本仓库是 skill 集合仓库, ponytail 是一个编码风格 skill, 天然适合放在 `general/` 下
2. 零依赖, 零运行时, 可直接用
3. 后续可按需升级到方案 B (增加 pi extension 层)
4. 辅助 skills (review/audit/debt) 也可按需逐步添加

### 增量路径

```
Phase 1: general/ponytail/SKILL.md + AGENTS.md     ← 核心规则, 立即可用
Phase 2: general/ponytail-review/SKILL.md           ← 审查 skill
Phase 3: general/ponytail-audit/SKILL.md            ← 审计 skill
Phase 4: pi/ponytail/ 扩展                          ← 可选: pi 集成
```

### 与其他 skill 的交互

- `ponytail` 与 `grilling` 正交: ponytail 管 you build what, grilling 管 you decide what
- `ponytail` 与 `tdd` 兼容: ponytail 要求非平凡逻辑留一个 runnable check, tdd 提供完整测试框架
- `ponytail` 与 `codebase-design` 互补: ponytail 防止过度设计, codebase-design 指导何时需要 deep module
- `ponytail` 与 `AGENTS.md` 电报文风格共存: ponytail 管代码产出, 电报文管对话风格

### 从 ponytail 仓库中不需要复刻的部分

| 不需要 | 原因 |
|--------|------|
| `hooks/` | 仅 Claude Code/Codex/Copilot 需要 |
| `.claude-plugin/`, `.codex-plugin/`, `.github/plugin/` | 插件清单, 仅限于特定 agent |
| `.cursor/rules/`, `.clinerules/`, `.windsurf/rules/`, `.kiro/steering/`, `.agents/rules/` | 规则文本副本, 本仓库不直接分发 |
| `benchmarks/` | 基准测试, 与 skill 核心无关 |
| `examples/` | 示例, 可选参考 |
| `ponytail-mcp/` | MCP 服务器, 额外分发渠道 |
| `commands/` | Claude Code 命令定义 |
| `tests/` | 测试 ponytail 自身 |
| `scripts/` | 维护脚本 (check-rule-copies, build-openclaw-skills) |
| `assets/` | 图片和 logo |
| `gemini-extension.json`, `opencode.json` | 特定 agent 配置 |
| `.openclaw/`, `.opencode/` | 辅助 skill 副本, 仅特定 agent 需要 |

### 风险与边界

1. **规则文本是 fork 的, 不是 link 的**: 上游 ponytail 更新时不会自动同步. 需要手动检查更新或在 README 中注明 base version.
2. **电报文风格冲突**: ponytail 的 "Output: Code first. Then at most three short lines." 与当前 `AGENTS.md` 的电报文风格互补但不完全相同. ponytail 更激进: "如果解释比代码长, 删解释". 需评估是否要调整.
3. **Level 缺失**: 纯 Skill 方式没有 lite/full/ultra 切换. 但可以通过在 SKILL.md 中固定 level (推荐 full) 来规避. 或者提供三个独立的 SKILL.md 变体.
4. **辅助 Skills 的 token 成本**: review/audit/debt/gain/help 每个 ~40-60 行, 总计约 250 行. 按需加载不会显著增加上下文.