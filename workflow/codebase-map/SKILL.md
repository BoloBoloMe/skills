---
name: codebase-map
description: 把代码库结构与依赖分层可视化成可交互页面, 手动查看用, 不被任何 skill 调用.
disable-model-invocation: true
---

纯手动工具: 只由用户手动调用, 任何 skill (含 to-spec) 都不调用它 (m13 D001). 职责只有一件事: 出"代码库结构与分层"的可视化页面, 不做架构评审, 不产重构建议, 不参与验收判断.

## 组成

- `tools/build-zh.sh`: 前端汉化构建流水线 (克隆钉死的上游 tag -> 三通道替换 -> npm build -> 渲染冒烟), 产物在 `~/.agents/codebase-map/cache/`.
- `tools/stage.py`: 把前端产物与数据副本铺进服务根 `~/.agents/codebase-map/serve-root/` (m13 D023/D024).
- `i18n/`: 三通道词表 (模板 355 条 / .ts 白名单 346 条 / 绑定内字面量 44 条, 术语单一译法按 D015).
- `README.md`: 操作手册 (分析端与前端命令, 数据交付, 升级流程, 已知坑), 逐条挂决策编号.

## v1 服务边界

本 skill 只交付汉化构建链与布局铺设. 常驻服务 (build/serve/stop 三子命令, 单例端口 8090, state.json 探活) 属 milestone-26 的 v1 实现 (m13 D027/D030, m24 U004); 在它就位前, 用 README 里的临时静态服务命令查看页面.
