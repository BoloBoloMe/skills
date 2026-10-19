# 本轮独立验收派工计划

- 目标提交: 5d3765e9b0d8228b8738a75ea69baef048402c45 (HEAD, feat: greet 支持全大写输出)
- 判据来源: docs/changes/tool-cli/PRODUCT.md, 验收标准节 (<!-- confirmed-flow: v1 -->)
- 证据目录: docs/changes/tool-cli/verify-5d3765e-r1/ (仓库内)
  - 影响判断: build.sh 只编译 tool.py; prepare.sh 只跑 tools/build_manifest.py; pytest 只发现 tests/. 该目录不被任何构建或测试发现读取, 可留在仓库内. 本轮只新增验收输出.
- 必验清单 (3 条):
  1. AC-001-1 第一行内容 = `tool-cli 1`
  2. AC-002-1 第二行内容 = `commands=greet,count,export`
  3. AC-003-1 第三行内容 = `greet-shout=yes`
  - 业务规则节无标 (审计) 的规则, BR-001 只作为 AC-003-1 的语义背景, 不单列.

## 分组

- 唯一场景组 G-A: AC-001-1, AC-002-1, AC-003-1 一起承接.
  依据: 三条场景同一前置 (`bash prepare.sh` 生成 `dist/app.txt`), 读同一份文件的不同行, 属同一份产物.

## 人数

- 当轮可用非作者验收者上限: 3 人.
- 计划人数: 1 人.
- 理由: 三条场景共用同一份前置产物 dist/app.txt, 且该产物生成在工作区单一 dist/ 路径下. 拆给多人就必须各自重复跑一次约 25 秒的 prepare.sh, 还会争用同一个 dist/app.txt, 准备成本与资源冲突都大于并行收益. 按规则只派一人依次做完, 不按 AC 逐条开会话.

## 委派权限

- 验收者只读被验项目, 不改源码/配置/测试; 临时文件只写证据目录.
- 验收者必须是本轮新开会话, 不继承实现会话上下文.
