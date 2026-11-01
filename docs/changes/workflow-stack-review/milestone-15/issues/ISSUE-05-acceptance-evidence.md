## 父级
- `../EXECUTION.md`

## 执行
- [x] 已完成

## 要核验什么
汇总本轮的完成证据, 并如实划出未验证范围:

- present 相关测试与修改过的 SKILL.md 格式检查: 每条检查留命令, 工具版本, 退出码与末行结果, 全过才记该项通过; 有一条失败就如实写失败命令与结果, 该项结论不是通过.
- 宿主环境真实局域网访问: 宿主侧按 SKILL.md 交付 URL 后, 由用户在同一网段另一台设备真实打开, 留下用户确认加能与本次请求对上的 `server.log` 请求行 (时间, 路径, 来源地址), 证据标明来自宿主环境.
- 容器环境真实局域网访问: 容器内 `start` 8800 后按 `SWT_HOST_LAN_IP` 加 8800 的宿主映射端口交付, 由用户设备真实打开, 留下同类证据, 标明来自容器环境; 缺映射端口或没有可用的容器环境时记未验证并列出未验证范围.
- 仓库边界 (BR-014 审计): 只改仓库内文件, 未运行会改安装目录的同步, 未改真实已安装 skills, 不声称安装效果或模型行为已验证.
- 隔离 (BR-015 审计复核): 测试与验证用独立运行时目录与端口, 未停止或接管真实展示实例.

对应 AC-007; BR-014 (审计), BR-015 (审计), BR-016 (审计); 非功能要求 两个环境的真实访问证据.

## 覆盖依据
- Product: `docs/changes/workflow-stack-review/milestone-15/PRODUCT.md`, AC-007; BR-014, BR-015, BR-016.
- Technical: `docs/changes/workflow-stack-review/milestone-15/TECHNICAL.md`, 非功能要求 (两个环境的真实访问证据, 页面自检), 接缝与依赖 (用户设备访问 属真正外部, 无法替身).

## 相关决策
- `docs/changes/workflow-stack-review/milestone-14/DECISIONS.md`: D012, D007, D010, F015.

## 代码定位提示
- 检查入口: `general/present/tests` (测试), `general/writing-for-llm/check_skill.py` (格式检查), `general/present/SKILL.md` (被检查文档).
- 地址与端口来源: 容器已确认宿主局域网地址 `192.168.65.165` 与环境变量 `SWT_HOST_LAN_IP`; 容器 8800 的宿主映射端口只来自 `SWT_HOST_WEB_PORT`; 宿主已确认地址来自 `~/.agents/sandbox-worktree/lan-address`. 本会话 `SWT_HOST_LAN_IP` 与 `SWT_HOST_WEB_PORT` 都不在环境里, 出生信息见 `~/docs/web-ports.md`.
- 访问证据来源: 运行时目录下的 `server.log` (`<系统临时目录>/pi-present-web-<uid>/server.log`); 不要在证据里贴出真实内网敏感路径或密钥.

## 验证入口
- `uv run python -m pytest general/present/tests`; 记退出码与末行, 以及 `uv run python -m pytest --version` 与 `uv run python --version`.
- `uv run python general/writing-for-llm/check_skill.py general/present/SKILL.md`; 记输出与退出码.
- 宿主证据: 在宿主侧按 SKILL.md 起服务, 交付 `http://192.168.65.165:<实际端口>/<页面>`, 请用户在同一网段另一台设备打开; 通过标准 用户确认看到页面内容, 且 `server.log` 里有与该次打开对得上的请求行 (时间, 路径, 来源地址); 证据注明 `宿主`.
- 容器证据: 先自查 (`env | grep SWT_HOST`, 容器识别, 8800 监听与记录), 仍缺映射端口时按 BR-003 经信箱向宿主会话 `01a18814-6e80-744f-a09f-346ba7b25522` 索取; 拿到后交付 `http://192.168.65.165:<映射端口>/<页面>` 并请用户设备打开; 通过标准 同上, 证据注明 `容器`; 映射或转发改写来源地址时, 用能对上本次展示请求的等价证据并写明口径.
- 两条证据不能互相代替: 只用容器本机 curl 或源码推断不得记通过; 缺哪个环境就在结论里写未验证并列出未验证范围.
- 仓库边界: `git status --short` 与 `git diff --stat` 只落 `../EXECUTION.md` 全局允许范围; 检查全程无 `sync-to-pi.py` 调用; `ls ~/.agents/skills/present` 与改前一致 (或如实记录其状态); 证据里不写安装效果或模型行为结论.
- 隔离复核: 验证前后 `pgrep -af "scripts/web_server.py"` 的 pid 集合与真实实例记录 mtime 对比不变; `workflow/navigate/` 无改动.

