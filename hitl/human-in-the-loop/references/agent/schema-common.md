# Agent Asset 通用结构

所有 agent 资产都是原始 YAML 文件，并以最小头字段开头：

```yaml
asset_ref: planning/design@v1
artifact: design
schema_version: "0.0.1"
```

agent asset 内不得写入：

- lifecycle_state
- record_role
- owner_skill
- owner_protocol
- approval
- confirmation
- human_view
- agent_view

这些字段由 manifest 管理。

## YAML 子集限制

脚本为零依赖实现，只支持保守 JSON/YAML 子集：普通 mapping、list、string、number、boolean、null，以及 JSON 风格的内联数组/对象。不支持 YAML block scalar（`|`/`>`）、锚点、复杂多文档或隐式高级类型。需要多行正文时，优先写成字符串列表或 JSON 转义字符串。

## 语言要求

所有面向人类审阅的正文值必须使用用户提出 HITL 请求时所用的主要语言，包括目标、范围、候选方案、取舍理由、风险、验证说明、摘要、执行步骤和结论。仅以下内容可保留原文：代码标识符、文件路径、命令、asset_ref、协议字段名、第三方产品名和原始错误片段。
