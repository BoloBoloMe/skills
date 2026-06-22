# 交接文档: ponytail 复刻到 skills 仓库

**日期**: 2026-06-23
**源会话**: ponytail 仓库探索, 方案讨论, 实施计划

---

## 摘要

用户发现 ponytail (https://github.com/DietrichGebert/ponytail, 48.9k stars), 一个让 AI agent 以最小代码工作的规则集. 目标: 将其核心复刻到本仓库 `D:/Workspace/skills`, 以中文版 skill + pi extension 形式 (方案 B).

已完成的阶段:
- ponytail 仓库完整探索, 架构分析
- 三轮方案讨论, 确定方案 B 和所有细节约定
- 实施计划已落盘

下一步: 按实施计划逐文件创建.

---

## 必读推荐

### 1. `docs/changes/ponytail-fork/exploration.md`
**理由**: ponytail 原始仓库的完整探索报告. 含 5 层架构分析, 文件清单, 每个核心文件的用途说明, 与本仓库现状的对比, 以及"不需要复刻"的清单.

### 2. `docs/changes/ponytail-fork/implementation-plan.md`
**理由**: 7 个文件的具体规格, 翻译规则, pi extension 设计, 事件流, level 默认值, 与现有 skill 的兼容性, 实现顺序, 风险边界. 这是实施阶段的直接依据.

---

## 路线图

### 用户真实意图

用户想在本仓库沉淀一套可复用的"最小化代码"规则集, 用于日常编码时约束 agent 行为. 选 ponytail 是因为它已被社区验证 (48.9k stars, 基准测试 -54% LOC). 复刻而非直接使用上游, 是因为需要中文翻译和与本仓库 skill 体系的整合.

### 关键里程碑

1. **发现 ponytail**: 用户搜索 "ponytail 简化代码", 找到 GitHub 仓库
2. **探索仓库**: 克隆到 `/tmp/ponytail-20260623`, 分析 5 层架构, 核心发现: 130 个文件中, 核心只有一段规则文本, 其余是分发机制
3. **方案 A vs B vs C 讨论**: 方案 A (纯 skill), 方案 B (skill + pi extension), 方案 C (合并到 AGENTS.md). 用户选 B
4. **细节约定确认**:
   - 放 `workflow/` 目录 (不是 `general/`)
   - 翻译中文 (代码/术语/命令保留英文)
   - 不复刻 AGENTS.md, README.md
   - 不集成 orchestrate
   - 命令不翻译
5. **澄清 AGENTS.md 作用**: 确认 AGENTS.md 是 SKILL.md 的严格子集, 用于无 plugin 机制的 agent 的零配置分发
6. **实施计划落盘**: `docs/changes/ponytail-fork/implementation-plan.md`

### 距离完成还剩

7 个文件待创建:

```
Phase 1: workflow/ponytail/SKILL.md           ← 核心, 翻译 skills/ponytail/SKILL.md
Phase 2: pi/ponytail/*                        ← 4 个 JS 文件, 从原仓库精简
Phase 3: workflow/ponytail-review/SKILL.md
Phase 4: workflow/ponytail-audit/SKILL.md
Phase 5: workflow/ponytail-debt/SKILL.md
Phase 6: workflow/ponytail-gain/SKILL.md
Phase 7: workflow/ponytail-help/SKILL.md
```

**源文件基准**: ponytail v4.7.0, 所有原始文件在 `/tmp/ponytail-20260623/`.

---

## 已确认的关键约定

- SKILL.md frontmatter: `name` 保留英文, `description` 翻译中文
- 代码, 命令, 技术术语, 路径: 保留英文
- 触发词: 保留英文 (如 `"review for over-engineering"`)
- 命令名: 保留英文 (`/ponytail`, `ponytail-review`)
- 不放入 `workflow/orchestrate` 决策树
- pi extension 通过 pi 的 skill API 读取 SKILL.md, 不硬编码相对路径
- level 默认值: `PONYTAIL_DEFAULT_MODE` env > `~/.config/ponytail/config.json` > `"full"`
- 与现有 AGENTS.md 电报文风格正交, 不合并