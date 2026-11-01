# milestone-24 裁决记录 (milestone-23 探针暴露的冲突)

产物根: `docs/changes/workflow-stack-review/milestone-24/`.
性质: 用户在本会话直接裁决 (2026-11-01), 代理未替答. 依据材料为 `../milestone-23/PROBE.md` 与 `../milestone-23/REVIEW.md`.
与 `../milestone-13/DECISIONS.md` 的关系: 本文件裁决的条目替代那里对应的旧条文, 旧条文保留历史, 不重写原文.

## 决策

### U001 接受"未解析名字比例"无法验证
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 工具没有"未解析 import/名字解析率"的定义与输出, 该门禁项永久不可按 D029 字面执行. 用户裁决接受现状, 以已实测事实作为继续实施的依据: 语法解析失败 0 个文件, 依赖边 8820 条, 文件层号 0-7 共 8 种, 环边 10, 向上依赖边 191. 不再要求补证, 也不得把该项写成"已验证".
- 后果: 交付时必须如实说明"依赖抽取完整性未量化", 不得宣称分层完全可信; 若日后要量化, 需另立研究(需上游新增输出或自建分析).

### U002 镜像引用改为官方纯数字 tag
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: 分析端镜像固定为 `docker.io/codecharta/codecharta-analysis:2.3.0`, 版本核对以 manifest digest 为准 (`sha256:6402a87f...`), 不信 `ccsh --version` (镜像内自报 2.2.1, 原因未查明). 不使用 `ana-2.3.0`; 该写法实为 GitHub release 命名, 在 docker hub 不存在.
- 后果: 替代 milestone-13 D002 的 tag 写法, 版本号 2.3.0 不变.

### U003 指标与展示"按官方的来"
- 状态: 当前有效
- 约束性: 必须遵守
- 内容: v1 不把层号拷进 metrics lens, 不做 build 后处理改动官方指标, 不改官方默认 URL 参数. 层号、环、向上依赖通过官方依赖视图 (`#/dependencies`, 自带 "In a cycle / Points upward" 过滤) 查看; 3D 城市图沿用官方默认 (面积 rloc, 高度与颜色 complexity).
- 后果: 撤销 D026 的 `height=level&area=rloc&color=violation` 交付组合, 也撤销 D019/D026 关于"建筑高度=层号"的目标; 交付文案要说明层号在哪里看. 不建议在 v1 阶段造自定义指标.

### U004 补 v1 实施节点 (父会话按用户"你看着办"决定)
- 状态: 当前有效
- 约束性: 可调整
- 内容: 目的地含"落地", 但原图只有汉化片 (milestone-21) 且缺 v1 服务本体, 故新增两个节点: milestone-25 准备 v1 的规格与执行输入 (HITL), milestone-26 实施 v1 (AFK, 按 drive-execution). 两者都阻塞终点验收; milestone-26 阻塞 milestone-25.
- 后果: v1 与汉化片仍按 D027 分两片, 汉化接入 v1 同一份数据与服务.

## 事实 (探针确认, 实施须遵守)

- **F001 rootless 容器写宿主目录必须 `--userns=keep-id`**: 默认映射下容器 uid 1000 映到宿主 100999, 对 bolo 目录无写权 (uid_map 实证, `../milestone-23/logs/uid-map-verify.log`).
- **F002 官方管道合并指标在本环境损坏**: `unifiedparser | dependencyparser` 报 MalformedJson 且指标未合入; 改用 `unifiedparser -o 文件` + `ccsh merge` 成功.
- **F003 零声明文件不进依赖树**: 全注释的 `*TestMapper` 与只有包声明的 `package-info` 解析后无可分析声明, 整体离开依赖树; `src/test` 与 `target/` 默认排除. 交付时须说明分母.
- **F004 层号字段位置**: `level` 在 `lenses.dependency.nodes`, 不在 metrics lens; 显式请求 `height=level` 会被前端静默改写为 `complexity`.
- **F005 宿主环境**: podman 5.7.0 rootless, 无 SELinux, Node v24.19.0, playwright chromium 可用; 分析可全程 `--network=none` 且源码只读挂载.
- **F006 官方前端可用**: vis-2.9.1 `web.zip` (sha256 `18b6377f...`) 原版即可吃探针产出的 cc.json 2.1 数据, 3D 与依赖视图均真实渲染, console 0 错误.

## 未采纳与边界

- 不采用"build 后把 level 复制进 metrics"的方案 (用户选择按官方).
- 不采用二维 cytoscape 方案, 不自算层号 (D005 仍然有效).
- 不因门禁项不可验证而减少任何已确认的验证要求; 该局限只进交付说明.
