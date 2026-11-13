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

### 3. 容器环境真实局域网访问证据: 已取得 (用户设备打开)

容器自查 (按 BR-003 顺序, `/tmp/m15-05/container-selfcheck.txt`):

- 容器识别: `/run/.containerenv` 存在.
- `env | grep -E '^SWT_HOST'` -> 无任何 `SWT_HOST_*` 变量, 缺 `SWT_HOST_LAN_IP` 与 8800 对应的 `SWT_HOST_WEB_PORT`.
- 容器内 8800 已被既有真实 present 实例占用: `LISTEN 0 5 0.0.0.0:8800 users:(("python3",pid=14757))`, 运行时记录 `pid=14757, port=8800, bind=0.0.0.0, fixed_port=true`; 该实例属安装版 skill, 本轮不停止不接管.
- birth 生成的 `~/docs/web-ports.md` 只给已确认地址 `192.168.65.165`, 映射端口写明 "create 后才知, 从 env 读取".

自查仍缺映射端口. 按本任务约定未向 birth 注入的信箱地址投信 (同容器会话共用信箱), 故未取得 `SWT_HOST_WEB_PORT`.

后续 (协调方已从宿主取得映射): 容器 8800 -> 41141, 8801 -> 34403, 8802 -> 33671, 8803 -> 36951, 8804 -> 33529, 8805 -> 36703; 其中 8800-8804 已被既有实例占用 (8800 是既有真实 present 实例 pid 14757), 只有 8805 空闲. 协调方授权用 8805 起本人实现的服务取证:

- 页面: `/tmp/m15-05/report/2026-11-01-m15-container-proof.html` (自造, 自检 `success: true`), 标记串 `M15-CONTAINER-PROOF-581e16ff55080425`, 页面内时间 `2026-11-01T05:57:39Z`.
- 服务: 独立运行时目录 `PI_PRESENT_WEB_RUNTIME_DIR=/tmp/m15-05/rt`, `start 8805 /tmp/m15-05/report --bind 0.0.0.0 --fixed-port`, CLI 按容器规则用 `SWT_HOST_LAN_IP=192.168.65.165` + `SWT_HOST_WEB_PORT=36703` 拼出交付 URL `http://192.168.65.165:36703/`; 记录 `server.json` 的 `port` 仍是 8805 (`pid 197610`), 未把 36703 写进记录.
- 容器内自测 (只走 `127.0.0.1:8805`, 未访问 `192.168.65.165`): 页面 200 且标记串一致; `server.log` 有请求行 `2026-11-01T05:57:45.645375+00:00 127.0.0.1 - "GET /2026-11-01-m15-container-proof.html HTTP/1.1" 200`.
- 协调方已用 `127.0.0.1:8805` 复核一次: HTTP 200 且页面含标记串 `M15-CONTAINER-PROOF-581e16ff55080425`; 日志里 `2026-11-01T05:58:05.887617+00:00 127.0.0.1 - "GET /2026-11-01-m15-container-proof.html HTTP/1.1" 200` 就是这次复核, **不是用户设备访问**, 不计入 BR-016 要求的证据.
- 用户设备真实打开 (协调方转述用户原话): 用 `http://192.168.65.165:36703/2026-11-01-m15-container-proof.html` 打开成功, 页面标题 "milestone-15: 容器侧展示服务取证页", 正文说明了服务监听容器 8805 与宿主映射端口, 标记串显示为 `M15-CONTAINER-PROOF-581e16ff55080425`, 生成时间 `2026-11-01T05:57:39Z`, 用户没有报错.
- 对上的日志行 (唯一一条 127.0.0.1 之外、且与我的自测和协调方复核不同的记录):
  `2026-11-01T05:58:52.261070+00:00 192.168.216.71 - "GET /2026-11-01-m15-container-proof.html HTTP/1.1" 200 -`, 同一来源紧随 `GET /favicon.ico` 404 (浏览器行为, curl 不会如此).
  原始日志留档: `/tmp/m15-05/final-server.log`.
- 限制 (如实写明, 不夸大):
  1. **时间取自服务日志, 用户未报精确时刻**; 用户侧只确认"打开成功, 内容如上".
  2. 来源地址显示 `192.168.216.71`, 属宿主/转发侧地址, **经转发改写无法据此确定用户设备的真实 IP**, 也不推断这条来源是容器内还是宿主转发, 故只作"该次请求与用户所述页面内容、标记串、时间窗一致"的证据.
  3. 该证据来自协调方转述 (用户原话), 不是本会话直接观察到的用户侧画面.
