# 资产布局

HITL 0.0.1 资产包根目录固定为 `docs/changes/<中文变更>/`，只允许以下正式布局：

```text
manifest.yaml
human-view.html              # 派生产物；初始化不创建
agent/
  <artifact>.vN.yaml         # 当前有效 agent 资产
  archive/
    <artifact>.vN.yaml       # superseded/retired/failed/closed 历史资产
```

## 初始化行为

`init_hitl_package.py` 只创建：

- `manifest.yaml`
- `agent/`
- `agent/archive/`

## 写入与归档

所有 agent 资产必须通过 `write_agent_asset.py` 写入并登记 `registry.path`。历史状态只能通过 `archive_asset.py` 移入 `agent/archive/`。

每次写入、替换或归档 agent 资产后，脚本必须同步刷新 `human-view.html` 与 `human-view@current`。初始化阶段是唯一允许暂时不存在 `human-view.html` 的阶段。

唯一正式人类审核入口是根部 `human-view.html`，由 `transform_human_view.py` 生成。