## 完成证据

## 完成证据

环境: 容器内 (本会话, `/run/.containerenv` 存在), Python 3.11.2, pytest 9.1.1. 原始输出 `/tmp/m15-05/`.

### 1. 自动化检查 (逐条: 命令 / 版本 / 退出码 / 结果)

| 检查 | 命令 | 版本 | 退出码 | 结果 |
| --- | --- | --- | --- | --- |
| present 测试 | `uv run python -m pytest general/present/tests` | Python 3.11.2 / pytest 9.1.1 | 0 | `99 passed, 4 skipped` (0 failed) |
| skill 格式 | `uv run python general/writing-for-llm/check_skill.py general/present/SKILL.md` | 同仓库脚本 (无独立版本号) | 0 | `general/present/SKILL.md: OK` |

改前基线 (ISSUE-03 记录): `143 tests collected`, 全量 `5 failed, 137 passed, 1 skipped` (5 条失败全在已删除的 `test_browser_session.py`). 现状 `103 tests collected`, 全量全绿; 4 条 skip 全是"宿主分支 CLI 用例 (容器内 `/run/.containerenv` 恒存在, 不可复现)", 不是伪通过.

条件回归: `_Handler` 类属性与静态内容服务行为未被改动 (`git diff a5a8ecf -- general/present/scripts/web_server.py | grep -E "^[+-].*(_Handler|_serve_static|_guard_control_namespace|_send_dir_listing)"` 无命中), 依据 TECHNICAL.md 接缝与依赖的跨 skill 依赖条, `uv run python -m pytest workflow/to-spec/tests/test_ac_draft.py` 免跑.

### 2. 宿主环境真实局域网访问证据: 未验证 (缺口)

本会话整体运行在容器内, 没有宿主 shell 与宿主网络视角, 不能在本会话执行宿主侧 `start` 并让用户设备打开页面. 需由宿主会话执行: 宿主侧用已确认局域网地址 `192.168.65.165` 加 49152-65534 内的实际监听端口起服务, 由用户在同一网段另一台设备打开 `http://192.168.65.165:<实际端口>/<页面文件名>`, 并留存 `server.log` 里与该次请求对得上的请求行 (时间, 路径, 来源地址). **本项记为未验证, 不用本机 curl 或源码推断顶替.**

### 3. 容器环境真实局域网访问证据: 未验证 (缺口)

容器自查 (按 BR-003 顺序, `/tmp/m15-05/container-selfcheck.txt`):

- 容器识别: `/run/.containerenv` 存在.
- `env | grep -E '^SWT_HOST'` -> 无任何 `SWT_HOST_*` 变量, 缺 `SWT_HOST_LAN_IP` 与 8800 对应的 `SWT_HOST_WEB_PORT`.
- 容器内 8800 已被既有真实 present 实例占用: `LISTEN 0 5 0.0.0.0:8800 users:(("python3",pid=14757))`, 运行时记录 `pid=14757, port=8800, bind=0.0.0.0, fixed_port=true`; 该实例属安装版 skill, 本轮不停止不接管.
- birth 生成的 `~/docs/web-ports.md` 只给已确认地址 `192.168.65.165`, 映射端口写明 "create 后才知, 从 env 读取".

