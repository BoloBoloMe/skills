## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已完成
- [ ] 派工前复核并记录 (写在本行下方): HEAD 提交号; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数; `workflow/codebase-map/` 当前存在哪些文件.

## 要核验什么
只核验, 不改成品. 核验容器内拿不到的那部分结果 (m25 D016 的宿主清单), 以及三条审计断言:

- 真实 Java 目标库的 `build`: 首次初始化 (`initialization.performed` 为真且 `notice` 存在), 三次 `podman run` 成功, 门禁通过, 统计与分母输出完整, 目标库出现 `.codebase-map/cc.json`, 记录的耗时.
- 目标库只读: 真实库是 git 仓库, build 后工作区只多 `.codebase-map/cc.json`.
- 真实镜像核对: `podman image inspect` 的 `RepoDigests` 含单架构清单 digest `sha256:286b0a54...`, 多架构值只出现在 `cache/cache.json`.
- 真实渲染: 局域网设备打开交付 URL 看到本次分析的 3D 城市图 (标题为库名, 不是官方示例数据), 官方依赖视图给出层号并默认只显示环与向上依赖, 3D 图指标为官方默认 (面积 rloc, 高度与颜色 complexity), 交付 URL 不带改指标选择的参数, 界面为官方英文原版且版本显示 `vis-2.9.1`.
- 真实局域网可达: 交付 URL 由已确认地址加实际端口拼成, 用户设备能打开 (m25 D007: 用户设备真实请求才算通过).
- AC-007 的宿主场景: 目标目录不存在; 没有 podman (PATH 收窄构造); 取不到官方前端 (清缓存且断网构造).
- AC-005 的副本失效场景: 手工改坏 `serve-root` 里的副本后重新 build, 页面显示的是原件数据.
- AC-004 的复原场景: 删掉 `~/.agents/codebase-map/` 后按 SKILL.md 复原, 得到能打开图的 URL, 且输出说明是重新起的实例.
- 长期常驻: 跨较长真实时间与多次命令调用后, 同一 URL 仍可用, 且 `serve` 复用同一实例.
- 三条审计断言的人工核验: BR-033 (仓库无第三方依赖清单, 脚本 import 全是标准库), BR-035 (仓库内无 `.cc.json`, 无前端产物, 无被分析库完整路径), BR-026 (验收目标库是一个真实 Java 库, 由用户指定).

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-25/PRODUCT.md`, AC-001, AC-002, AC-005, AC-006, AC-007 (宿主三条场景与目标库只读), AC-008 (真实地址与设备可达), AC-009 (英文原版与版本显示); BR-005, BR-009, BR-016, BR-017, BR-021, BR-022, BR-023, BR-024, BR-025, BR-026, BR-027, BR-028, BR-029, BR-031, BR-033 (审计), BR-035 (审计).
- Technical: `docs/changes/workflow-stack-review/milestone-25/TECHNICAL.md`, 接缝与依赖 (进程接缝与用户设备访问为真正外部, 无法替身), 非功能要求 (常驻性, 观察代价, 验证分工), 安全策略 (数据与隐私).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-25/DECISIONS.md`: D007, D010, D016, F004, F005, F006.
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D007, D012.
- `docs/changes/workflow-stack-review/milestone-24/DECISIONS.md`: U001, U003.

## 代码定位提示
- 真实入口: `python3 workflow/codebase-map/scripts/codebase-map.py build <目标库> --json` / `serve` / `stop` (宿主), 文档在 `workflow/codebase-map/SKILL.md`.
- 运行时数据: `~/.agents/codebase-map/` (`state.json`, `serve-root/`, `cache/cache.json`, `cache/work/`, `logs/`).
- 已确认地址: `~/.agents/sandbox-worktree/lan-address`.
- 证据脱敏纪律: 仓库内只写清洗后的库名与路径哈希; 原始日志, 截图, 完整路径一律放仓库外 `/tmp/m25-07/` (本节点) 与 `/tmp/m26-07/` (实施节点), 不入 git.
- 量级参照 (只记录不判定): `docs/changes/workflow-stack-review/milestone-23/PROBE.md` 6.2 的单库单步约 26 秒, 6.4 的分母算法与零声明定性.

## 验证入口
宿主上按顺序执行, 每条都要记命令, 环境, 输入, 预期, 实际与可复查材料位置. 缺环境的条目记未验证并写明缺什么, 不用替身顶替.