- 取证环境收尾: 已 `stop` 本次 8805 实例 (`{"success": true, "command": "stop"}`), `pgrep -af "__serve__ 8805"` 无服务进程, `ss -ltn` 无 8805 监听, 运行时目录只剩 `server.log` (`server.json` 已删); 8800 上既有真实 present 实例 `pid 14757` 未动 (`/tmp/m15-05/stop-proof.txt`).

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
- 容器环境真实局域网访问 (用户设备打开): 已取得, 见第 3 节 (含时间取自日志、来源地址被改写的限制).
- 宿主环境真实局域网访问: **未验证** (缺口), 见第 2 节; 本会话只有容器视角, 不能执行宿主侧 `start`, 也不拿容器证据代替.
- 不用一种环境的证据代替另一种, 不用本机 curl 或源码推断顶替.

### 7. 最终结论摘要 (供关闭本节点)

| ISSUE | 结论 | 已验证 | 未验证/缺口 |
| --- | --- | --- | --- |
| ISSUE-01 地址解析与交付 URL | 通过 (带缺口) | 显式地址优先/已确认记录/缺口与候选/容器映射/loopback 分支/SSH 变量不改变地址 (显式入参与 CLI 用例); `pytest general/present/tests` 全绿 | 宿主分支 CLI 端到端未在容器实跑 (4 条 skip); 真实容器映射端口访问由 ISSUE-05 承接 |
| ISSUE-02 端口记录与重建一致性 | 通过 (带缺口) | 复用取实际端口; 重建换口后记录/`status`/`url`/真实监听四处一致; 容器记录写监听端口不写映射端口; 既有 fixed_port/content 用例复跑通过 | 容器 8800 字面被占的 `port_in_use` 未实测 (该端口被既有实例占用, 不能停) |
| ISSUE-03 单流程文档 | 通过 | `SKILL.md` 唯一流程, `REMOTE.md`/`browser_session.py`/两份测试已删, 取消状态对象强制, 文本契约与 `check_skill.py` 通过, 人工按文档走查自检与失败出口 | 宿主侧 agent 实际遵从文档的行为未验证 (属模型行为, 不在本节点范围) |
| ISSUE-04 安全与常驻性 | 通过 | 闲置存活/stop/内容面/控制面用例复跑通过; 真实 stop 两页均不可访问; LAN 来源控制面 403; `../` 越界 404; loopback ping 200 且 pid 一致; 真实实例未被触碰 | 从未做 24 小时等待 (只用既有 1 秒闲置用例承接) |
| ISSUE-05 验收证据 | 部分通过 | 自动化检查全部通过; 容器侧用户设备证据已取得 (附限制) | 宿主侧真实局域网访问未验证 (缺口) |

- 可关闭性判断: 代码/文档/自动化检查全部通过, 容器侧真实设备证据已取得; **唯一未验证项是宿主环境真实局域网访问**, 需在宿主上起服务后由用户设备打开取证, 本会话无此环境, 不用容器证据顶替.
- 与 D012/BR-016 的关系: 两种环境分别出证的要求未完全满足 (宿主侧缺), 按标准该细分项记未验证, 不写通过.
- 用户裁决 (2026-11-01, 经协调方转述): 宿主侧真实局域网访问记为未验证缺口, **不阻塞本节点关闭**, 留到终点验收 (milestone-08) 再核. 本节点不为此去动宿主环境, 也不因此改写已完成项的结论.
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
- [x] present 相关测试与 `check_skill.py` 的命令, 版本, 退出码与结果逐条列出, 且全部通过.
- [ ] 宿主环境有一条用户设备真实访问证据, 能与 `server.log` 里的请求行对上, 并标明来自宿主. (未勾: 宿主环境真实局域网访问未验证, 见 完成证据 第 2 节)
- [x] 容器环境有一条同类真实访问证据并标明来自容器, 或明确记为未验证并列出范围.
- [x] 结论里不用一种环境的证据代替另一种, 不用本机 curl 或源码推断顶替.
- [x] `git status --short` 只落允许范围, 无同步调用, 未改真实已安装 skills, 无安装效果或模型行为声明.
- [x] 验证前后真实展示实例未被停止或接管, `workflow/navigate/` 无改动.

## 被阻塞于
- ISSUE-01, ISSUE-02, ISSUE-03, ISSUE-04.