自查仍缺映射端口. 按本任务约定未向 birth 注入的信箱地址投信 (同容器会话共用信箱), 故未取得 `SWT_HOST_WEB_PORT`. 因此**容器侧真实局域网访问记为未验证**, 未用容器 8800 或猜测端口拼 URL. 待办: 由协调方转交用户/宿主会话提供 8800 的宿主映射端口, 再用 `http://192.168.65.165:<映射端口>/<页面文件名>` 由用户设备打开取证.

### 4. 仓库边界 (BR-014 审计)

- `git status --short` 为空 (全部改动已提交); `git diff a5a8ecf --stat` 只落允许范围: `README.md`, `general/present/**`, 本目录 `issues/ISSUE-01..05` 的交付证据节. 未触碰 `workflow/`, 仓库根 `tests/`, `pytest.ini`, 真实安装目录, 其它 worktree.
- 未运行 `sync-to-pi.py` 或任何会改安装目录的同步 (本会话无该进程; `pgrep` 命中的只是我自己的 shell 命令行).
- `~/.agents/skills/present` 未被改动: 目录与文件 mtime 仍为 2026-10-27/2026-10-30 (本轮之前), 内容仍是旧版 `SKILL.md` + `REMOTE.md`.
- 本报告不声称安装效果或模型行为已验证.

### 5. 隔离复核 (BR-015 审计)

- 验证前后真实服务进程集合一致 (`/tmp/m15-04/pgrep-before.txt` vs `/tmp/m15-04/pgrep-after.txt`): 真实 present 实例 `pid 14757`, navigate 实例 `pid 117626` 均存活; 差异仅我自己的 `bash -c` 包装进程 pid.
- 真实运行时记录 `pid` 仍为 `14757`; 其 `server.log` 行数在整套 present 测试前后同为 `41` 行, 说明测试未经默认运行时目录打到真实实例 (期间 05:44:10/05:44:48 的日志行来自另一个并发会话, 不是本次验证).
- `workflow/navigate/` 无改动 (`git diff --stat -- workflow/navigate` 为空).

### 6. 结论

- 自动化检查项: 通过 (命令, 版本, 退出码, 结果见第 1 节).
- 宿主与容器两种环境的真实局域网访问: 均未验证, 原因是本会话只有容器视角且缺宿主映射端口; 不用一种环境代替另一种, 也不用本机请求或源码推断顶替.
## 风险提示
- 本会话缺 `SWT_HOST_WEB_PORT`, 容器证据可能拿不到; 只能记未验证, 不得用容器 8800 或猜测端口拼 URL 充当容器证据.
- 宿主场景需要先判断当前会话是否就是宿主; 若本会话只在容器内运行, 宿主场景由宿主会话执行, 本 issue 记"由宿主会话提供/待提供", 不自行改写成通过.
- 只有本机 curl 成功不构成 BR-016 要求的证据; 用户设备打开是对齐本次请求的关键, 没有它就写未验证.
- 映射或转发若改写来源地址, 日志里的来源可能不是用户设备真实 IP; 用路径与时间对上, 并写明口径, 不夸大成"已确认来源".

## 停止条件
需要改变任一 Spec, 决策或核验范围时停止; 需要挪动证据口径 (例如用非用户设备证据替代) 时先上报, 不自行放宽.

## 适合 AFK 的原因
不适合 AFK: 需要用户在同一网段另一台设备真实打开页面并确认, 还需要宿主会话提供容器 8800 的映射端口. 测试与格式检查部分可自行完成.

## 验收标准
- [ ] present 相关测试与 `check_skill.py` 的命令, 版本, 退出码与结果逐条列出, 且全部通过.
- [ ] 宿主环境有一条用户设备真实访问证据, 能与 `server.log` 里的请求行对上, 并标明来自宿主.
- [ ] 容器环境有一条同类真实访问证据并标明来自容器, 或明确记为未验证并列出范围.
- [ ] 结论里不用一种环境的证据代替另一种, 不用本机 curl 或源码推断顶替.
- [ ] `git status --short` 只落允许范围, 无同步调用, 未改真实已安装 skills, 无安装效果或模型行为声明.
- [ ] 验证前后真实展示实例未被停止或接管, `workflow/navigate/` 无改动.

## 被阻塞于
- ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04.
