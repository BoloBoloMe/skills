# 独立验收派工计划 (round 1)

- 时间: 2026-10-19T22:25+08:00
- 目标提交: cd087542b4610c49ded0a1278fe8065726b62d9d (HEAD), 上一提交 8438934fc81b67ed518dc4ad2e2f7dbd83b0192a
- 判据来源: docs/changes/relay-board/PRODUCT.md (验收标准 confirmed-flow v1)
- 版本前提: 目标提交存在; `git status --porcelain --untracked-files=all` 为空 (无已跟踪改动, 无未跟踪产品文件); runtime/ 与 .agents/ 为 gitignore 目录.

## 必验清单 (5 项)

| 编号 | 类型 | 判据摘要 |
| --- | --- | --- |
| AC-001-1 | 场景 | 浏览器渲染 /status-page 并截图, 截图显示 instance=alpha, state=ready, version=relay-v1 |
| AC-002-1 | 场景 | `python3 app.py job --port 18101 --ms 2500` 输出 `job-done instance=alpha elapsed_ms=2500`, 退出码 0 |
| AC-003-1 | 场景 | `python3 app.py report --port 18101` 输出 `relay-report instance=alpha version=relay-v1 state=ready`, 退出码 0 |
| AC-004-1 | 场景 | `python3 app.py log --port 18101` 输出含 `instance=alpha` 与 `event=job-end`, 退出码 0 |
| BR-001 | 审计 (静态) | 本次变更不新增第三方依赖, deps.txt 与上一提交逐项一致 |

## 证据目录影响判断

- 目录: `docs/changes/relay-board/evidence/v1-cd08754/` (本轮新增, 不覆盖旧证据; 旧证据不存在).
- 只写 .md/.log/.txt/.png 等验收输出, 不写 .py 测试文件.
- 项目无 pytest.ini/tox.ini/setup.cfg/pyproject.toml/conftest.py; README 的 pytest 命令只发现 test_*.py, 不读取 docs/.
- 服务与测试运行输入只有 runtime/ (gitignore), 不读 docs/.
- 结论: 写入该目录不进入构建, 测试发现或运行输入, 可留在仓库内; 证据目录新增是本轮相对起始提交的唯一预期变化.

## 分组与人数

当轮可用非作者验收者 2 名; 计划 2 名.

### 组 1: 运行场景 (承接 AC-001-1, AC-002-1, AC-003-1, AC-004-1)

- 验收者: `i04-a1-ac` (新会话).
- 资源: 唯一实例 alpha, 端口 18101, `runtime/alpha`, `runtime/shared`; google-chrome headless 截图.
- 共用准备: 由本组自己启动实例并 health, 只启动一次; 只有本组需要该实例, 无跨组共用.
- 顺序: AC-002 的 job 完成后才能做 AC-004 (AC-004 假定耗时任务已执行); 其余场景同一实例顺序执行.
- 不拆理由: 四条场景争用同一实例/端口/数据目录; 禁止为并行加实例或扩端口; 单个场景不值得单开会话.
- 原始材料归属: 本组自己产生的命令输出, 截图, runtime 日志; 全部由 `i04-a1-ac` 负责.

### 组 2: 静态依赖审计 (承接 BR-001)

- 验收者: `i04-a1-br` (新会话).
- 资源: 只读 git 历史与工作区文件; 不占用实例, 端口与 runtime/.
- 并行: 与组 1 完全隔离, 无共用准备, 可同时开工.
- 原始材料归属: 比对命令与原始输出由 `i04-a1-br` 负责; 结论标注为静态材料核对结果.

### 争用与先后

- 组 1 内 AC-002 (写 shared/events.log) 先于 AC-004 (只读同一日志), 执行者 `i04-a1-ac`, 依据 AC-004 的"假定耗时任务已经执行".
- 组 2 与组 1 无共用资源, 无先后约束.
- 不为制造并行新增实例, 端口或写入授权.

### 并行收益

- 组 2 无需任何共用准备, 与组 1 同时执行, 直接节省等待时间; 同时让 BR-001 由未参与实现的会话独立核对, 避免只取实现方自证.
- 组 1 内部不可再分, 故不再开第三个会话.

## 交付物

- 组 1: `evidence/v1-cd08754/runtime-AC/REPORT.md` + 原始输出/截图.
- 组 2: `evidence/v1-cd08754/audit-BR-001/REPORT.md` + 原始输出.
- 指挥者: 本计划 + `evidence/v1-cd08754/VERIFY-REPORT.md` (汇总).
