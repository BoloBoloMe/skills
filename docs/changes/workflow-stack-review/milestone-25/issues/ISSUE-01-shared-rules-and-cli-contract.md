## 父级
- `../EXECUTION.md`

## 执行
- [ ] 已完成
- [ ] 派工前复核并记录 (写在本行下方): HEAD 提交号; `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数; `workflow/codebase-map/` 当前存在哪些文件.
  - HEAD: `2bc146d3cadb3f9fafb4cb3cf28e7823c8ae33b7`, 与派工基点 `2bc146d` 一致.
  - 收集条数: 865, 与 EXECUTION.md 评审起点基线一致 (原始记录 `/tmp/m26-01/collect-baseline.txt`).
  - `workflow/codebase-map/` 现存: `README.md`, `SKILL.md`, `agents/openai.yaml`, `i18n/` (三份词表), `tools/` (六个 py 加 `build-zh.sh`); 来自已合并的 milestone-21 (merge `f2ca80d`, 早于本 spec 全部提交). 与 EXECUTION.md 评审起点 "目录不存在, 全部从零新建" 及 m25 F007 冲突; `scripts/` 与 `tests/` 确不存在, 本 issue 落点无碰撞. 按停止条件停手上报, 未实施.

## 要交付什么
新建 skill 的骨架与共享规则, 让 CLI 第一次能从真实入口跑起来:

- `workflow/codebase-map/scripts/codemap_common.py`: 数据键计算 `data_key(target_dir)`; 运行时目录解析 (`CODEMAP_RUNTIME_DIR` 覆盖, 默认 `~/.agents/codebase-map`, 子目录 `serve-root/`, `cache/`, `logs/`); 默认排除集合 (`node_modules`, `.git`, `dist`, `build`, `target`, `vendor`, `.codebase-map`) 与 `--exclude <glob>` 追加, 以及同一份数据转成 ccsh `-e` 正则的转换函数 (元字符逐字转义); 版本常量 (镜像 tag `docker.io/codecharta/codecharta-analysis:2.3.0`, 单架构清单 digest `sha256:286b0a54...`, 多架构清单 digest `sha256:6402a87f...`, 前端 `vis-2.9.1` 的 `web.zip` sha256 `18b6377f...`, 默认端口 8090, 绑定 `0.0.0.0`); 人类可读摘要与单行 JSON 两种输出编码的共用辅助.
- `workflow/codebase-map/scripts/codebase-map.py`: 三子命令的参数解析骨架与错误信封. 本 issue 只注册 `build`: 前置检查 (容器内 -> `container_not_supported`; 目标目录不存在 -> `target_missing`; 没有 podman -> `podman_missing`), `--json` 时 stdout 只有一行 JSON, 默认输出多行人类可读摘要, 失败退出码 1, 成功 0, 每个失败都有稳定错误码且非 JSON 模式在 stderr 说清下一步动作. `serve` 与 `stop` 由 ISSUE-04/ISSUE-05 注册, 本 issue 不建占位分支, 不写会静默成功的空实现.
- `workflow/codebase-map/tests/`: 新测试树. 只放唯一定名的 helper 模块 (先例 `workflow/navigate/tests/nav_helpers.py`), 不加 `conftest.py`, 禁止 `from conftest import`.
- `pytest.ini`: `testpaths` 在 `tests` 之前追加 `workflow/codebase-map/tests`, 其余行不动.

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-25/PRODUCT.md`, AC-007 (沙箱容器里调用被拒绝这条场景); BR-011, BR-013 (子命令形状), BR-015 (排除集语义与两处同源), BR-021 (环境不足报错停下), BR-032, BR-033 (审计); G-001, NG-003, NG-008.
- Technical: `docs/changes/workflow-stack-review/milestone-25/TECHNICAL.md`, 模块划分 (`codemap_common.py`, `codebase-map.py`), 模块接口 (CLI 前置/错误码/数据键不变式/排除集合/版本常量/运行时目录), 接缝与依赖 (内部接缝), 非功能要求 (可诊断).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-25/DECISIONS.md`: D005, D012, D014, D016, D019, F007, F008.
- `docs/changes/workflow-stack-review/milestone-13/DECISIONS.md`: D003, D009, D017.

## 允许范围
同全局, 增量: 本 issue 只落 `codemap_common.py` 与 `codebase-map.py` 的 `build` 骨架, 新测试树的首批用例, `pytest.ini` 一行.

## 禁止范围
- 不实现分析流水线与服务 (`codemap_analyze.py`, `codemap_service.py` 留给 ISSUE-02 至 ISSUE-05), 不写返回假成功的占位实现.
- 不新增配置源: 不建 config 文件, 不读 `SSH_CONNECTION`, 不读环境变量来做地址判定 (地址只走 `--address` 与 `~/.agents/sandbox-worktree/lan-address`, 见 ISSUE-05).
- 不引第三方依赖, 不建 venv, 不在 `scripts/` 里 import 仓库内其它 skill 的代码.
- 不改 `tests/` 与另外两棵测试树, 不动 `pytest.ini` 既有行与 markers 段.

## 代码定位提示
从零新建, 无入口可抄, 参照这些既有形状:
- 子命令与参数解析: `workflow/navigate/scripts/roadmap.py` 的 `main()` 与 argparse 子命令段.
- 运行时目录, 摘要输出, 端口与 bind: `workflow/navigate/scripts/web_server.py` (运行目录解析与摘要输出, 行 96-99 的 `flock` 用法, 行 502 的 `ThreadingHTTPServer`).
- 静态守卫写法: `workflow/navigate/tests/test_stdlib_only_and_no_external_refs.py`.
- 测试 helper 的唯一定名先例与 `conftest` 陷阱说明: `workflow/navigate/tests/nav_helpers.py`, `workflow/navigate/tests/conftest.py`, `pytest.ini` 文件头注释.
- 键命名与清洗的期望样例: PRODUCT AC-005 的 `Demo App` -> `Demo-App-<8 位十六进制>.cc.json`.

## 验证契约
- 变更类型: 行为变更 (新增对外 CLI 契约与错误码) 加 非行为改动 (`pytest.ini` 接线, 无外部行为变化).
- 对应范围: CLI 前置检查与错误信封; 共享纯函数 (键, 排除集, 版本常量, 运行时目录); 测试接线.
- 验证要求/证据: 逐条验证 AC-007 的容器内场景与 BR-011/BR-032/BR-015/BR-021 的口径; 证据为 pytest 输出加真实 CLI 调用的 stdout/stderr 摘录 (放 `/tmp/m25-01/`, 脱敏), 以及 `pytest.ini` 改动前后的收集条数差.

## 验证入口
- `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest workflow/codebase-map/tests`; 通过标准 退出码 0 且无 failed. 新增用例:
  - TC-007 (AC-007 主用例): 在容器内从真实入口跑 `python3 workflow/codebase-map/scripts/codebase-map.py build <临时目标目录> --json`, 断言 `success: false`, `error.code == "container_not_supported"`, 退出码非 0, 且不产出任何数据文件.
  - TC-01-01: 键命名与清洗 (空格换成 `-`, 非法字符逐个换, 连续 `-` 折叠, 首尾 `-` 去掉, 空 -> `repo`; 同一 realpath 恒同键, 不同 realpath 不同键; 键只含 `[A-Za-z0-9._-]`; 哈希取 realpath 字节的 sha256 前 8 位).
  - TC-01-02: 运行时目录解析 (`CODEMAP_RUNTIME_DIR` 覆盖生效, 默认值为 `~/.agents/codebase-map`, 三个子目录按需创建).
  - TC-01-03: 默认排除集与 `--exclude` 追加后转成的 ccsh `-e` 正则, 逐条核对元字符被转义, 且同一份集合喂给分析侧与扫描侧.
  - TC-01-04: 版本常量与题目给定值逐字一致 (tag, 两个 digest, 前端版本与 sha256, 端口 8090, bind `0.0.0.0`).
  - TC-01-05: 静态守卫, `workflow/codebase-map/scripts/*.py` 只 import 标准库 (按 import 行解析, 不执行).
  - TC-01-06: CLI 输出形状与可诊断性, `--json` 时 stdout 恰好一行可解析 JSON 且字段含 `success`/`command`/`error`; 非 JSON 模式失败时 stderr 有下一步动作, 退出码 1.
- 收集基线核对: `PYTEST_XDIST_WORKER=gw0 uv run python -m pytest --collect-only -q` 条数 = 865 加本 issue 新增用例数, 记下实际数.
- 不在本 issue 验证: `target_missing`/`podman_missing` 在容器内被 `container_not_supported` 挡在前面, 只能宿主构造 (ISSUE-07), 本 issue 不用 stub 或注入伪造这两条.

## 交付证据

## 风险提示
- `pytest.ini` 的 testpaths 顺序承担 conftest 预载职责, 新树若引入 `conftest.py` 或 `from conftest import`, 会让别的树拿到错对象; 只用唯一定名 helper.
- 键用 realpath 而非 `abspath`: 软链进同一目录必须得到同一键, 测试要覆盖.

## 停止条件
需要改变任一 Spec, 决策, issue 边界或扩大范围时停止; 需要新增环境变量或配置源时停止并上报 (现有 `CODEMAP_RUNTIME_DIR`/`CODEMAP_PORT` 之外一律不加).

## 验收标准
- [ ] 容器内执行 `build` 被拒并给出 `container_not_supported`, 不产出数据.
- [ ] 数据键与清洗口径与 BR-011/BR-032 逐字一致, 同目录恒同键.
- [ ] `--json` 单行且字段稳定, 失败有错误码, 退出码 0/1 分明.
- [ ] `scripts/` 下脚本只 import 标准库 (静态守卫通过).
- [ ] `workflow/codebase-map/tests` 已进 `testpaths` 且排在 `tests` 之前, 收集条数增量对得上.

## 被阻塞于
- 无
