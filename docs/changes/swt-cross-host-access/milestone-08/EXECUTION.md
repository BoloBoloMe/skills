# MILESTONE-08 窗口直飞实施 EXECUTION

任务书: [MILESTONE-08.md](../roadmap/MILESTONE-08.md). 权威输入: [M06 决策账本](../milestone-06/DECISIONS.md) (D001-D008/F001-F008), ADR [0013](../../../adr/0013-waypipe-trigger-via-mailbox-zero-param-exec.md), [M07 实测结论与新事实 N1-N6](../roadmap/MILESTONE-07.md), [词汇表](../../../language/UBIQUITOUS_LANGUAGE.md), [UNAUTHORIZED_DECISIONS.md](UNAUTHORIZED_DECISIONS.md) (UD-01 起).

工作模式: AFK 自主推进 (probe task 类型, 设计已经 M06 与用户闭环, 实测已经 M07 真机; EXECUTION 为总指挥自拟, 见 UD-01), 自主决定逐条落 UNAUTHORIZED_DECISIONS.md.

## 全局约束

- D005: STATE 单行 json 不加任何远程显示字段; 容器内文件/socket 事实是唯一事实源.
- N1: 启动脚本内部设 env (export), 交付包/配方命令模板禁止 `VAR=... cmd` 赋值前缀.
- N5/N6: 容器 uid=1001, apt waypipe 0.8.4; 设备侧 waypipe 版本用户自管 (M07 实测 0.11 Rust 透传 -R).
- 服务端/swt 零新增第三方依赖, Python 标准库; relay 扩展零新增 npm 依赖.
- swt 测试沿用 test_swt_birth_mailbox.py 约定: importlib 加载 swt.py, fake `run` 替换 podman 边界, tmpdir 当 records_root, 不依赖 podman. 服务端测试沿用 test_swt_base_server_mailbox.py 约定 (Mailbox 直例, tmpdir SQLite).
- relay 测试沿用 tests/pi/swt-mailbox-relay.test.mjs 约定: mock pi API + 注入 spawn/fetch/时钟; 运行 `node --test tests/pi/swt-mailbox-relay.test.mjs`.
- Python 测试命令 `uv run --with pytest python -m pytest tests/...`; 本环境 (sandbox) 无 podman, 需真 podman 的路径不宣称通过, 留 M09.
- 镜像重建 (D017 级联: base→display→全部项目层) 超出本环境能力: 只改仓库内生成器与清单 + 分发说明, 实际重建留 host/M09 (M05 UD-08 同款).
- 提交粒度: 每 ISSUE 一次 `feat: ISSUE-<NN>: <描述>` (文档类 ISSUE 用 `doc:`), 只 stage 本 ISSUE 文件; MILESTONE-08.md 状态行与 ROADMAP.md 为总指挥管, 执行者永不 stage.

## ISSUE 列表

- [x] ISSUE-01: base 层 sshd 三项 + entrypoint 目录保障
  - 范围: image-prep.py BASE_CONTAINERFILE: (1) 既有 SetEnv 单行合并追加 `XDG_RUNTIME_DIR=/tmp/xdg-1001` (N5 固定常量, UD-03; 不用 ~/.ssh/environment 路径, UD-04); (2) 追加 `StreamLocalBindUnlink yes` 行; (3) CMD 换 entrypoint 脚本 (install -d bolo 0700 建 /tmp/xdg-1001 与 /tmp/swt 后 exec sshd). 不加残尸清理 (UD-12). 更新 test_swt_m07.py 既有 SetEnv 断言 + 新增三项断言.
  - 依据: D004/N3/N5. 接缝: 生成器输出文本断言 (既有模式 test_swt_m07.py:233).
- [x] ISSUE-02: display 层需求清单加 waypipe/libpulse0
  - 范围: image/requirements-browser.md 追加 waypipe (probe `waypipe --version`) 与 libpulse0 (dpkg-query probe) 两 apt 条目, 位置在 chromium 条目之前; 解析断言 (条目存在, install 含 apt-get, probe 非空).
  - 依据: M08 任务书 (display 层加 waypipe/libpulse0), N6. 接缝: parse_requirements 对真实清单文件的断言.
- [x] ISSUE-03: 启动脚本母本制 + preflight + birth 接线
  - 范围: 新母本 workflow/use-sandbox-worktree/headed-browser/swt-headed-browser.sh: preflight (WAYLAND_DISPLAY/XDG_RUNTIME_DIR 在场且 $XDG_RUNTIME_DIR/$WAYLAND_DISPLAY 经 python3 AF_UNIX 可连, 不满足 exit 86, UD-11) + 条件导出 PULSE_SERVER (socket 在场才导, UD-08) + `exec '__CHROMIUM__' --no-sandbox --ozone-platform=wayland "$@"` (N1: env 脚本内设). swt.py: birth 流程解析 chromium 精确路径 (throwaway `podman run --rm <image-ref> sh -c 'ls -d .../chromium-*/chrome-linux*/chrome | sort -V | tail -1'`, UD-06) → 实例落 `<records_root>/runtime/<identity>/swt-headed-browser.sh` (0755, __CHROMIUM__ 替换) → create 增 `-v <实例>:<容器固定路径>:ro` (固定路径 /home/bolo/.local/bin/swt-headed-browser.sh, D003); 解析失败 → stderr 告警 + 跳过挂载 (UD-06). create_and_start_container 增脚本有无的返回/传递供 ISSUE-07 消费.
  - 依据: D003/D007(1)/F006/N1/N5. 接缝: fake-run 断言 create 参数含 ro 挂载; 实例脚本行为测试 (无 env → exit 86; 构造真 unix socket + __CHROMIUM__=/bin/echo → 通过且回显参数).