1. 环境与版本: `podman --version`, `python3 --version`, `uv --version`; 通过标准 与 m25 F001/F004 一致 (python3 3.14.x, uv 0.12.x, podman rootless 可用).
2. 镜像核对: `podman image inspect docker.io/codecharta/codecharta-analysis:2.3.0 --format '{{json .RepoDigests}}'`; 通过标准 含 `sha256:286b0a54f947c412b7c290a57312ac2c4327352531e046ad4ab834c13b2ddc36`; 多架构值只出现在 `cache/cache.json`.
3. 首次 build (目标库 = 用户指定的真实 Java 库): 先记录目标库 `git status --porcelain` 与 HEAD; 跑 `build <目标库> --json`; 通过标准 退出码 0, `initialization.performed == true` 且 `notice` 说明拉镜像与取前端属慢操作, `gate.passed == true`, `.codebase-map/cc.json` 出现, `stats` 各分量完整, `duration_seconds` 被记录.
4. 目标库只读: 再跑一次 `git status --porcelain`; 通过标准 只多 `.codebase-map/cc.json` (若该库 `.gitignore` 忽略它, 记为 0 变更并写明), 其它文件与改动状态不变.
5. 门禁统计与分母: 从 `build --json` 抄下依赖边数, 文件层号种数, 依赖树文件数, 扫描文件数, 零声明清单, 未支持扩展名清单; 通过标准 边数 > 0, 层号种数 >= 3, 五个 `excluded` 类与零声明之和能与扫描文件数逐类归因; 与 m23 的量级对照只记录.
6. serve 与真实交付: `serve --json`; 通过标准 有 `url` 与每个键的完整 URL, `delivery_notes` 三类说明齐全, 端口与 `state.json.port` 一致.
7. 用户设备真实打开 (需要用户在场): 3D 城市图渲染出本次数据且标题为库名; 切到官方依赖视图能看到层号与环/向上依赖边; 指标为官方默认 (面积 rloc, 高度与颜色 complexity) 且交付 URL 无改指标参数; 界面为英文原版且版本显示 `vis-2.9.1`; 通过标准 逐条由用户确认, 并留对得上的访问记录 (时间, URL, 页面状态). 本机 curl 与截图只能辅助.
8. AC-007 宿主场景三条: (a) `build /不存在的目录` -> `target_missing`; (b) 断网并清空 `cache/frontend/` 后 `build` -> 前端取不到即停, 报错含"取不到官方前端产物"; (c) `env PATH=/nonexistent /usr/bin/python3 <skill>/scripts/codebase-map.py build <目标库>` -> `podman_missing`. 通过标准 三条都以非 0 退出且不产出替代数据; (b) 执行前先把既有前端缓存整体复制到 `/tmp/m25-07/cache-backup/` 保留, 不直接删掉原数据.
9. AC-005 副本失效: 备份并改坏 `serve-root` 里某一份副本, 重新 `build` 该库, 刷新页面; 通过标准 页面显示原件数据, 被改坏的副本不再生效; 原始被改坏文件保留在备份目录.
10. AC-004 复原: 记录当前 `state.json` 与 `serve-root` 内容 -> 把 `~/.agents/codebase-map/` 整目录移到 `/tmp/m25-07/runtime-backup/` (不删除) -> 按 SKILL.md 复原步骤重新 `build` 再 `serve`; 通过标准 得到能打开图的局域网 URL, 输出说明这是重新起的实例.
11. 长期常驻: 在多次 `serve` 调用与一段真实等待之后再次打开 URL; 通过标准 页面仍可用, `serve` 复用同一 `pid`.
12. 审计核验: `git ls-files | grep -Ei '\.cc\.json|web\.zip|vis-2\.9\.1|package-lock\.json|pyproject\.toml'` (在 `workflow/codebase-map/` 范围内) 应为空; 逐个看 `workflow/codebase-map/scripts/*.py` 的 import 全是标准库; 检查 `SKILL.md` frontmatter 与 `agents/openai.yaml`; 全仓库检索没有任何 skill 调用 `codebase-map`. 通过标准 BR-033/BR-034/BR-035 三条都成立.
13. 全量回归 (宿主): `uv run python -m pytest`; 通过标准 退出码 0. 容器内跑不了这一条 (无 podman), 属环境缺口, 不得伪记通过.
14. 观察代价: 只记录首次初始化耗时与单库 build 耗时, 与 m23 的 26 秒量级对照, 不设阈值, 不下性能结论.

## 完成证据
执行后填写: 每条的宿主命令与脱敏输出, 设备访问记录 (时间, URL, 用户确认结论), 真实统计数值, 备份目录位置与占用, 未验证项及缺什么. 仓库内只写清洗后的库名与路径哈希.

## 风险提示
- 第 8(b) 与第 10 条要动既有缓存与运行时目录, 必须先整体备份到 `/tmp/m25-07/` 再动手, 不直接 `rm`; 备份未成功就停下.
- 局域网设备访问需要用户配合, 代理不在场时该条只能记未验证; 用本机 curl 或截图顶替会被判伪造.
- 真实库的日志与截图含私有文件名与路径, 一律不入仓库 (m25 D010); 入仓库的只有清洗后库名, 路径哈希与数值.

## 停止条件
需要改变任一 Spec, 决策或核验范围时停止; 用户未指定真实 Java 库时停在第 3 条并记未验证; 备份失败或动到非本工具的数据时停止.

## 适合 AFK 的原因
大部分条目是跑现成命令与采集数值, 不需要产品/API/架构决策. 不适合 AFK 的只有第 7 条 (局域网设备真实打开) 与第 3 条的前置 (用户指定真实 Java 库): 前者必须用户在自己设备上确认, 后者需要用户给目标库, 缺其中任一项就记未验证而不是自选目标.

## 验收标准
- [ ] 真实 Java 库 build 通过门禁, 统计与分母完整, 原件落在目标库.
- [ ] 目标库除 `.codebase-map/cc.json` 外未被改动.
- [ ] 用户设备真实打开看到本次数据的 3D 图与依赖视图, 指标与 URL 参数为官方默认, 界面为英文原版 vis-2.9.1.
- [ ] 交付 URL 用已确认局域网地址加实际端口, 设备可打开.
- [ ] 三类环境缺口与两类退化场景都在宿主复现并如实报错.
- [ ] 删运行时目录与改坏副本两条复原路径按文档走通.
- [ ] 长期常驻后仍复用同一实例.
- [ ] 三条审计断言 (BR-033, BR-034, BR-035) 人工核验成立.
- [ ] 全量 pytest 在宿主通过; 容器内跑不了的项已明确记未验证.

## 被阻塞于
- `ISSUE-01-shared-rules-and-cli-contract.md`
- `ISSUE-02-first-init-and-analysis-output.md`
- `ISSUE-03-gate-stats-and-serve-copies.md`
- `ISSUE-04-resident-service-and-state.md`
- `ISSUE-05-delivery-output-and-address.md`
- `ISSUE-06-skill-docs-and-metadata.md`
