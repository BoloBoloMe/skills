# Pi Token 统计插件

## 目的地

完成一个 pi token 统计插件的开发与安装; 该插件能按内容分类统计任意会话 (含历史会话) 的 token 使用情况.

## 笔记

- 领域: pi 插件机制, 会话 JSONL 格式, token usage 数据结构
- 参考: Claude Code token 统计功能
- 插件运行在 pi extensions 框架上, TypeScript 编写

## 已关闭决策

- [ITEM-01](ITEM-01.md): Usage 结构 `{input,output,cacheRead,cacheWrite,cacheWrite1h?,reasoning?,totalTokens}` 为唯一精确数据源, 不拆分 input by role. `getContextUsage()` 混合精度 (精确+chars/4估算), 无内置 tokenizer, `before_provider_request` 暴露完整 messages 可自行估算. 详见 [ITEM-01-findings.md](ITEM-01-findings.md)
- [ITEM-02](ITEM-02.md): Claude Code 用 `/cost` 命令, 分类为 system prompt / tools / messages / attachments / cache / output, 全量来自 API usage 不自己 tokenize. 支持 session + all-time 双层统计. 详见 [ITEM-02-findings.md](ITEM-02-findings.md)

## 前沿

- [ITEM-03](ITEM-03.md) — `grilling` — 分类体系设计
- [ITEM-04](ITEM-04.md) — `grilling` — UI 交互设计 (已关闭)

## 决策账本

- [DECISIONS.md](DECISIONS.md) — D001~D010 功能级决策记录

## 未决迷雾

- **插件分发方式**: npm 包还是本地文件? 等设计定型再定

## 范围外

- 计费/预算控制 (只统计, 不计费)
- 跨设备同步
- 实时用量预警

## 阻塞关系

```
ITEM-01 ─┬─► ITEM-03 ─► ITEM-05 ─► ITEM-06
ITEM-02 ─┘    ITEM-04 ─┘
```

- ~~ITEM-01~~ (已关闭): pi token usage 暴露面调查
- ~~ITEM-02~~ (已关闭): Claude Code token 统计参考
- ITEM-03 (grilling, 阻塞于 ~~ITEM-01, ITEM-02~~): 分类体系设计
- ~~ITEM-04~~ (已关闭): UI 交互设计
- ITEM-05 (prototype, 阻塞于 ITEM-03, ITEM-04): 核心统计逻辑原型
- ITEM-06 (task, 阻塞于 ITEM-05): 历史会话批量统计实现