- [x] ISSUE-04: 服务端指令集首成员 swt.pull-window
  - 范围: swt-base-server.py 常量 `PULL_WINDOW_TOOL = "swt.pull-window"`; exec 投信命中判定: dict 恰含 {tool, container} 两键且 container == 投信容器 key 的自身容器名 → 直批 (不降级), 否则维持既有 canonical/降级路径 (UD-05: 不落静态 whitelist 行; 裸 tool 无 container/多余键/他人容器名 → 降级). admin whitelist 机制不动.
  - 依据: D008(1)/F004(M01). 接缝: Mailbox.post 单测 (命中不降级, 错名/缺名/多键/未注册名降级, 非 pull-window exec 既有行为不变).
- [x] ISSUE-05: 设备侧执行器机械判定 (relay 扩展拉窗门)
  - 范围: swt-mailbox-relay.ts: exec 来信 body 解析出 tool=swt.pull-window 时进门逻辑: (1) waypipe 在场检查 (spawn `sh -c command -v waypipe`), 缺席 → 本地 notify 安装提示 (缺席期去重, 恢复后重查) + 立即 ack outcome=skipped:waypipe-missing + 不 triggerTurn (D006(3) "不取下一封同类信", UD-10); (2) 限频: 同容器 min 间隔 300s (UD-07), 窗内 → ack outcome=skipped:rate-limited + info notify + 不 triggerTurn; (3) 过门 → 记限频时刻, triggerTurn, hint 指向 SKILL.md 窗口直飞配方节 (UD-07 分层). awaitingAck 项带 outcome, 既有 handled 路径不变.
  - 依据: D006(3)/D008(2)(3)/D007 判定拆分原则. 接缝: node --test 注入 spawn/fetch/now (既有约定).
- [x] ISSUE-06: swt enroll-device-key 子命令 (设备密钥 enrollment)
  - 范围: swt.py 新子命令 `enroll-device-key <容器名> [--pubkey-file <路径>|-, 缺省 stdin]`: 校验公钥 (单行, 非注释, ≥2 字段) → podman exec -i 容器 sh 合并进 /home/bolo/.ssh/authorized_keys (mkdir/touch/chmod 600 + `grep -qxF` 去重, 单次 exec, stdin 传公钥) → 打印确认与设备侧测试提示. 容器不在/公钥非法 → 明确报错 (DECIDE 协议之外的操作类错误, 沿用既有错误通道).
  - 依据: N4/D006. 接缝: fake-run 断言命令形状 + stdin 内容 + 非法公钥拒绝.
- [x] ISSUE-07: 交付包 "远程直飞" 项
  - 范围: print_delivery_lines 增 `headed_script` 形参 (ISSUE-03 产物有无): 有 → 两行: 模板行 `waypipe ssh -p <port> -R /tmp/swt/pulse-b.sock:/run/user/$(id -u)/pulse/native bolo@<lan> /home/bolo/.local/bin/swt-headed-browser.sh` (UD-09; lan 缺 → 未附发 reason 行, F3 模式) + 前置行 (设备 Linux Wayland + waypipe 客户端检查 + enroll-device-key 提示); 无 → 一行 reason. birth/resume/status 调用点接线; 既有交付断言按新行更新.
  - 依据: D001(a)/D006(2)/N1/N4. 接缝: 交付输出文本断言.
- [x] ISSUE-08: SKILL.md 显示栈节改写 + 指令集现状更新 (文档)
  - 范围: use-sandbox-worktree/SKILL.md: (1) 交付包定义 (L15 段) 增远程直飞项; (2) 存续节显示栈段后增 "窗口直飞 (三态选路)" 小节: 容器侧编排 (脚本 preflight/exit 86 → 投信 letter 形状示例 + to 当前设备沿 M05 流程 → ack 后轮询新 waypipe-server-*.sock token 差集, 超时 120s (UD-02) → 落 noVNC 并告知用户) + 设备侧配方 (waypipe 前提与 distrobox/enroll-device-key/幂等 pgrep 探测/nohup 后台拉起/herdr notification 回报/N1 禁赋值前缀); (3) 基础服务节指令集现状 (L220-222 段) 改为首成员已落地 (形状校验 + 自身容器绑定, UD-05); (4) 分发与生效节增 base/display D017 级联重建提醒 (M05 UD-08 同款).
  - 依据: D001/D006(1)/D007/D008/N1-N4. 无代码接缝; 真链验证归 M09.

依赖: ISSUE-07 阻塞于 ISSUE-03; ISSUE-08 阻塞于 ISSUE-01..07; 其余无阻塞, 可并行.

## 完成定义

- `uv run --with pytest python -m pytest` 全绿 (存量 + 新增); `node --test tests/pi/swt-mailbox-relay.test.mjs` 全绿.
- 每 ISSUE 一次提交; 测试接缝均落公开行为 (生成器文本/CLI 行为/交付输出/HTTP 单元/扩展事件), 不测内部实现.
- 需要 podman/真机的路径 (镜像重建, 真窗口拉起, 跨机端到端) 不宣称通过, 显式留 M09. 本沙箱无 podman: 全量 pytest 中 m12/m04/m09/m07-e2e 等需真 podman 的用例基线即红 (111 errors/96 failed 均此类), 契约池基线 244 绿 (web_access/base_server*/birth_mailbox/m07 除 e2e); 比对以契约池为准, 不追全量绿.

## 全局风险和停止条件

- Spec (D001-D008/N1-N6) 与代码事实冲突, 或需新增决策 → 停, 落 UD 或升级用户.
- 触碰禁止范围 (STATE 加字段, 容器白名单放行出向, 改造现有容器) → 停.
